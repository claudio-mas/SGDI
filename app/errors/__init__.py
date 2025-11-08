"""
Error handlers and custom exceptions
"""
from flask import render_template, jsonify


class GEDException(Exception):
    """Base exception for GED System"""
    pass


class AuthenticationError(GEDException):
    """Authentication related errors"""
    pass


class AuthorizationError(GEDException):
    """Authorization related errors"""
    pass


class ValidationError(GEDException):
    """Validation related errors"""
    pass


class NotFoundError(GEDException):
    """Resource not found errors"""
    pass


class StorageError(GEDException):
    """Storage related errors"""
    pass


def register_error_handlers(app):
    """Register error handlers with the Flask app"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(500)
    def internal_error(error):
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(GEDException)
    def handle_ged_exception(error):
        return jsonify({'error': str(error)}), 400
