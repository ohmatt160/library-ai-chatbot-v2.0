import logging
import os

from flask import render_template
from flask_cors import CORS

from app import create_app
from app.extensions import db
from app.model import User
from config import Config
os.environ['HF_TOKEN'] = Config.HF_TOKEN
# Reduce SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)

# Reduce werkzeug (Flask) logs
logging.getLogger('werkzeug').setLevel(logging.WARNING)

app = create_app()
CORS(app, supports_credentials=True,
     origins=["http://localhost", "http://127.0.0.1:5500"],  # Add your frontend URL
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
@app.route('/')
def index():
    return render_template('index.html')

def create_tables():
    """Create database tables"""
    with app.app_context():
        db.create_all()

        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                email='admin@library.com',
                first_name='System',
                last_name='Administrator',
                user_type='Admin'
            )
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created: admin / admin123")

if __name__ == '__main__':
    create_tables()
    port = int(os.environ.get("PORT", 5000))

    print("""
    📚 Library Chatbot API with Flask-RESTful
    =========================================
    Running on http://0.0.0.0:5000
    """)

    app.run(host='0.0.0.0', port=port, debug=True)
