"""
Application factory for the Intelligent Library Chat Assistant
"""

import os
from datetime import timedelta
from flask import Flask, jsonify
from flask_cors import CORS
from flask_restful import Api
from .extensions import db, bcrypt, ma, login_manager, jwt


def create_app(config_class='config.DevelopmentConfig'):
    """Create and configure the Flask application"""
    app = Flask(__name__)

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

    # Setup logger
    from .utils.logger import setup_logger
    setup_logger(app)

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500

    return app
