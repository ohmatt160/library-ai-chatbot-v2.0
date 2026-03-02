import logging
import os
import sys

# Setup logging immediately
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

logger.info("=" * 60)
logger.info("Starting Library Chatbot Application")
logger.info("=" * 60)

try:
    logger.info("Step 1: Importing Flask modules...")
    from flask import render_template
    from flask_cors import CORS
    logger.info("Step 1: ✓ Flask modules imported")
    
    logger.info("Step 2: Importing create_app...")
    from app import create_app
    logger.info("Step 2: ✓ create_app imported")
    
    logger.info("Step 3: Importing Config...")
    from config import Config
    logger.info("Step 3: ✓ Config imported")
    
    logger.info("Step 4: Setting HF_TOKEN...")
    os.environ['HF_TOKEN'] = Config.HF_TOKEN
    logger.info("Step 4: ✓ HF_TOKEN set")
    
    logger.info("Step 5: Configuring logging levels...")
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logger.info("Step 5: ✓ Logging configured")
    
    logger.info("Step 6: Creating Flask app...")
    app = create_app()
    logger.info(f"Step 6: ✓ Flask app created: {app.name}")
    
    logger.info("Step 7: Setting up CORS...")
    CORS(app, supports_credentials=True,
         origins=["http://localhost", "http://127.0.0.1:5500"],
         allow_headers=["Content-Type", "Authorization"],
         methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
    logger.info("Step 7: ✓ CORS configured")
    
    logger.info("Step 8: Defining routes...")
    
    @app.route('/')
    def index():
        logger.info("Request received: GET /")
        try:
            return render_template('index.html')
        except Exception as e:
            logger.error(f"Template error: {e}")
            return {"status": "ok", "service": "Library Chatbot API"}, 200

    @app.route('/health')
    def health():
        logger.info("Request received: GET /health")
        return {"status": "healthy"}, 200

    @app.route('/debug')
    def debug():
        logger.info("Request received: GET /debug")
        return {
            "status": "ok",
            "app_name": app.name,
            "routes": [str(r) for r in app.url_map.iter_rules()][:10]
        }, 200

    logger.info("Step 8: ✓ Routes defined")
    logger.info("=" * 60)
    logger.info("Flask app ready for gunicorn")
    logger.info("=" * 60)

except Exception as e:
    logger.error("=" * 60)
    logger.error(f"CRITICAL ERROR: {e}")
    logger.error("=" * 60)
    import traceback
    logger.error(traceback.format_exc())
    sys.exit(1)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)
