import logging
import os

from flask import render_template
from flask_cors import CORS

from app import create_app
from config import Config

os.environ['HF_TOKEN'] = Config.HF_TOKEN

# Reduce SQLAlchemy logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)

# Reduce werkzeug (Flask) logs
logging.getLogger('werkzeug').setLevel(logging.WARNING)

# Create the Flask app - database tables are created in create_app()
app = create_app()

# Setup CORS
CORS(app, supports_credentials=True,
     origins=["http://localhost", "http://127.0.0.1:5500"],
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

@app.route('/')
def index():
    return render_template('index.html')

# Log successful startup
print(f"✅ Flask app ready: {app.name}")

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    print(f"""
    📚 Library Chatbot API with Flask-RESTful
    =========================================
    Running on http://0.0.0.0:{port}
    """)
    app.run(host='0.0.0.0', port=port, debug=True)
