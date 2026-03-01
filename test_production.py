# test_production.py
from app import create_app
import os

# Force production settings
os.environ['FLASK_ENV'] = 'production'
os.environ['FLASK_DEBUG'] = '0'

app = create_app()

if __name__ == '__main__':
    print("🚀 Testing PRODUCTION mode on http://localhost:5000")
    print("🔧 Debug mode: OFF")
    print("📁 Static files: ", app.static_folder)
    app.run(debug=False, port=5000)