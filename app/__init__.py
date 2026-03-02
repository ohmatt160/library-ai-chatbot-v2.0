"""
Application factory for the Intelligent Library Chat Assistant
"""

import os
from datetime import timedelta
from flask import Flask, jsonify, send_from_directory, Blueprint
from flask_cors import CORS
from flask_restful import Api
from .extensions import db, bcrypt, ma, login_manager, jwt
from flask import Flask, send_from_directory
import os


def _run_migrations(app):
    """Run database migrations for existing tables"""
    try:
        from sqlalchemy import text, inspect
        
        inspector = inspect(db.engine)
        
        # Check if reserve_requests table exists
        if 'reserve_requests' in inspector.get_table_names():
            columns = [c['name'] for c in inspector.get_columns('reserve_requests')]
            
            # Add notes column if it doesn't exist
            if 'notes' not in columns:
                try:
                    db.session.execute(text('ALTER TABLE reserve_requests ADD COLUMN notes TEXT'))
                    db.session.commit()
                    app.logger.info('Added notes column to reserve_requests table')
                except Exception as e:
                    app.logger.warning(f'Could not add notes column: {e}')
                    db.session.rollback()
            
            # Try to handle book_id nullable - for SQLite this is tricky
            # For other databases, we try to make it nullable
            if 'book_id' in columns:
                try:
                    # Try to check if foreign key constraint exists and modify
                    db.session.execute(text('PRAGMA foreign_keys=OFF'))
                    # For SQLite, we'll just note that nullable might not work
                    # The model change should handle new inserts
                except Exception as e:
                    app.logger.warning(f'Could not modify constraints: {e}')
                            
        app.logger.info('Database migrations completed')
    except Exception as e:
        app.logger.warning(f'Database migration check failed: {e}')
        # Continue anyway - the app should still work


def create_app(config_class='config.DevelopmentConfig'):
    """Create and configure the Flask application"""
    app = Flask(__name__,
                static_folder='static',  # Point to your React build
                template_folder='templates')

    # ... your existing config ...

    # 👇 THIS ROUTE GOES HERE (on app, not blueprint)




    # Load configuration
    app.config.from_object(config_class)

    # Override from environment variable if set
    if os.getenv('FLASK_CONFIG'):
        app.config.from_object(os.getenv('FLASK_CONFIG'))

    # JWT Configuration
    app.config.setdefault('JWT_SECRET_KEY', app.config.get('SECRET_KEY', 'jwt-secret-change-in-production'))
    app.config.setdefault('JWT_ACCESS_TOKEN_EXPIRES', timedelta(hours=24))
    app.config.setdefault('JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=30))
    app.config.setdefault('JWT_TOKEN_LOCATION', ['headers'])
    app.config.setdefault('JWT_HEADER_NAME', 'Authorization')
    app.config.setdefault('JWT_HEADER_TYPE', 'Bearer')

    # OPAC Configuration (OpenLibrary integration)
    # Set OPAC_TYPE to 'openlibrary' to use OpenLibrary API
    # Options: 'generic', 'koha', 'evergreen', 'sierra', 'aleph', 'openlibrary'
    app.config.setdefault('OPAC_TYPE', 'openlibrary')  # Use OpenLibrary by default
    app.config.setdefault('OPAC_URL', '')
    app.config.setdefault('OPAC_API_KEY', '')
    app.config.setdefault('OPAC_USERNAME', '')
    app.config.setdefault('OPAC_PASSWORD', '')
    app.config.setdefault('OPAC_TIMEOUT', 30)
    app.config.setdefault('OPAC_USE_MOCK', False)

    # Initialize extensions with app
    db.init_app(app)
    bcrypt.init_app(app)
    ma.init_app(app)
    login_manager.init_app(app)
    jwt.init_app(app)

    from .model import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    # JWT user lookup callback
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data['sub']
        return User.query.get(identity)

    # JWT error handlers
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has expired', 'code': 'token_expired'}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({'error': 'Invalid token', 'code': 'invalid_token'}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({'error': 'Authorization token is required', 'code': 'authorization_required'}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({'error': 'Token has been revoked', 'code': 'token_revoked'}), 401

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_react(path):
        """Serve React static files"""
        if path and os.path.exists(os.path.join(app.static_folder, path)):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')

    # Register blueprints
    from app.api.routes import api_bp
    app.register_blueprint(api_bp, url_prefix='/api')

    # Initialize API
    api = Api(app)
    from .api.resources import (
        GetSession, RegisterResource, LoginResource, LogoutResource,
        ProfileResource, ChatResource, FeedbackResource, ActivityResource,
        BookSearchResource, AdminUsersResource, AdminActivitiesResource,
        AdminMetricsResource, AdminBooksResource, AdminBookResource,
        AdminBooksBulkResource, AdminContactsResource, AdminContactResource,
        QuestionnaireResource, QuestionnaireStatsResource, EvaluationReportResource
    )
    api.add_resource(GetSession, '/api/session')
    api.add_resource(RegisterResource, '/api/register')
    api.add_resource(LoginResource, '/api/login')
    api.add_resource(LogoutResource, '/api/logout')
    api.add_resource(ProfileResource, '/api/profile')
    api.add_resource(ChatResource, '/api/chat')
    api.add_resource(FeedbackResource, '/api/feedback')
    api.add_resource(QuestionnaireResource, '/api/questionnaire')
    api.add_resource(QuestionnaireStatsResource, '/api/questionnaire/stats')
    api.add_resource(EvaluationReportResource, '/api/evaluation/report')
    api.add_resource(ActivityResource, '/api/activity')
    api.add_resource(BookSearchResource, '/api/search/books')
    api.add_resource(AdminUsersResource, '/api/admin/users')
    api.add_resource(AdminActivitiesResource, '/api/admin/activities')
    api.add_resource(AdminMetricsResource, '/api/admin/metrics')
    api.add_resource(AdminBooksResource, '/api/admin/books')
    api.add_resource(AdminBookResource, '/api/admin/books/<int:book_id>')
    api.add_resource(AdminBooksBulkResource, '/api/admin/books/bulk')
    api.add_resource(AdminContactsResource, '/api/admin/contacts')
    api.add_resource(AdminContactResource, '/api/admin/contacts/<int:contact_id>')

    # Initialize CORS
    CORS(app, supports_credentials=True,
         origins=["http://localhost", "http://127.0.0.1:5500", "http://localhost:5173", "http://localhost:5174", "http://127.0.0.1:5173"],
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    # Register borrow blueprint
    from .api.borrow_routes import borrow_bp
    app.register_blueprint(borrow_bp, url_prefix='/api')

    # Setup logger
    from .utils.logger import setup_logger
    setup_logger(app)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        import logging
        logging.error(f"Internal error: {error}")
        return jsonify({'error': 'Internal server error'}), 500

    # Log all requests for debugging
    @app.before_request
    def log_request():
        from flask import request
        import logging
        logging.info(f"Request: {request.method} {request.path}")

    @app.after_request
    def log_response(response):
        import logging
        logging.info(f"Response: {response.status_code}")
        return response

    return app
