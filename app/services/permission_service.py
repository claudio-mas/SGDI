"""
Permission service for access control and document sharing
Handles permission checking, granting, revocation, and sharing
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from app import db
from app.models.permission import Permissao
from app.models.document import Documento
from app.models.user import User


class PermissionServiceError(Exception):
    """Base exception for permission service errors"""
    pass


class PermissionDeniedError(PermissionServiceError):
    """Raised when user lacks permission for an operation"""
    pass


class InvalidPermissionTypeError(PermissionServiceError):
    """Raised when invalid permission type is provided"""
    pass


class PermissionService:
    """Service for permission and access control operations"""
    
    VALID_PERMISSION_TYPES = ['visualizar', 'editar', 'excluir', 'compartilhar']
    
    def __init__(self):
        """Initialize permission service"""
        pass
    
    def check_permission(
        self,
        documento: Documento,
        user_id: int,
        permission_type: str
    ) -> bool:
        """
        Check if user has specific permission for a document
        
        Args:
            documento: Document to check permission for
            user_id: User ID
            permission_type: Type of permission (visualizar, editar, excluir, compartilhar)
            
        Returns:
            True if user has permission, False otherwise
        """
        # Validate permission type
        if permission_type not in self.VALID_PERMISSION_TYPES:
            raise InvalidPermissionTypeError(
                f"Invalid permission type: {permission_type}. "
                f"Valid types: {', '.join(self.VALID_PERMISSION_TYPES)}"
            )
        
        # Owner has all permissions (owner-based permission inheritance)
        if documento.usuario_id == user_id:
            return True
        
        # Check explicit permissions
        permission = db.session.query(Permissao).filter_by(
            documento_id=documento.id,
            usuario_id=user_id,
            tipo_permissao=permission_type
        ).first()
        
        if permission and not permission.is_expired():
            return True
        
        # For view permission, also check if user has higher-level permissions
        # (edit, delete, or share implies view)
        if permission_type == 'visualizar':
            for perm_type in ['editar', 'excluir', 'compartilhar']:
                permission = db.session.query(Permissao).filter_by(
                    documento_id=documento.id,
                    usuario_id=user_id,
                    tipo_permissao=perm_type
                ).first()
                if permission and not permission.is_expired():
                    return True
        
        return False

    def grant_permission(
        self,
        documento: Documento,
        target_user_id: int,
        permission_type: str,
        granted_by_user_id: int,
        expiration_date: Optional[datetime] = None
    ) -> Permissao:
        """
        Grant permission to a user for a document
        
        Args:
            documento: Document to grant permission for
            target_user_id: ID of user receiving the permission
            permission_type: Type of permission (visualizar, editar, excluir, compartilhar)
            granted_by_user_id: ID of user granting the permission
            expiration_date: Optional expiration date for the permission
            
        Returns:
            Created or updated Permissao instance
            
        Raises:
            PermissionDeniedError: If granting user lacks permission
            InvalidPermissionTypeError: If invalid permission type
        """
        # Validate permission type
        if permission_type not in self.VALID_PERMISSION_TYPES:
            raise InvalidPermissionTypeError(
                f"Invalid permission type: {permission_type}. "
                f"Valid types: {', '.join(self.VALID_PERMISSION_TYPES)}"
            )
        
        # Check if granting user has permission to share
        # Owner can grant any permission, others need 'compartilhar' permission
        if documento.usuario_id != granted_by_user_id:
            if not self.check_permission(documento, granted_by_user_id, 'compartilhar'):
                raise PermissionDeniedError(
                    "You don't have permission to share this document"
                )
        
        # Check if target user exists
        target_user = db.session.query(User).filter_by(id=target_user_id).first()
        if not target_user:
            raise PermissionServiceError(f"User with ID {target_user_id} not found")
        
        # Check if target user is active
        if not target_user.ativo:
            raise PermissionServiceError(f"Cannot grant permission to inactive user")
        
        # Check if permission already exists
        existing_permission = db.session.query(Permissao).filter_by(
            documento_id=documento.id,
            usuario_id=target_user_id,
            tipo_permissao=permission_type
        ).first()
        
        if existing_permission:
            # Update existing permission
            existing_permission.concedido_por = granted_by_user_id
            existing_permission.data_concessao = datetime.utcnow()
            existing_permission.data_expiracao = expiration_date
            db.session.commit()
            return existing_permission
        
        # Create new permission
        permission = Permissao(
            documento_id=documento.id,
            usuario_id=target_user_id,
            tipo_permissao=permission_type,
            concedido_por=granted_by_user_id,
            data_expiracao=expiration_date
        )
        db.session.add(permission)
        db.session.commit()
        
        # Log permission grant
        try:
            from app.services.audit_service import AuditService
            audit_service = AuditService()
            audit_service.log_document_share(
                usuario_id=granted_by_user_id,
                documento_id=documento.id,
                shared_with_user_id=target_user_id,
                permission_type=permission_type
            )
        except Exception as e:
            print(f"Warning: Failed to log permission grant audit entry: {e}")
        
        return permission
    
    def revoke_permission(
        self,
        documento: Documento,
        target_user_id: int,
        permission_type: str,
        revoked_by_user_id: int
    ) -> bool:
        """
        Revoke permission from a user for a document
        
        Args:
            documento: Document to revoke permission for
            target_user_id: ID of user losing the permission
            permission_type: Type of permission to revoke
            revoked_by_user_id: ID of user revoking the permission
            
        Returns:
            True if permission was revoked, False if permission didn't exist
            
        Raises:
            PermissionDeniedError: If revoking user lacks permission
        """
        # Check if revoking user has permission to manage permissions
        # Owner can revoke any permission, others need 'compartilhar' permission
        if documento.usuario_id != revoked_by_user_id:
            if not self.check_permission(documento, revoked_by_user_id, 'compartilhar'):
                raise PermissionDeniedError(
                    "You don't have permission to revoke permissions for this document"
                )
        
        # Find and delete the permission
        permission = db.session.query(Permissao).filter_by(
            documento_id=documento.id,
            usuario_id=target_user_id,
            tipo_permissao=permission_type
        ).first()
        
        if permission:
            db.session.delete(permission)
            db.session.commit()
            
            # Log permission revocation
            try:
                from app.services.audit_service import AuditService
                audit_service = AuditService()
                audit_service.log_action(
                    usuario_id=revoked_by_user_id,
                    acao='revoke_permission',
                    tabela='permissoes',
                    registro_id=documento.id,
                    dados={
                        'target_user_id': target_user_id,
                        'permission_type': permission_type
                    }
                )
            except Exception as e:
                print(f"Warning: Failed to log permission revocation audit entry: {e}")
            
            return True
        
        return False
    
    def revoke_all_permissions(
        self,
        documento: Documento,
        target_user_id: int,
        revoked_by_user_id: int
    ) -> int:
        """
        Revoke all permissions from a user for a document
        
        Args:
            documento: Document to revoke permissions for
            target_user_id: ID of user losing all permissions
            revoked_by_user_id: ID of user revoking the permissions
            
        Returns:
            Number of permissions revoked
            
        Raises:
            PermissionDeniedError: If revoking user lacks permission
        """
        # Check if revoking user has permission to manage permissions
        if documento.usuario_id != revoked_by_user_id:
            if not self.check_permission(documento, revoked_by_user_id, 'compartilhar'):
                raise PermissionDeniedError(
                    "You don't have permission to revoke permissions for this document"
                )
        
        # Delete all permissions for the target user
        count = db.session.query(Permissao).filter_by(
            documento_id=documento.id,
            usuario_id=target_user_id
        ).delete()
        
        db.session.commit()
        return count

    def get_document_permissions(
        self,
        documento: Documento,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get all permissions for a document
        
        Args:
            documento: Document to get permissions for
            user_id: ID of user requesting permissions (must be owner or have share permission)
            
        Returns:
            List of permission dictionaries with user info
            
        Raises:
            PermissionDeniedError: If user lacks permission to view permissions
        """
        # Check if user has permission to view permissions
        if documento.usuario_id != user_id:
            if not self.check_permission(documento, user_id, 'compartilhar'):
                raise PermissionDeniedError(
                    "You don't have permission to view permissions for this document"
                )
        
        # Get all permissions with user info
        permissions = db.session.query(Permissao, User).join(
            User, Permissao.usuario_id == User.id
        ).filter(
            Permissao.documento_id == documento.id
        ).all()
        
        result = []
        for permission, user in permissions:
            result.append({
                'permission_id': permission.id,
                'user_id': user.id,
                'user_name': user.nome,
                'user_email': user.email,
                'permission_type': permission.tipo_permissao,
                'granted_date': permission.data_concessao,
                'expiration_date': permission.data_expiracao,
                'is_expired': permission.is_expired(),
                'granted_by': permission.concedido_por
            })
        
        return result
    
    def get_user_permissions(
        self,
        user_id: int,
        include_expired: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Get all permissions granted to a user
        
        Args:
            user_id: User ID
            include_expired: Whether to include expired permissions
            
        Returns:
            List of permission dictionaries with document info
        """
        query = db.session.query(Permissao, Documento).join(
            Documento, Permissao.documento_id == Documento.id
        ).filter(
            Permissao.usuario_id == user_id,
            Documento.status == 'ativo'  # Only active documents
        )
        
        permissions = query.all()
        
        result = []
        for permission, documento in permissions:
            # Skip expired permissions if not requested
            if not include_expired and permission.is_expired():
                continue
            
            result.append({
                'permission_id': permission.id,
                'document_id': documento.id,
                'document_name': documento.nome,
                'permission_type': permission.tipo_permissao,
                'granted_date': permission.data_concessao,
                'expiration_date': permission.data_expiracao,
                'is_expired': permission.is_expired(),
                'owner_id': documento.usuario_id
            })
        
        return result
    
    def cleanup_expired_permissions(self) -> int:
        """
        Remove expired permissions from the database
        
        Returns:
            Number of permissions removed
        """
        now = datetime.utcnow()
        
        # Delete permissions where expiration date has passed
        count = db.session.query(Permissao).filter(
            Permissao.data_expiracao.isnot(None),
            Permissao.data_expiracao < now
        ).delete()
        
        db.session.commit()
        return count
    
    def share_document(
        self,
        documento: Documento,
        target_user_id: int,
        permission_types: List[str],
        shared_by_user_id: int,
        expiration_days: Optional[int] = None,
        send_notification: bool = True
    ) -> List[Permissao]:
        """
        Share a document with another user (convenience method)
        
        Args:
            documento: Document to share
            target_user_id: ID of user to share with
            permission_types: List of permission types to grant
            shared_by_user_id: ID of user sharing the document
            expiration_days: Optional number of days until permissions expire
            send_notification: Whether to send email notification
            
        Returns:
            List of created Permissao instances
            
        Raises:
            PermissionDeniedError: If sharing user lacks permission
            InvalidPermissionTypeError: If invalid permission type
        """
        # Calculate expiration date if specified
        expiration_date = None
        if expiration_days is not None:
            expiration_date = datetime.utcnow() + timedelta(days=expiration_days)
        
        # Grant each permission type
        permissions = []
        for permission_type in permission_types:
            permission = self.grant_permission(
                documento=documento,
                target_user_id=target_user_id,
                permission_type=permission_type,
                granted_by_user_id=shared_by_user_id,
                expiration_date=expiration_date
            )
            permissions.append(permission)
        
        # Send notification if requested
        if send_notification:
            try:
                from app.services.notification_service import NotificationService
                notification_service = NotificationService()
                notification_service.notify_share(
                    documento=documento,
                    from_user_id=shared_by_user_id,
                    to_user_id=target_user_id,
                    permission_types=permission_types,
                    expiration_date=expiration_date
                )
            except (ImportError, AttributeError):
                # NotificationService not yet fully implemented, skip notification
                pass
        
        return permissions
    
    def unshare_document(
        self,
        documento: Documento,
        target_user_id: int,
        unshared_by_user_id: int
    ) -> int:
        """
        Remove all sharing permissions from a user (convenience method)
        
        Args:
            documento: Document to unshare
            target_user_id: ID of user to remove permissions from
            unshared_by_user_id: ID of user removing the share
            
        Returns:
            Number of permissions revoked
            
        Raises:
            PermissionDeniedError: If unsharing user lacks permission
        """
        return self.revoke_all_permissions(
            documento=documento,
            target_user_id=target_user_id,
            revoked_by_user_id=unshared_by_user_id
        )
    
    def get_shared_with_me(
        self,
        user_id: int,
        permission_type: Optional[str] = None
    ) -> List[Documento]:
        """
        Get documents shared with a user
        
        Args:
            user_id: User ID
            permission_type: Optional filter by permission type
            
        Returns:
            List of Documento instances
        """
        query = db.session.query(Documento).join(
            Permissao, Documento.id == Permissao.documento_id
        ).filter(
            Permissao.usuario_id == user_id,
            Documento.status == 'ativo'
        )
        
        if permission_type:
            query = query.filter(Permissao.tipo_permissao == permission_type)
        
        # Get unique documents (user might have multiple permission types)
        documents = query.distinct().all()
        
        # Filter out expired permissions
        result = []
        for documento in documents:
            # Check if user still has valid permission
            has_valid_permission = False
            for permission in documento.permissoes:
                if permission.usuario_id == user_id and not permission.is_expired():
                    has_valid_permission = True
                    break
            
            if has_valid_permission:
                result.append(documento)
        
        return result
    
    def get_shared_by_me(
        self,
        user_id: int
    ) -> List[Dict[str, Any]]:
        """
        Get documents shared by a user
        
        Args:
            user_id: User ID
            
        Returns:
            List of dictionaries with document and sharing info
        """
        # Get documents owned by user that have permissions granted to others
        documents = db.session.query(Documento).filter(
            Documento.usuario_id == user_id,
            Documento.status == 'ativo'
        ).all()
        
        result = []
        for documento in documents:
            # Get permissions for this document (excluding owner)
            permissions = db.session.query(Permissao, User).join(
                User, Permissao.usuario_id == User.id
            ).filter(
                Permissao.documento_id == documento.id,
                Permissao.usuario_id != user_id
            ).all()
            
            if permissions:
                shared_with = []
                for permission, user in permissions:
                    if not permission.is_expired():
                        shared_with.append({
                            'user_id': user.id,
                            'user_name': user.nome,
                            'user_email': user.email,
                            'permission_type': permission.tipo_permissao,
                            'granted_date': permission.data_concessao,
                            'expiration_date': permission.data_expiracao
                        })
                
                if shared_with:
                    result.append({
                        'document_id': documento.id,
                        'document_name': documento.nome,
                        'shared_with': shared_with
                    })
        
        return result
