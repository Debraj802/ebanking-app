# config.py
import os
from datetime import timedelta

class Config:
    # Secret key for session management
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-change-in-production'
    
    # MySQL Database Configuration
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'root'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or '@#.debraj_Admin'
    MYSQL_DB = os.environ.get('MYSQL_DB') or 'ebanking_db'
    MYSQL_CURSORCLASS = 'DictCursor'
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=30)
    SESSION_REFRESH_EACH_REQUEST = True
    
    # Security Configurations
    SESSION_COOKIE_SECURE = True  # Use only with HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Application Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    
    # Banking Settings
    MIN_DEPOSIT_AMOUNT = 1
    MAX_WITHDRAWAL_PER_TRANSACTION = 50000
    MAX_TRANSFER_PER_TRANSACTION = 100000
    DAILY_TRANSACTION_LIMIT = 500000
    
class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False  # Set to False for development (no HTTPS)
    
class ProductionConfig(Config):
    DEBUG = False
    # Add production-specific settings
    pass

# Select configuration based on environment
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}