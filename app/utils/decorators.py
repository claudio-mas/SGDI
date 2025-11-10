"""
Security decorators and middleware
"""
from functools import wraps
from datetime import datetime
from flask import session, redirect, url_for, flash, request, abort
from flask_login import current_user
from app.models.permission import Permissao
from app.models.document import Documento
from app import db


def login_required(f):
    """
    Decorator to require user authentication with session validation and timeout.
    
    This decorator:
    - Checks if user is authenticated
    - Validates session is not expired
    - Implements automatic session timeout
    - Updates last activity timestamp
    
    Requirements: 1.1, 14.1
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if user is authenticated
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        # Check if account is locked
        if current_user.is_account_locked():
            flash('Sua conta está temporariamente bloqueada. Tente novamente mais tarde.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Check if account is active
        if not current_user.ativo:
            flash('Sua conta está desativada. Entre em contato com o administrador.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Session timeout validation
        last_activity = session.get('last_activity')
        if last_activity:
            last_activity_time = datetime.fromisoformat(last_activity)
            session_timeout = request.app.config.get('PERMANENT_SESSION_LIFETIME')
            
            # Check if session has expired
            if datetime.utcnow() - last_activity_time > session_timeout:
                flash('Sua sessão expirou. Por favor, faça login novamente.', 'info')
                session.clear()
                return redirect(url_for('auth.login', next=request.url))
        
        # Update last activity timestamp
        session['last_activity'] = datetime.utcnow().isoformat()
        session.modified = True
        
        # Update user's last access time (periodically, not on every request)
        if not current_user.ultimo_acesso or \
           (datetime.utcnow() - current_user.ultimo_acesso).seconds > 300:  # Update every 5 minutes
            current_user.ultimo_acesso = datetime.utcnow()
            db.session.commit()
        
        return f(*args, **kwargs)
    
    return decorated_function


def permission_required(permission_type):
    """
    Decorator to check if user has specific permission.
    
    This decorator checks role-based permissions at the profile level.
    For document-specific permissions, use document_permission_required.
    
    Args:
        permission_type: Type of permission required (e.g., 'view', 'edit', 'delete', 'share', 'approve')
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # First check if user is authenticated
            if not current_user.is_authenticated:
                flash('Por favor, faça login para acessar esta página.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # Check if user has the required permission
            if not current_user.has_permission(permission_type):
                flash('Você não tem permissão para realizar esta ação.', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def document_permission_required(permission_type, document_id_param='document_id'):
    """
    Decorator to check if user has specific permission on a document.
    
    This decorator validates resource-level permissions for documents.
    It checks:
    - If user is the document owner
    - If user has explicit permission granted
    - If user's role allows the action
    
    Args:
        permission_type: Type of permission required ('visualizar', 'editar', 'excluir', 'compartilhar')
        document_id_param: Name of the parameter containing document ID (default: 'document_id')
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # First check if user is authenticated
            if not current_user.is_authenticated:
                flash('Por favor, faça login para acessar esta página.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            # Get document ID from kwargs or args
            document_id = kwargs.get(document_id_param)
            if document_id is None:
                # Try to get from view args
                document_id = request.view_args.get(document_id_param)
            
            if document_id is None:
                flash('ID do documento não fornecido.', 'danger')
                abort(400)
            
            # Get document
            documento = Documento.query.get(document_id)
            if not documento:
                flash('Documento não encontrado.', 'danger')
                abort(404)
            
            # Check if document is deleted (only owner can access deleted documents)
            if documento.status == 'excluido' and documento.usuario_id != current_user.id:
                flash('Documento não encontrado.', 'danger')
                abort(404)
            
            # Check permissions
            has_permission = False
            
            # 1. Owner has all permissions
            if documento.usuario_id == current_user.id:
                has_permission = True
            
            # 2. Administrator has all permissions
            elif current_user.perfil.nome == 'Administrador':
                has_permission = True
            
            # 3. Check explicit document permissions
            else:
                permissao = Permissao.query.filter_by(
                    documento_id=document_id,
                    usuario_id=current_user.id,
                    tipo_permissao=permission_type
                ).first()
                
                if permissao and not permissao.is_expired():
                    has_permission = True
            
            if not has_permission:
                flash('Você não tem permissão para acessar este documento.', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


def admin_required(f):
    """
    Decorator to require administrator role.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check if user is authenticated
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        # Check if user is administrator
        if current_user.perfil.nome != 'Administrador':
            flash('Acesso restrito a administradores.', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    
    return decorated_function


def manager_or_admin_required(f):
    """
    Decorator to require manager or administrator role.
    
    Requirements: 5.1, 5.2, 5.3, 5.4, 5.5
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # First check if user is authenticated
        if not current_user.is_authenticated:
            flash('Por favor, faça login para acessar esta página.', 'warning')
            return redirect(url_for('auth.login', next=request.url))
        
        # Check if user is manager or administrator
        if current_user.perfil.nome not in ['Administrador', 'Gerente']:
            flash('Acesso restrito a gerentes e administradores.', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    
    return decorated_function
