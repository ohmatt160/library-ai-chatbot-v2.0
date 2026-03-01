# """
# Configuration settings for the Intelligent Library Chat Assistant
# """
#
# import os
# from datetime import timedelta
# from dotenv import load_dotenv
#
# load_dotenv()
#
# class Config:
#     """Base configuration"""
#
#     # Flask settings
#     HF_token = os.getenv('HF_TOKEN', '')
#     SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
#
#     # Database settings (XAMPP MySQL defaults)
#     DB_HOST = os.getenv('DB_HOST', 'localhost')
#     DB_PORT = os.getenv('DB_PORT', '3306')
#     DB_NAME = os.getenv('DB_NAME', 'library_chatbot_db')
#     DB_USER = os.getenv('DB_USER', 'root')
#     DB_PASSWORD = os.getenv('DB_PASSWORD', '')
#
#     # SQLAlchemy settings
#     # Use MySQL if DATABASE_URL not set, build from DB settings
#     if os.getenv('DATABASE_URL'):
#         SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
#     else:
#         SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
#     SQLALCHEMY_TRACK_MODIFICATIONS = False
#     SQLALCHEMY_ENGINE_OPTIONS = {
#         'pool_size': 10,
#         'pool_recycle': 3600,
#         'pool_pre_ping': True,
#     }
#
#     # Redis settings (for session management)
#     REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
#     REDIS_PORT = os.getenv('REDIS_PORT', 6379)
#     REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
#
#     # JWT settings for API authentication
#     JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'jwt-secret-key-change-me')
#     JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
#     JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)
#
#     # File upload settings
#     MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max file size
#     UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
#
#     # Chatbot settings
#     CHATBOT_NAME = "Library Assistant"
#     CHATBOT_VERSION = "1.0.0"
#
#     # NLP model settings
#     SPACY_MODEL = "en_core_web_lg"
#     SENTENCE_TRANSFORMER_MODEL = "all-MiniLM-L6-v2"
#
#     # Rate limiting
#     RATELIMIT_DEFAULT = "200 per day;50 per hour"
#     RATELIMIT_STORAGE_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
#
#     # CORS settings
#     CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')
#
#     # Logging
#     LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
#     LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'app.log')
#
#     # Performance settings
#     MAX_RESPONSE_TIME = 4.0  # seconds
#     CACHE_TIMEOUT = 300  # seconds
#
#     # Evaluation metrics
#     EVALUATION_ENABLED = True
#     FEEDBACK_COLLECTION = True
#
#     # Other settings
#     SESSION_TYPE = 'filesystem'
#     PERMANENT_SESSION_LIFETIME = timedelta(hours=24)
#
#     # OPAC (Online Public Access Catalog) settings
#     # Set OPAC_URL to enable external library catalog integration
#     # Supported types: 'koha', 'evergreen', 'sierra', 'aleph', 'generic'
#     OPAC_TYPE = os.getenv('OPAC_TYPE', 'generic')
#     OPAC_URL = os.getenv('OPAC_URL', '')  # e.g., 'https://library.example.com'
#     OPAC_API_KEY = os.getenv('OPAC_API_KEY', '')
#     OPAC_USERNAME = os.getenv('OPAC_USERNAME', '')
#     OPAC_PASSWORD = os.getenv('OPAC_PASSWORD', '')
#     OPAC_TIMEOUT = int(os.getenv('OPAC_TIMEOUT', '30'))
#     OPAC_USE_MOCK = os.getenv('OPAC_USE_MOCK', 'false').lower() == 'true'  # Use mock client only when explicitly enabled
#
#
# class DevelopmentConfig(Config):
#     """Development configuration"""
#     DEBUG = True
#     TESTING = False
#     ENV = 'development'
#
#     # Development-specific settings
#     SQLALCHEMY_ECHO = True  # Log SQL queries
#     CHATBOT_MODE = "development"
#
#
# class TestingConfig(Config):
#     """Testing configuration"""
#     DEBUG = False
#     TESTING = True
#     ENV = 'testing'
#
#     # Use SQLite for testing
#     SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
#
#     # Disable rate limiting for tests
#     RATELIMIT_ENABLED = False
#
#
# class ProductionConfig(Config):
#     """Production configuration"""
#     DEBUG = False
#     TESTING = False
#     ENV = 'production'
#
#     # Production-specific settings
#     CHATBOT_MODE = "production"
#
#     # Security settings
#     SESSION_COOKIE_SECURE = True
#     REMEMBER_COOKIE_SECURE = True
#     SESSION_COOKIE_HTTPONLY = True
#     REMEMBER_COOKIE_HTTPONLY = True
#
#     # Ensure secret keys are set
#     SECRET_KEY = os.getenv('SECRET_KEY', 'prod-secret-key-change-me')
#     JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'prod-jwt-secret-key-change-me')


