"""
Document repository with search, filtering, and permission checks
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import or_, and_, func
from app.repositories.base_repository import BaseRepository
from app.models.document import Documento, Tag, DocumentoTag
from app.models.permission import Permissao


class DocumentRepository(BaseRepository[Documento]):
    """
    Repository for Documento model with specialized search and filtering.
    Handles document queries with permission checks and advanced search.
    """
    
    def __init__(self):
        """Initialize DocumentRepository with Documento model."""
        super().__init__(Documento)
    
    def get_by_hash(self, hash_arquivo: str) -> Optional[Documento]:
        """
        Find document by file hash (for duplicate detection).
        
        Args:
            hash_arquivo: SHA256 hash of file
            
        Returns:
            Documento instance or None
        """
        return self.get_one_by(hash_arquivo=hash_arquivo, status='ativo')
    
    def get_by_user(self, usuario_id: int, status: str = 'ativo') -> List[Documento]:
        """
        Get all documents owned by a user.
        
        Args:
            usuario_id: User ID
            status: Document status filter (default 'ativo')
            
        Returns:
            List of Documento instances
        """
        return self.filter_by(usuario_id=usuario_id, status=status)
    
    def get_by_category(self, categoria_id: int, usuario_id: Optional[int] = None) -> List[Documento]:
        """
        Get documents by category, optionally filtered by user.
        
        Args:
            categoria_id: Category ID
            usuario_id: Optional user ID to filter by ownership
            
        Returns:
            List of Documento instances
        """
        query = self.get_query().filter(
            Documento.categoria_id == categoria_id,
            Documento.status == 'ativo'
        )
        if usuario_id:
            query = query.filter(Documento.usuario_id == usuario_id)
        return query.all()
    
    def get_by_folder(self, pasta_id: int, usuario_id: Optional[int] = None) -> List[Documento]:
        """
        Get documents in a folder, optionally filtered by user.
        
        Args:
            pasta_id: Folder ID
            usuario_id: Optional user ID to filter by ownership
            
        Returns:
            List of Documento instances
        """
        query = self.get_query().filter(
            Documento.pasta_id == pasta_id,
            Documento.status == 'ativo'
        )
        if usuario_id:
            query = query.filter(Documento.usuario_id == usuario_id)
        return query.all()
    
    def get_recent(self, usuario_id: int, days: int = 7, limit: int = 10) -> List[Documento]:
        """
        Get recent documents for a user.
        
        Args:
            usuario_id: User ID
            days: Number of days to look back
            limit: Maximum number of documents to return
            
        Returns:
            List of recent Documento instances
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.get_query().filter(
            Documento.usuario_id == usuario_id,
            Documento.status == 'ativo',
            Documento.data_upload >= cutoff_date
        ).order_by(Documento.data_upload.desc()).limit(limit).all()
    
    def get_deleted(self, usuario_id: Optional[int] = None) -> List[Documento]:
        """
        Get deleted documents (trash).
        
        Args:
            usuario_id: Optional user ID to filter by ownership
            
        Returns:
            List of deleted Documento instances
        """
        query = self.get_query().filter(Documento.status == 'excluido')
        if usuario_id:
            query = query.filter(Documento.usuario_id == usuario_id)
        return query.order_by(Documento.data_exclusao.desc()).all()
    
    def get_expired_trash(self, days: int = 30) -> List[Documento]:
        """
        Get documents in trash older than specified days for permanent deletion.
        
        Args:
            days: Number of days after which to permanently delete
            
        Returns:
            List of Documento instances ready for permanent deletion
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        return self.get_query().filter(
            Documento.status == 'excluido',
            Documento.data_exclusao.isnot(None),
            Documento.data_exclusao <= cutoff_date
        ).all()
    
    def search(
        self,
        query: str,
        usuario_id: Optional[int] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Documento]:
        """
        Search documents by name, description, and tags.
        
        Args:
            query: Search term
            usuario_id: Optional user ID to filter by ownership
            filters: Optional additional filters (categoria_id, tipo_mime, etc.)
            
        Returns:
            List of matching Documento instances
        """
        search_query = self.get_query().filter(Documento.status == 'ativo')
        
        # Text search in name and description
        if query:
            search_pattern = f'%{query}%'
            search_query = search_query.filter(
                or_(
                    Documento.nome.ilike(search_pattern),
                    Documento.descricao.ilike(search_pattern)
                )
            )
        
        # User filter
        if usuario_id:
            search_query = search_query.filter(Documento.usuario_id == usuario_id)
        
        # Additional filters
        if filters:
            if 'categoria_id' in filters:
                search_query = search_query.filter(Documento.categoria_id == filters['categoria_id'])
            if 'tipo_mime' in filters:
                search_query = search_query.filter(Documento.tipo_mime == filters['tipo_mime'])
            if 'data_inicio' in filters:
                search_query = search_query.filter(Documento.data_upload >= filters['data_inicio'])
            if 'data_fim' in filters:
                search_query = search_query.filter(Documento.data_upload <= filters['data_fim'])
            if 'tamanho_min' in filters:
                search_query = search_query.filter(Documento.tamanho_bytes >= filters['tamanho_min'])
            if 'tamanho_max' in filters:
                search_query = search_query.filter(Documento.tamanho_bytes <= filters['tamanho_max'])
        
        return search_query.order_by(Documento.data_upload.desc()).all()
    
    def search_with_permissions(
        self,
        query: str,
        usuario_id: int,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Documento]:
        """
        Search documents that user owns or has permission to view.
        
        Args:
            query: Search term
            usuario_id: User ID
            filters: Optional additional filters
            
        Returns:
            List of Documento instances user can access
        """
        search_query = self.get_query().filter(Documento.status == 'ativo')
        
        # Text search
        if query:
            search_pattern = f'%{query}%'
            search_query = search_query.filter(
                or_(
                    Documento.nome.ilike(search_pattern),
                    Documento.descricao.ilike(search_pattern)
                )
            )
        
        # Permission filter: owned by user OR has permission
        search_query = search_query.outerjoin(Permissao).filter(
            or_(
                Documento.usuario_id == usuario_id,
                and_(
                    Permissao.usuario_id == usuario_id,
                    Permissao.tipo_permissao.in_(['visualizar', 'editar', 'excluir', 'compartilhar'])
                )
            )
        )
        
        # Additional filters
        if filters:
            if 'categoria_id' in filters:
                search_query = search_query.filter(Documento.categoria_id == filters['categoria_id'])
            if 'tipo_mime' in filters:
                search_query = search_query.filter(Documento.tipo_mime == filters['tipo_mime'])
            if 'data_inicio' in filters:
                search_query = search_query.filter(Documento.data_upload >= filters['data_inicio'])
            if 'data_fim' in filters:
                search_query = search_query.filter(Documento.data_upload <= filters['data_fim'])
        
        return search_query.distinct().order_by(Documento.data_upload.desc()).all()
    
    def get_by_tags(self, tag_names: List[str]) -> List[Documento]:
        """
        Get documents that have all specified tags.
        
        Args:
            tag_names: List of tag names
            
        Returns:
            List of Documento instances
        """
        if not tag_names:
            return []
        
        query = self.get_query().join(Documento.tags).filter(
            Tag.nome.in_(tag_names),
            Documento.status == 'ativo'
        ).group_by(Documento.id).having(
            func.count(Tag.id) == len(tag_names)
        )
        return query.all()
    
    def get_storage_usage_by_user(self, usuario_id: int) -> int:
        """
        Calculate total storage used by a user.
        
        Args:
            usuario_id: User ID
            
        Returns:
            Total bytes used
        """
        result = self.session.query(
            func.sum(Documento.tamanho_bytes)
        ).filter(
            Documento.usuario_id == usuario_id,
            Documento.status == 'ativo'
        ).scalar()
        return result or 0
    
    def get_total_storage_usage(self) -> int:
        """
        Calculate total storage used by all documents.
        
        Returns:
            Total bytes used
        """
        result = self.session.query(
            func.sum(Documento.tamanho_bytes)
        ).filter(Documento.status == 'ativo').scalar()
        return result or 0
    
    def get_document_count_by_type(self) -> List[Dict[str, Any]]:
        """
        Get document count grouped by MIME type.
        
        Returns:
            List of dicts with tipo_mime and count
        """
        results = self.session.query(
            Documento.tipo_mime,
            func.count(Documento.id).label('count')
        ).filter(
            Documento.status == 'ativo'
        ).group_by(Documento.tipo_mime).all()
        
        return [{'tipo_mime': r[0], 'count': r[1]} for r in results]
    
    def permanent_delete(self, id: int) -> bool:
        """
        Permanently delete a document (physical deletion).
        
        Args:
            id: Document ID
            
        Returns:
            True if deleted, False if not found
        """
        return self.delete(id)


class TagRepository(BaseRepository[Tag]):
    """
    Repository for Tag model.
    """
    
    def __init__(self):
        """Initialize TagRepository with Tag model."""
        super().__init__(Tag)
    
    def get_by_name(self, nome: str) -> Optional[Tag]:
        """
        Get tag by name.
        
        Args:
            nome: Tag name
            
        Returns:
            Tag instance or None
        """
        return self.get_one_by(nome=nome)
    
    def get_or_create(self, nome: str) -> Tag:
        """
        Get existing tag or create new one.
        
        Args:
            nome: Tag name
            
        Returns:
            Tag instance
        """
        tag = self.get_by_name(nome)
        if not tag:
            tag = self.create(nome=nome)
        return tag
    
    def search_tags(self, query: str, limit: int = 10) -> List[Tag]:
        """
        Search tags by name (for autocomplete).
        
        Args:
            query: Search term
            limit: Maximum number of results
            
        Returns:
            List of matching Tag instances
        """
        return self.get_query().filter(
            Tag.nome.ilike(f'%{query}%')
        ).limit(limit).all()
    
    def get_popular_tags(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get most used tags.
        
        Args:
            limit: Maximum number of tags to return
            
        Returns:
            List of dicts with tag name and usage count
        """
        results = self.session.query(
            Tag.nome,
            func.count(DocumentoTag.documento_id).label('count')
        ).join(DocumentoTag).group_by(Tag.id, Tag.nome).order_by(
            func.count(DocumentoTag.documento_id).desc()
        ).limit(limit).all()
        
        return [{'nome': r[0], 'count': r[1]} for r in results]
