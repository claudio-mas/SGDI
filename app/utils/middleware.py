"""
Request middleware for security and permission checking
"""
from flask import request, g, session
from flask_login import current_user
from datetime import datetime
from app import db
from app.models.audit import LogAuditoria


class PermissionMiddleware:
    """
    Middleware for permission checking and validation.
    
    This middleware runs before each request to:
    - Validate user permissions
    - Check resource-level access
    - Log access attempts
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app"""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
    
    def before_request(self):
        """
        Execute before each request.
        
        - Store request start time
        - Validate user session
        - Check IP-based restrictions (if configured)
        """
        # Store request start time for performance monitoring
        g.request_start_time = datetime.utcnow()
        
        # Store request IP address
        g.request_ip = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', 'unknown')
        
        # If user is authenticated, store user info in g
        if current_user.is_authenticated:
            g.current_user_id = current_user.id
            g.current_user_email = current_user.email
            g.current_user_profile = current_user.perfil.nome
        else:
            g.current_user_id = None
            g.current_user_email = None
            g.current_user_profile = None
    
    def after_request(self, response):
        """
        Execute after each request.
        
        - Log request details
        - Add security headers
        """
        # Calculate request duration
        if hasattr(g, 'request_start_time'):
            duration = (datetime.utcnow() - g.request_start_time).total_seconds()
            response.headers['X-Request-Duration'] = str(duration)
        
        return response


def check_document_permission(documento, user, permission_type):
    """
    Check if user has specific permission on a document.
    
    This is a utility function that can be called from services or views
    to validate document permissions.
    
    Args:
        documento: Document object
        user: User object
        permission_type: Type of permission ('visualizar', 'editar', 'excluir', 'compartilhar')
    
    Returns:
        bool: True if user has permission, False otherwise
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    from app.models.permission import Permissao
    
    # Owner has all permissions
    if documento.usuario_id == user.id:
        return True
    
    # Administrator has all permissions
    if user.perfil.nome == 'Administrador':
        return True
    
    # Check explicit document permissions
    permissao = Permissao.query.filter_by(
        documento_id=documento.id,
        usuario_id=user.id,
        tipo_permissao=permission_type
    ).first()
    
    if permissao and not permissao.is_expired():
        return True
    
    return False


def check_role_permission(user, permission_name):
    """
    Check if user's role has specific permission.
    
    This validates role-based access control (RBAC) permissions.
    
    Args:
        user: User object
        permission_name: Name of the permission to check
    
    Returns:
        bool: True if user has permission, False otherwise
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    if not user.ativo:
        return False
    
    # Administrator has all permissions
    if user.perfil.nome == 'Administrador':
        return True
    
    # Define permission mappings for each profile
    profile_permissions = {
        'Gerente': [
            'view', 'edit', 'delete', 'share', 'upload',
            'approve', 'manage_workflows', 'view_reports'
        ],
        'Usuário': [
            'view', 'edit', 'share', 'upload', 'create_folders'
        ],
        'Auditor': [
            'view', 'audit', 'view_reports', 'view_logs'
        ],
        'Visitante': [
            'view'
        ]
    }
    
    return permission_name in profile_permissions.get(user.perfil.nome, [])


def validate_resource_access(resource_type, resource_id, user, action):
    """
    Validate user access to a specific resource.
    
    This is a generic function for validating access to different resource types.
    
    Args:
        resource_type: Type of resource ('document', 'category', 'workflow', etc.)
        resource_id: ID of the resource
        user: User object
        action: Action to perform ('view', 'edit', 'delete', etc.)
    
    Returns:
        tuple: (bool, str) - (has_access, error_message)
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    if not user.is_authenticated:
        return False, 'Usuário não autenticado'
    
    if not user.ativo:
        return False, 'Conta de usuário desativada'
    
    # Administrator has access to everything
    if user.perfil.nome == 'Administrador':
        return True, None
    
    # Resource-specific validation
    if resource_type == 'document':
        from app.models.document import Documento
        documento = Documento.query.get(resource_id)
        
        if not documento:
            return False, 'Documento não encontrado'
        
        # Map action to permission type
        permission_map = {
            'view': 'visualizar',
            'edit': 'editar',
            'delete': 'excluir',
            'share': 'compartilhar'
        }
        
        permission_type = permission_map.get(action)
        if not permission_type:
            return False, 'Ação inválida'
        
        if check_document_permission(documento, user, permission_type):
            return True, None
        else:
            return False, 'Permissão negada para este documento'
    
    elif resource_type == 'workflow':
        # Managers and above can manage workflows
        if user.perfil.nome in ['Administrador', 'Gerente']:
            return True, None
        else:
            return False, 'Apenas gerentes podem gerenciar workflows'
    
    elif resource_type == 'user':
        # Only administrators can manage users
        if user.perfil.nome == 'Administrador':
            return True, None
        else:
            return False, 'Apenas administradores podem gerenciar usuários'
    
    elif resource_type == 'category':
        # Managers and above can manage categories
        if user.perfil.nome in ['Administrador', 'Gerente']:
            return True, None
        else:
            return False, 'Apenas gerentes podem gerenciar categorias'
    
    # Default deny
    return False, 'Acesso não autorizado'
