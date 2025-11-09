"""
Permission repository for data access
"""
from typing import Optional, List
from datetime import datetime
from app.repositories.base_repository import BaseRepository
from app.models.permission import Permissao
from app import db


class PermissionRepository(BaseRepository):
    """Repository for permission data access"""
    
    def __init__(self):
        """Initialize permission repository"""
        super().__init__(Permissao)
    
    def get_by_document_and_user(
        self,
        documento_id: int,
        usuario_id: int,
        tipo_permissao: Optional[str] = None
    ) -> Optional[Permissao]:
        """
        Get permission by document and user
        
        Args:
            documento_id: Document ID
            usuario_id: User ID
            tipo_permissao: Optional permission type filter
            
        Returns:
            Permissao instance or None
        """
        query = self.model.query.filter_by(
            documento_id=documento_id,
            usuario_id=usuario_id
        )
        
        if tipo_permissao:
            query = query.filter_by(tipo_permissao=tipo_permissao)
        
        return query.first()
    
    def get_by_document(
        self,
        documento_id: int,
        include_expired: bool = False
    ) -> List[Permissao]:
        """
        Get all permissions for a document
        
        Args:
            documento_id: Document ID
            include_expired: Whether to include expired permissions
            
        Returns:
            List of Permissao instances
        """
        query = self.model.query.filter_by(documento_id=documento_id)
        
        permissions = query.all()
        
        if not include_expired:
            permissions = [p for p in permissions if not p.is_expired()]
        
        return permissions
    
    def get_by_user(
        self,
        usuario_id: int,
        include_expired: bool = False
    ) -> List[Permissao]:
        """
        Get all permissions for a user
        
        Args:
            usuario_id: User ID
            include_expired: Whether to include expired permissions
            
        Returns:
            List of Permissao instances
        """
        query = self.model.query.filter_by(usuario_id=usuario_id)
        
        permissions = query.all()
        
        if not include_expired:
            permissions = [p for p in permissions if not p.is_expired()]
        
        return permissions
    
    def delete_by_document_and_user(
        self,
        documento_id: int,
        usuario_id: int,
        tipo_permissao: Optional[str] = None
    ) -> int:
        """
        Delete permissions by document and user
        
        Args:
            documento_id: Document ID
            usuario_id: User ID
            tipo_permissao: Optional permission type filter
            
        Returns:
            Number of permissions deleted
        """
        query = self.model.query.filter_by(
            documento_id=documento_id,
            usuario_id=usuario_id
        )
        
        if tipo_permissao:
            query = query.filter_by(tipo_permissao=tipo_permissao)
        
        count = query.delete()
        db.session.commit()
        return count
    
    def delete_expired(self) -> int:
        """
        Delete all expired permissions
        
        Returns:
            Number of permissions deleted
        """
        now = datetime.utcnow()
        
        count = self.model.query.filter(
            self.model.data_expiracao.isnot(None),
            self.model.data_expiracao < now
        ).delete()
        
        db.session.commit()
        return count
    
    def get_expired(self) -> List[Permissao]:
        """
        Get all expired permissions
        
        Returns:
            List of expired Permissao instances
        """
        now = datetime.utcnow()
        
        return self.model.query.filter(
            self.model.data_expiracao.isnot(None),
            self.model.data_expiracao < now
        ).all()
