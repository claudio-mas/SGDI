"""
Error handlers and custom exceptions
"""
from flask import render_template, jsonify, request
from flask_login import current_user
import traceback


class GEDException(Exception):
    """Base exception for GED System"""
    
    def __init__(self, message, status_code=400, payload=None):
        super().__init__()
        self.message = message
        self.status_code = status_code
        self.payload = payload
    
    def to_dict(self):
        rv = dict(self.payload or ())
        rv['error'] = self.message
        return rv


class AuthenticationError(GEDException):
    """Authentication related errors"""
    
    def __init__(self, message="Erro de autenticação", status_code=401, payload=None):
        super().__init__(message, status_code, payload)


class InvalidCredentialsError(AuthenticationError):
    """Invalid credentials error"""
    
    def __init__(self, message="Credenciais inválidas"):
        super().__init__(message, 401)


class AccountBlockedError(AuthenticationError):
    """Account blocked error"""
    
    def __init__(self, message="Conta bloqueada temporariamente"):
        super().__init__(message, 403)


class SessionExpiredError(AuthenticationError):
    """Session expired error"""
    
    def __init__(self, message="Sessão expirada"):
        super().__init__(message, 401)


class AuthorizationError(GEDException):
    """Authorization related errors"""
    
    def __init__(self, message="Erro de autorização", status_code=403, payload=None):
        super().__init__(message, status_code, payload)


class PermissionDeniedError(AuthorizationError):
    """Permission denied error"""
    
    def __init__(self, message="Permissão negada"):
        super().__init__(message, 403)


class InsufficientPrivilegesError(AuthorizationError):
    """Insufficient privileges error"""
    
    def __init__(self, message="Privilégios insuficientes"):
        super().__init__(message, 403)


class ValidationError(GEDException):
    """Validation related errors"""
    
    def __init__(self, message="Erro de validação", status_code=400, payload=None):
        super().__init__(message, status_code, payload)


class InvalidFileTypeError(ValidationError):
    """Invalid file type error"""
    
    def __init__(self, message="Tipo de arquivo inválido"):
        super().__init__(message, 400)


class FileSizeExceededError(ValidationError):
    """File size exceeded error"""
    
    def __init__(self, message="Tamanho do arquivo excedido"):
        super().__init__(message, 400)


class DuplicateDocumentError(ValidationError):
    """Duplicate document error"""
    
    def __init__(self, message="Documento duplicado"):
        super().__init__(message, 409)


class NotFoundError(GEDException):
    """Resource not found errors"""
    
    def __init__(self, message="Recurso não encontrado", status_code=404, payload=None):
        super().__init__(message, status_code, payload)


class DocumentNotFoundError(NotFoundError):
    """Document not found error"""
    
    def __init__(self, message="Documento não encontrado"):
        super().__init__(message, 404)


class UserNotFoundError(NotFoundError):
    """User not found error"""
    
    def __init__(self, message="Usuário não encontrado"):
        super().__init__(message, 404)


class StorageError(GEDException):
    """Storage related errors"""
    
    def __init__(self, message="Erro de armazenamento", status_code=500, payload=None):
        super().__init__(message, status_code, payload)


class FileUploadError(StorageError):
    """File upload error"""
    
    def __init__(self, message="Erro ao fazer upload do arquivo"):
        super().__init__(message, 500)


class FileDownloadError(StorageError):
    """File download error"""
    
    def __init__(self, message="Erro ao fazer download do arquivo"):
        super().__init__(message, 500)


def register_error_handlers(app):
    """Register error handlers with the Flask app"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors"""
        app.logger.warning(
            f'404 Error: {request.method} {request.path} | '
            f'User: {current_user.id if current_user.is_authenticated else "anonymous"} | '
            f'IP: {request.remote_addr}'
        )
        
        if request.is_json or request.accept_mimetypes.accept_json:
            return jsonify({'error': 'Recurso não encontrado'}), 404
        
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 Forbidden errors"""
        app.logger.warning(
            f'403 Error: {request.method} {request.path} | '
            f'User: {current_user.id if current_user.is_authenticated else "anonymous"} | '
            f'IP: {request.remote_addr} | '
            f'Error: {str(error)}'
        )
        
        if request.is_json or request.accept_mimetypes.accept_json:
            return jsonify({'error': 'Acesso negado'}), 403
        
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(429)
    def too_many_requests_error(error):
        """Handle 429 Too Many Requests errors"""
        app.logger.warning(
            f'429 Error: Rate limit exceeded | '
            f'User: {current_user.id if current_user.is_authenticated else "anonymous"} | '
            f'IP: {request.remote_addr}'
        )
        
        if request.is_json or request.accept_mimetypes.accept_json:
            return jsonify({'error': 'Muitas requisições. Tente novamente mais tarde.'}), 429
        
        return render_template('errors/429.html'), 429
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors"""
        app.logger.error(
            f'500 Error: {request.method} {request.path} | '
            f'User: {current_user.id if current_user.is_authenticated else "anonymous"} | '
            f'IP: {request.remote_addr} | '
            f'Error: {str(error)}\n'
            f'Traceback:\n{traceback.format_exc()}'
        )
        
        # Rollback database session on error
        from app import db
        db.session.rollback()
        
        if request.is_json or request.accept_mimetypes.accept_json:
            return jsonify({'error': 'Erro interno do servidor'}), 500
        
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(GEDException)
    def handle_ged_exception(error):
        """Handle custom GED exceptions"""
        app.logger.warning(
            f'GED Exception: {error.__class__.__name__} | '
            f'Message: {error.message} | '
            f'User: {current_user.id if current_user.is_authenticated else "anonymous"} | '
            f'Path: {request.path}'
        )
        
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(AuthenticationError)
    def handle_authentication_error(error):
        """Handle authentication errors"""
        app.logger.warning(
            f'Authentication Error: {error.__class__.__name__} | '
            f'Message: {error.message} | '
            f'IP: {request.remote_addr}'
        )
        
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(AuthorizationError)
    def handle_authorization_error(error):
        """Handle authorization errors"""
        app.logger.warning(
            f'Authorization Error: {error.__class__.__name__} | '
            f'Message: {error.message} | '
            f'User: {current_user.id if current_user.is_authenticated else "anonymous"} | '
            f'Path: {request.path}'
        )
        
        if request.is_json or request.accept_mimetypes.accept_json:
            response = jsonify(error.to_dict())
            response.status_code = error.status_code
            return response
        
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(ValidationError)
    def handle_validation_error(error):
        """Handle validation errors"""
        app.logger.info(
            f'Validation Error: {error.__class__.__name__} | '
            f'Message: {error.message} | '
            f'User: {current_user.id if current_user.is_authenticated else "anonymous"}'
        )
        
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
    
    @app.errorhandler(NotFoundError)
    def handle_not_found_error(error):
        """Handle not found errors"""
        app.logger.info(
            f'Not Found Error: {error.__class__.__name__} | '
            f'Message: {error.message} | '
            f'User: {current_user.id if current_user.is_authenticated else "anonymous"}'
        )
        
        if request.is_json or request.accept_mimetypes.accept_json:
            response = jsonify(error.to_dict())
            response.status_code = error.status_code
            return response
        
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(StorageError)
    def handle_storage_error(error):
        """Handle storage errors"""
        app.logger.error(
            f'Storage Error: {error.__class__.__name__} | '
            f'Message: {error.message} | '
            f'User: {current_user.id if current_user.is_authenticated else "anonymous"}'
        )
        
        response = jsonify(error.to_dict())
        response.status_code = error.status_code
        return response
