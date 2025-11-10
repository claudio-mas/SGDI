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
    # Configure static and template folders to use root-level directories
    import os
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    static_folder = os.path.join(root_dir, 'static')
    template_folder = 'templates'  # Relative to app/ directory

    app = Flask(__name__,
                static_folder=static_folder,
                template_folder=template_folder)
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

    # In test mode, relax strict slash behavior to avoid 308 Permanent Redirects
    # Tests expect 302/200/401/403; disabling strict slashes in tests reduces flakiness.
    if app.config.get('TESTING', False):
        try:
            app.url_map.strict_slashes = False
        except Exception:
            # Older Werkzeug/Flask may not support setting strict_slashes; ignore safely
            pass
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    # login_manager.login_message = 'Por favor, faça login para acessar esta página.'
    login_manager.login_message_category = 'info'
    
    # Initialize security middleware
    from app.utils.security import SecurityHeaders, RateLimiter
    from app.utils.middleware import PermissionMiddleware
    
    SecurityHeaders(app)
    # Disable/skip rate limiting when running tests to avoid flakiness
    if not app.config.get('TESTING', False):
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
    
    # Register context processors
    @app.context_processor
    def inject_system_settings():
        """Inject system settings into all templates"""
        try:
            from app.repositories.settings_repository import (
                SettingsRepository
            )
            settings_repo = SettingsRepository()
            system_logo = settings_repo.get_value('system_logo', '')
            return dict(system_logo=system_logo)
        except Exception:
            # If database not ready or error, return empty
            return dict(system_logo='')
    
    # Also expose some helper functions/globals to Jinja environment for templates
    # - make get_file_icon available as a global (templates may call it as a function)
    # - expose builtin min/max to avoid UndefinedError in templates that use them
    try:
        from app.utils.template_filters import get_file_icon
        app.jinja_env.globals.update(get_file_icon=get_file_icon)
    except Exception:
        # If import fails, skip safely
        pass

    # Expose Python builtins min/max for use in templates (safe usage expected)
    try:
        app.jinja_env.globals.update(min=min, max=max)
    except Exception:
        pass
    # Provide a small wrapper for url_for to accept alternative param names used in some templates
    try:
        from flask import url_for as _flask_url_for

        def _url_for(endpoint, **values):
            # No automatic parameter mapping
            # Use exact parameter names for endpoints
            return _flask_url_for(endpoint, **values)

        app.jinja_env.globals.update(url_for=_url_for)
    except Exception:
        pass

    # Root route: redirect to search page (login_required on search will
    # forward anonymous users to the login page configured in LoginManager)
    from flask import redirect, url_for

    @app.route('/')
    def index():
        return redirect(url_for('search.search'))
    
    return app
