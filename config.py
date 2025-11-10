import os
from datetime import timedelta
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))


class Config:
    """Base configuration class"""
    
    # Flask Core
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    ENV = os.environ.get('FLASK_ENV', 'development')
    
    # Database Configuration
    DATABASE_SERVER = os.environ.get('DATABASE_SERVER', 'localhost')
    DATABASE_NAME = os.environ.get('DATABASE_NAME', 'sistema_ged')
    DATABASE_USER = os.environ.get('DATABASE_USER', 'sa')
    DATABASE_PASSWORD = os.environ.get('DATABASE_PASSWORD', '')
    DATABASE_DRIVER = os.environ.get('DATABASE_DRIVER', 'ODBC Driver 17 for SQL Server')
    
    SQLALCHEMY_DATABASE_URI = (
        f"mssql+pyodbc://{DATABASE_USER}:{DATABASE_PASSWORD}@{DATABASE_SERVER}/"
        f"{DATABASE_NAME}?driver={DATABASE_DRIVER.replace(' ', '+')}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_RECYCLE = 3600
    
    # File Upload Configuration
    UPLOAD_FOLDER = os.path.join(basedir, os.environ.get('UPLOAD_FOLDER', 'uploads'))
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 52428800))  # 50MB
    ALLOWED_EXTENSIONS = set(os.environ.get('ALLOWED_EXTENSIONS', 'pdf,doc,docx,xls,xlsx,jpg,png,tif').split(','))
    
    # Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@example.com')
    
    # Session Configuration
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(seconds=int(os.environ.get('PERMANENT_SESSION_LIFETIME', 3600)))
    
    # Security Settings
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
    ACCOUNT_LOCKOUT_DURATION = int(os.environ.get('ACCOUNT_LOCKOUT_DURATION', 900))  # 15 minutes
    PASSWORD_RESET_TOKEN_EXPIRATION = int(os.environ.get('PASSWORD_RESET_TOKEN_EXPIRATION', 3600))  # 1 hour
    
    # Application Settings
    MAX_VERSIONS_PER_DOCUMENT = int(os.environ.get('MAX_VERSIONS_PER_DOCUMENT', 10))
    TRASH_RETENTION_DAYS = int(os.environ.get('TRASH_RETENTION_DAYS', 30))
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', 100))
    
    # Caching
    CACHE_TYPE = 'SimpleCache'
    CACHE_DEFAULT_TIMEOUT = 300


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    ENV = 'development'
    SQLALCHEMY_ECHO = True


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    ENV = 'testing'
    # Use a file-backed SQLite DB during tests to support concurrency across threads
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'test_sqlite.db')
    # Allow SQLite connections to be used from multiple threads during concurrent tests
    SQLALCHEMY_ENGINE_OPTIONS = {
        'connect_args': {'check_same_thread': False}
    }
    # Keep ORM objects usable after commit during tests (prevents expired attributes)
    SQLALCHEMY_EXPIRE_ON_COMMIT = False
    WTF_CSRF_ENABLED = False
    # Increase upload limit during tests to avoid RequestEntityTooLarge for test payloads
    MAX_CONTENT_LENGTH = int(os.environ.get('TESTING_MAX_CONTENT_LENGTH', 209715200))  # 200MB


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    ENV = 'production'
    SESSION_COOKIE_SECURE = True
    SQLALCHEMY_ECHO = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
