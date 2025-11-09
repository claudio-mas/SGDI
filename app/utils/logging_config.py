"""
Logging configuration for Sistema GED
Implements rotating file handlers with different log levels for environments
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime


def setup_logging(app):
    """
    Configure application logging with rotating file handlers
    
    Args:
        app: Flask application instance
    """
    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'logs')
    os.makedirs(log_dir, exist_ok=True)
    
    # Determine log level based on environment
    if app.config.get('DEBUG'):
        log_level = logging.DEBUG
    elif app.config.get('TESTING'):
        log_level = logging.WARNING
    else:
        log_level = logging.INFO
    
    # Set application logger level
    app.logger.setLevel(log_level)
    
    # Remove existing handlers to avoid duplicates
    app.logger.handlers.clear()
    
    # Configure structured logging format
    log_format = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s (%(funcName)s:%(lineno)d): %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Application log file handler (rotating, 10MB max, 10 backups)
    app_log_file = os.path.join(log_dir, 'ged_system.log')
    app_handler = RotatingFileHandler(
        app_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    app_handler.setLevel(log_level)
    app_handler.setFormatter(log_format)
    app.logger.addHandler(app_handler)
    
    # Error log file handler (only errors and critical)
    error_log_file = os.path.join(log_dir, 'ged_errors.log')
    error_handler = RotatingFileHandler(
        error_log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10,
        encoding='utf-8'
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(log_format)
    app.logger.addHandler(error_handler)
    
    # Console handler for development
    if app.config.get('DEBUG'):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(log_format)
        app.logger.addHandler(console_handler)
    
    # Log startup message
    app.logger.info('=' * 80)
    app.logger.info(f'Sistema GED Application Started - Environment: {app.config.get("ENV", "unknown")}')
    app.logger.info(f'Debug Mode: {app.config.get("DEBUG", False)}')
    app.logger.info(f'Log Level: {logging.getLevelName(log_level)}')
    app.logger.info('=' * 80)
    
    # Configure SQLAlchemy logging
    if app.config.get('SQLALCHEMY_ECHO'):
        logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
    else:
        logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    return app.logger


def log_request(app):
    """
    Log HTTP requests with details
    
    Args:
        app: Flask application instance
    """
    @app.before_request
    def before_request_logging():
        from flask import request
        from flask_login import current_user
        
        # Skip logging for static files
        if request.endpoint and 'static' in request.endpoint:
            return
        
        user_id = current_user.id if current_user.is_authenticated else 'anonymous'
        app.logger.info(
            f'Request: {request.method} {request.path} | '
            f'User: {user_id} | '
            f'IP: {request.remote_addr}'
        )
    
    @app.after_request
    def after_request_logging(response):
        from flask import request
        
        # Skip logging for static files
        if request.endpoint and 'static' in request.endpoint:
            return response
        
        app.logger.info(
            f'Response: {request.method} {request.path} | '
            f'Status: {response.status_code}'
        )
        
        return response


def log_exception(app):
    """
    Log unhandled exceptions with full traceback
    
    Args:
        app: Flask application instance
    """
    @app.errorhandler(Exception)
    def log_exception_handler(error):
        from flask import request
        from flask_login import current_user
        import traceback
        
        user_id = current_user.id if current_user.is_authenticated else 'anonymous'
        
        app.logger.error(
            f'Unhandled Exception: {str(error)}\n'
            f'Request: {request.method} {request.path}\n'
            f'User: {user_id}\n'
            f'IP: {request.remote_addr}\n'
            f'Traceback:\n{traceback.format_exc()}'
        )
        
        # Re-raise the exception to be handled by error handlers
        raise


class RequestLogger:
    """Context manager for logging operations with timing"""
    
    def __init__(self, logger, operation_name, user_id=None, **context):
        self.logger = logger
        self.operation_name = operation_name
        self.user_id = user_id
        self.context = context
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        context_str = ', '.join(f'{k}={v}' for k, v in self.context.items())
        self.logger.info(
            f'Starting operation: {self.operation_name} | '
            f'User: {self.user_id} | '
            f'{context_str}'
        )
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            self.logger.info(
                f'Completed operation: {self.operation_name} | '
                f'Duration: {duration:.3f}s'
            )
        else:
            self.logger.error(
                f'Failed operation: {self.operation_name} | '
                f'Duration: {duration:.3f}s | '
                f'Error: {exc_val}'
            )
        
        # Don't suppress exceptions
        return False
