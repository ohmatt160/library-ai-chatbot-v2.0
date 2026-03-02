import logging
import os
import sys

# Setup basic logging first
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from flask import render_template
    from flask_cors import CORS

    from app import create_app
    from config import Config

    os.environ['HF_TOKEN'] = Config.HF_TOKEN

    # Reduce SQLAlchemy logging
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)

    # Create the Flask app
    logger.info("Creating Flask app...")
    app = create_app()
    logger.info(f"Flask app created: {app.name}")

    # Setup CORS
    CORS(app, supports_credentials=True,
         origins=["http://localhost", "http://127.0.0.1:5500"],
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

    @app.route('/')
    def index():
        try:
            return render_template('index.html')
        except Exception as e:
            logger.error(f"Error serving index: {e}")
            return {"status": "ok", "message": "Library Chatbot API is running"}, 200

    @app.route('/health')
    def health():
        return {"status": "healthy", "timestamp": "ok"}, 200

    logger.info("✅ Flask app ready")

except Exception as e:
    logger.error(f"❌ Failed to create app: {e}")
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    print(f"""
    📚 Library Chatbot API with Flask-RESTful
    =========================================
    Running on http://0.0.0.0:{port}
    """)
    app.run(host='0.0.0.0', port=port, debug=True)
