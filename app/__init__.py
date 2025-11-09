from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_caching import Cache
from flask_mail import Mail
from config import config

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
cache = Cache()
mail = Mail()


def create_app(config_name='default'):
    """Application factory pattern"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # Set up logging first
    from app.utils.logging_config import setup_logging, log_request, log_exception
    setup_logging(app)
    log_request(app)
    log_exception(app)
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    cache.init_app(app)
    mail.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Initialize security middleware
    from app.utils.security import SecurityHeaders, RateLimiter
    from app.utils.middleware import PermissionMiddleware
    
    SecurityHeaders(app)
    RateLimiter(app, requests_per_minute=app.config.get('RATE_LIMIT_PER_MINUTE', 100))
    PermissionMiddleware(app)
    
    # Register blueprints
    from app.auth import auth_bp
    from app.documents import document_bp
    from app.categories import category_bp
    from app.search import search_bp
    from app.workflows import workflow_bp
    from app.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(document_bp, url_prefix='/documents')
    app.register_blueprint(category_bp, url_prefix='/categories')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(workflow_bp, url_prefix='/workflows')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Register error handlers
    from app.errors import register_error_handlers
    register_error_handlers(app)
    
    # Create upload folder if it doesn't exist
    import os
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register template filters
    from app.utils.template_filters import register_filters
    register_filters(app)
    
    return app