"""
Configuration settings for the Intelligent Library Chat Assistant
All sensitive values come from environment variables (.env file)
"""

import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration - ALL secrets from environment variables"""

    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY')
    if not SECRET_KEY:
        raise ValueError("SECRET_KEY must be set in .env file")

    # JWT settings for API authentication
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY')
    if not JWT_SECRET_KEY:
        raise ValueError("JWT_SECRET_KEY must be set in .env file")

    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # Security salt (optional but recommended)
    SECURITY_PASSWORD_SALT = os.getenv('SECURITY_PASSWORD_SALT', '')

    # Hugging Face (optional)
    HF_TOKEN = os.getenv('HF_TOKEN', '')

    # Database settings - ALL from environment
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '3306')
    DB_NAME = os.getenv('DB_NAME', 'library_chatbot_db')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')

    # SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL')
    if not SQLALCHEMY_DATABASE_URI:
        # Build from individual DB settings if DATABASE_URL not provided
        SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': int(os.getenv('DB_POOL_SIZE', '10')),
        'pool_recycle': int(os.getenv('DB_POOL_RECYCLE', '3600')),
        'pool_pre_ping': True,
    }

    # Redis settings (for session management)
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', '6379'))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)

    # Rate limiting
    RATELIMIT_DEFAULT = os.getenv('RATELIMIT_DEFAULT', "200 per day;50 per hour")
    RATELIMIT_STORAGE_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0" if REDIS_HOST != 'localhost' else "memory://"

    # CORS settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*').split(',')

    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', os.path.join(os.path.dirname(__file__), 'logs', 'app.log'))

    # File upload settings
    MAX_CONTENT_LENGTH = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', os.path.join(os.path.dirname(__file__), 'uploads'))

    # Chatbot settings
    CHATBOT_NAME = os.getenv('CHATBOT_NAME', "Library Assistant")
    CHATBOT_VERSION = os.getenv('CHATBOT_VERSION', "1.0.0")

    # NLP model settings
    SPACY_MODEL = os.getenv('SPACY_MODEL', "en_core_web_lg")
    SENTENCE_TRANSFORMER_MODEL = os.getenv('SENTENCE_TRANSFORMER_MODEL', "all-MiniLM-L6-v2")

    # Performance settings
    MAX_RESPONSE_TIME = float(os.getenv('MAX_RESPONSE_TIME', '4.0'))
    CACHE_TIMEOUT = int(os.getenv('CACHE_TIMEOUT', '300'))

    # Evaluation metrics
    EVALUATION_ENABLED = os.getenv('EVALUATION_ENABLED', 'true').lower() == 'true'
    FEEDBACK_COLLECTION = os.getenv('FEEDBACK_COLLECTION', 'true').lower() == 'true'

    # Session settings
    SESSION_TYPE = os.getenv('SESSION_TYPE', 'filesystem')
    PERMANENT_SESSION_LIFETIME = timedelta(hours=int(os.getenv('SESSION_LIFETIME_HOURS', '24')))

    # OPAC settings (external catalog integration)
    OPAC_TYPE = os.getenv('OPAC_TYPE', 'generic')
    OPAC_URL = os.getenv('OPAC_URL', '')
    OPAC_API_KEY = os.getenv('OPAC_API_KEY', '')
    OPAC_USERNAME = os.getenv('OPAC_USERNAME', '')
    OPAC_PASSWORD = os.getenv('OPAC_PASSWORD', '')
    OPAC_TIMEOUT = int(os.getenv('OPAC_TIMEOUT', '30'))
    OPAC_USE_MOCK = os.getenv('OPAC_USE_MOCK', 'false').lower() == 'true'


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    ENV = 'development'

    # Development-specific settings
    SQLALCHEMY_ECHO = True
    CHATBOT_MODE = "development"

    # Override with development defaults if needed
    CORS_ORIGINS = os.getenv('DEV_CORS_ORIGINS', 'http://localhost:5000,http://127.0.0.1:5000').split(',')


class TestingConfig(Config):
    """Testing configuration"""
    DEBUG = False
    TESTING = True
    ENV = 'testing'

    # Use SQLite for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    RATELIMIT_ENABLED = False


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    ENV = 'production'

    # Production-specific settings
    CHATBOT_MODE = "production"

    # Security settings - STRICT in production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True

    # Ensure secret keys are set (no fallbacks in production)
    @classmethod
    def validate(cls):
        """Validate that required secrets are set"""
        required_vars = ['SECRET_KEY', 'JWT_SECRET_KEY']
        missing = [var for var in required_vars if not os.getenv(var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        return True


# Dictionary for easy config selection
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}