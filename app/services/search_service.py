"""
Search service for document search functionality
Handles simple search, advanced search with filters, and permission-based result filtering
"""
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from sqlalchemy import or_, and_, func, text
from app import db
from app.models.document import Documento, Tag, DocumentoTag, Categoria
from app.models.permission import Permissao
from app.repositories.document_repository import DocumentRepository, TagRepository
import os
from pathlib import Path


class SearchServiceError(Exception):
    """Base exception for search service errors"""
    pass


class SearchService:
    """Service for document search operations"""
    
    def __init__(
        self,
        document_repository: Optional[DocumentRepository] = None,
        tag_repository: Optional[TagRepository] = None
    ):
        """
        Initialize search service
        
        Args:
            document_repository: Repository for document data access
            tag_repository: Repository for tag data access
        """
        self.document_repository = document_repository or DocumentRepository()
        self.tag_repository = tag_repository or TagRepository()
    
    def search(
        self,
        query: str,
        user_id: int,
        filters: Optional[Dict[str, Any]] = None,
        page: int = 1,
        per_page: int = 20,
        include_shared: bool = True
    ) -> Tuple[List[Documento], int]:
        """
        Unified search with pagination and permission-based filtering
        
        Args:
            query: Search term (searches in name, description, and tags)
            user_id: ID of user performing the search
            filters: Optional filters (categoria_id, tipo_mime, date ranges, etc.)
            page: Page number (1-indexed)
            per_page: Number of results per page
            include_shared: Whether to include documents shared with user
            
        Returns:
            Tuple of (list of Documento instances, total count)
            
        Requirements: 4.1, 4.2, 4.4, 4.5
        """
        # Build base query with permission filtering
        search_query = self._build_base_query(user_id, include_shared)
        
        # Apply text search
        if query and query.strip():
            search_query = self._apply_text_search(search_query, query.strip())
        
        # Apply additional filters
        if filters:
            search_query = self._apply_filters(search_query, filters)
        
        # Get total count before pagination
        total_count = search_query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        results = search_query.order_by(
            Documento.data_upload.desc()
        ).offset(offset).limit(per_page).all()
        
        return results, total_count
    
    def _build_base_query(self, user_id: int, include_shared: bool):
        """
        Build base query with permission filtering
        
        Args:
            user_id: User ID
            include_shared: Whether to include shared documents
            
        Returns:
            SQLAlchemy query object
        """
        # Start with active documents only
        query = db.session.query(Documento).filter(Documento.status == 'ativo')
        
        if include_shared:
            # Include documents owned by user OR shared with user
            query = query.outerjoin(Permissao).filter(
                or_(
                    Documento.usuario_id == user_id,
                    and_(
                        Permissao.usuario_id == user_id,
                        Permissao.tipo_permissao.in_(['visualizar', 'editar', 'excluir', 'compartilhar']),
                        or_(
                            Permissao.data_expiracao.is_(None),
                            Permissao.data_expiracao > datetime.utcnow()
                        )
                    )
                )
            ).distinct()
        else:
            # Only documents owned by user
            query = query.filter(Documento.usuario_id == user_id)
        
        return query
    
    def _apply_text_search(self, query, search_term: str):
        """
        Apply text search to query (searches name, description, and tags)
        
        Args:
            query: SQLAlchemy query object
            search_term: Search term
            
        Returns:
            Modified query object
            
        Requirements: 4.1
        """
        search_pattern = f'%{search_term}%'
        
        # Search in document name and description
        text_filter = or_(
            Documento.nome.ilike(search_pattern),
            Documento.descricao.ilike(search_pattern)
        )
        
        # Also search in tags
        tag_subquery = db.session.query(DocumentoTag.documento_id).join(Tag).filter(
            Tag.nome.ilike(search_pattern)
        ).subquery()
        
        # Combine text search with tag search
        query = query.filter(
            or_(
                text_filter,
                Documento.id.in_(tag_subquery)
            )
        )
        
        return query
    
    def _apply_filters(self, query, filters: Dict[str, Any]):
        """
        Apply advanced filters to query
        
        Args:
            query: SQLAlchemy query object
            filters: Dictionary of filters
            
        Returns:
            Modified query object
            
        Requirements: 4.2
        """
        # Category filter
        if 'categoria_id' in filters and filters['categoria_id']:
            query = query.filter(Documento.categoria_id == filters['categoria_id'])
        
        # File type filter
        if 'tipo_mime' in filters and filters['tipo_mime']:
            query = query.filter(Documento.tipo_mime == filters['tipo_mime'])
        
        # Author/Owner filter
        if 'autor_id' in filters and filters['autor_id']:
            query = query.filter(Documento.usuario_id == filters['autor_id'])
        
        # Date range filters
        if 'data_inicio' in filters and filters['data_inicio']:
            if isinstance(filters['data_inicio'], str):
                data_inicio = datetime.fromisoformat(filters['data_inicio'])
            else:
                data_inicio = filters['data_inicio']
            query = query.filter(Documento.data_upload >= data_inicio)
        
        if 'data_fim' in filters and filters['data_fim']:
            if isinstance(filters['data_fim'], str):
                data_fim = datetime.fromisoformat(filters['data_fim'])
            else:
                data_fim = filters['data_fim']
            query = query.filter(Documento.data_upload <= data_fim)
        
        # File size filters
        if 'tamanho_min' in filters and filters['tamanho_min']:
            query = query.filter(Documento.tamanho_bytes >= filters['tamanho_min'])
        
        if 'tamanho_max' in filters and filters['tamanho_max']:
            query = query.filter(Documento.tamanho_bytes <= filters['tamanho_max'])
        
        # Tag filter (documents must have all specified tags)
        if 'tags' in filters and filters['tags']:
            tag_names = filters['tags'] if isinstance(filters['tags'], list) else [filters['tags']]
            for tag_name in tag_names:
                tag_subquery = db.session.query(DocumentoTag.documento_id).join(Tag).filter(
                    Tag.nome.ilike(tag_name)
                ).subquery()
                query = query.filter(Documento.id.in_(tag_subquery))
        
        # Folder filter
        if 'pasta_id' in filters and filters['pasta_id']:
            query = query.filter(Documento.pasta_id == filters['pasta_id'])
        
        # Extension filter
        if 'extensao' in filters and filters['extensao']:
            ext = filters['extensao'].lower()
            if not ext.startswith('.'):
                ext = f'.{ext}'
            query = query.filter(Documento.nome_arquivo_original.ilike(f'%{ext}'))
        
        return query
    
    def advanced_search(
        self,
        user_id: int,
        nome: Optional[str] = None,
        descricao: Optional[str] = None,
        categoria_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        autor_id: Optional[int] = None,
        tipo_mime: Optional[str] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        tamanho_min: Optional[int] = None,
        tamanho_max: Optional[int] = None,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Documento], int]:
        """
        Advanced search with multiple specific filters
        
        Args:
            user_id: ID of user performing the search
            nome: Document name filter
            descricao: Description filter
            categoria_id: Category ID filter
            tags: List of tag names (documents must have all tags)
            autor_id: Author/owner ID filter
            tipo_mime: MIME type filter
            data_inicio: Start date filter
            data_fim: End date filter
            tamanho_min: Minimum file size in bytes
            tamanho_max: Maximum file size in bytes
            page: Page number
            per_page: Results per page
            
        Returns:
            Tuple of (list of Documento instances, total count)
            
        Requirements: 4.2, 4.4
        """
        # Build filters dictionary
        filters = {}
        
        if categoria_id:
            filters['categoria_id'] = categoria_id
        if autor_id:
            filters['autor_id'] = autor_id
        if tipo_mime:
            filters['tipo_mime'] = tipo_mime
        if data_inicio:
            filters['data_inicio'] = data_inicio
        if data_fim:
            filters['data_fim'] = data_fim
        if tamanho_min:
            filters['tamanho_min'] = tamanho_min
        if tamanho_max:
            filters['tamanho_max'] = tamanho_max
        if tags:
            filters['tags'] = tags
        
        # Combine nome and descricao into a single query string
        query_parts = []
        if nome:
            query_parts.append(nome)
        if descricao:
            query_parts.append(descricao)
        
        query_string = ' '.join(query_parts) if query_parts else ''
        
        # Use unified search
        return self.search(
            query=query_string,
            user_id=user_id,
            filters=filters,
            page=page,
            per_page=per_page,
            include_shared=True
        )
    
    def get_quick_filter_results(
        self,
        user_id: int,
        filter_type: str,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Documento], int]:
        """
        Get results for quick filters (My Documents, Recent, Favorites, Pending Approval)
        
        Args:
            user_id: User ID
            filter_type: Type of quick filter ('my_documents', 'recent', 'favorites', 'pending_approval')
            page: Page number
            per_page: Results per page
            
        Returns:
            Tuple of (list of Documento instances, total count)
            
        Requirements: 4.5
        """
        query = db.session.query(Documento).filter(Documento.status == 'ativo')
        
        if filter_type == 'my_documents':
            # Documents owned by user
            query = query.filter(Documento.usuario_id == user_id)
        
        elif filter_type == 'recent':
            # Documents uploaded in last 7 days (owned or shared)
            from datetime import timedelta
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            query = query.outerjoin(Permissao).filter(
                or_(
                    Documento.usuario_id == user_id,
                    and_(
                        Permissao.usuario_id == user_id,
                        Permissao.tipo_permissao.in_(['visualizar', 'editar', 'excluir', 'compartilhar'])
                    )
                ),
                Documento.data_upload >= cutoff_date
            ).distinct()
        
        elif filter_type == 'favorites':
            # Favorite documents of current user
            from app.models.document import Favorito
            query = query.join(Favorito).filter(
                Favorito.usuario_id == user_id
            ).distinct()
        
        elif filter_type == 'pending_approval':
            # Documents pending approval (requires workflow integration)
            # This will be fully implemented when workflow service is complete
            from app.models.workflow import AprovacaoDocumento
            pending_subquery = db.session.query(AprovacaoDocumento.documento_id).filter(
                AprovacaoDocumento.status == 'pendente'
            ).subquery()
            query = query.filter(Documento.id.in_(pending_subquery))
        
        else:
            raise SearchServiceError(f"Unknown quick filter type: {filter_type}")
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        results = query.order_by(Documento.data_upload.desc()).offset(offset).limit(per_page).all()
        
        return results, total_count
    
    def get_search_statistics(self, user_id: int) -> Dict[str, Any]:
        """
        Get search-related statistics for user
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with statistics
        """
        # Count documents by ownership and sharing
        owned_count = db.session.query(func.count(Documento.id)).filter(
            Documento.usuario_id == user_id,
            Documento.status == 'ativo'
        ).scalar()
        
        shared_count = db.session.query(func.count(Documento.id.distinct())).join(Permissao).filter(
            Permissao.usuario_id == user_id,
            Documento.status == 'ativo',
            Documento.usuario_id != user_id
        ).scalar()
        
        # Recent documents (last 7 days)
        from datetime import timedelta
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        recent_count = db.session.query(func.count(Documento.id)).filter(
            Documento.usuario_id == user_id,
            Documento.status == 'ativo',
            Documento.data_upload >= cutoff_date
        ).scalar()
        
        return {
            'owned_documents': owned_count or 0,
            'shared_documents': shared_count or 0,
            'recent_documents': recent_count or 0,
            'total_accessible': (owned_count or 0) + (shared_count or 0)
        }
    
    def fulltext_search(
        self,
        query: str,
        user_id: int,
        page: int = 1,
        per_page: int = 20
    ) -> Tuple[List[Documento], int]:
        """
        Full-text search in document content using SQL Server Full-Text Search
        
        Args:
            query: Search term for full-text search
            user_id: ID of user performing the search
            page: Page number
            per_page: Results per page
            
        Returns:
            Tuple of (list of Documento instances, total count)
            
        Requirements: 4.3
        
        Note: This requires SQL Server Full-Text Search to be configured.
        If full-text search is not available, falls back to regular search.
        """
        try:
            # Build base query with permissions
            base_query = self._build_base_query(user_id, include_shared=True)
            
            # Use SQL Server CONTAINS function for full-text search
            # This searches in the conteudo_texto column (extracted PDF text)
            fulltext_filter = text(
                "CONTAINS(documentos.conteudo_texto, :search_term)"
            ).bindparams(search_term=query)
            
            search_query = base_query.filter(fulltext_filter)
            
            # Get total count
            total_count = search_query.count()
            
            # Apply pagination
            offset = (page - 1) * per_page
            results = search_query.order_by(
                Documento.data_upload.desc()
            ).offset(offset).limit(per_page).all()
            
            return results, total_count
            
        except Exception as e:
            # If full-text search fails (not configured or other error),
            # fall back to regular search
            print(f"Full-text search error: {e}. Falling back to regular search.")
            return self.search(
                query=query,
                user_id=user_id,
                page=page,
                per_page=per_page
            )
    
    @staticmethod
    def extract_pdf_text(file_path: str) -> Optional[str]:
        """
        Extract text content from PDF file for indexing
        
        Args:
            file_path: Path to PDF file
            
        Returns:
            Extracted text or None if extraction fails
            
        Requirements: 4.3
        """
        try:
            import PyPDF2
            
            # Convert to Path object
            pdf_path = Path(file_path)
            
            if not pdf_path.exists():
                return None
            
            # Open and read PDF
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text_content = []
                
                # Extract text from each page
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                
                # Join all pages
                full_text = '\n'.join(text_content)
                
                # Limit text length to avoid database issues (max 4000 chars for indexing)
                if len(full_text) > 4000:
                    full_text = full_text[:4000]
                
                return full_text if full_text.strip() else None
                
        except ImportError:
            print("PyPDF2 not installed. PDF text extraction unavailable.")
            return None
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
            return None
    
    @staticmethod
    def setup_fulltext_catalog():
        """
        Set up SQL Server Full-Text Search catalog and index
        
        This method creates the full-text catalog and index on the documentos table.
        Should be run once during database initialization.
        
        Requirements: 4.3
        
        Note: This requires SQL Server Full-Text Search feature to be installed.
        """
        try:
            # Check if full-text catalog exists
            check_catalog = text("""
                SELECT COUNT(*) 
                FROM sys.fulltext_catalogs 
                WHERE name = 'ged_fulltext_catalog'
            """)
            
            result = db.session.execute(check_catalog).scalar()
            
            if result == 0:
                # Create full-text catalog
                create_catalog = text("""
                    CREATE FULLTEXT CATALOG ged_fulltext_catalog AS DEFAULT
                """)
                db.session.execute(create_catalog)
                db.session.commit()
                print("Full-text catalog created successfully.")
            
            # Check if full-text index exists
            check_index = text("""
                SELECT COUNT(*) 
                FROM sys.fulltext_indexes 
                WHERE object_id = OBJECT_ID('documentos')
            """)
            
            result = db.session.execute(check_index).scalar()
            
            if result == 0:
                # First, ensure conteudo_texto column exists
                check_column = text("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_NAME = 'documentos' AND COLUMN_NAME = 'conteudo_texto'
                """)
                
                column_exists = db.session.execute(check_column).scalar()
                
                if column_exists == 0:
                    # Add conteudo_texto column
                    add_column = text("""
                        ALTER TABLE documentos 
                        ADD conteudo_texto NVARCHAR(MAX)
                    """)
                    db.session.execute(add_column)
                    db.session.commit()
                    print("Added conteudo_texto column to documentos table.")
                
                # Create full-text index
                create_index = text("""
                    CREATE FULLTEXT INDEX ON documentos(
                        nome LANGUAGE 1046,
                        descricao LANGUAGE 1046,
                        conteudo_texto LANGUAGE 1046
                    )
                    KEY INDEX PK__document__3213E83F (id)
                    ON ged_fulltext_catalog
                    WITH CHANGE_TRACKING AUTO
                """)
                db.session.execute(create_index)
                db.session.commit()
                print("Full-text index created successfully.")
            
            return True
            
        except Exception as e:
            print(f"Error setting up full-text search: {e}")
            db.session.rollback()
            return False
    
    def index_document_content(self, documento: Documento, file_path: str) -> bool:
        """
        Extract and index document content for full-text search
        
        Args:
            documento: Documento instance to index
            file_path: Path to the document file
            
        Returns:
            True if indexing successful, False otherwise
            
        Requirements: 4.3
        """
        try:
            # Only extract text from PDFs for now
            if documento.tipo_mime == 'application/pdf':
                extracted_text = self.extract_pdf_text(file_path)
                
                if extracted_text:
                    # Update documento with extracted text
                    # Note: This requires conteudo_texto column to exist
                    update_query = text("""
                        UPDATE documentos 
                        SET conteudo_texto = :texto 
                        WHERE id = :doc_id
                    """)
                    
                    db.session.execute(
                        update_query,
                        {'texto': extracted_text, 'doc_id': documento.id}
                    )
                    db.session.commit()
                    return True
            
            return False
            
        except Exception as e:
            print(f"Error indexing document content: {e}")
            db.session.rollback()
            return False
    
    def get_suggestions(
        self,
        partial_query: str,
        user_id: int,
        limit: int = 10
    ) -> Dict[str, List[str]]:
        """
        Get search suggestions based on partial query
        
        Returns suggestions from document names, tags, and categories
        
        Args:
            partial_query: Partial search term
            user_id: User ID (for permission filtering)
            limit: Maximum number of suggestions per category
            
        Returns:
            Dictionary with suggestion categories:
            {
                'documents': ['doc1', 'doc2', ...],
                'tags': ['tag1', 'tag2', ...],
                'categories': ['cat1', 'cat2', ...]
            }
            
        Requirements: 3.5, 4.1
        """
        if not partial_query or len(partial_query) < 2:
            return {'documents': [], 'tags': [], 'categories': []}
        
        search_pattern = f'%{partial_query}%'
        
        # Get document name suggestions (only accessible documents)
        doc_query = self._build_base_query(user_id, include_shared=True)
        doc_suggestions = doc_query.filter(
            Documento.nome.ilike(search_pattern)
        ).with_entities(Documento.nome).distinct().limit(limit).all()
        
        document_names = [doc[0] for doc in doc_suggestions]
        
        # Get tag suggestions
        tag_suggestions = self.tag_repository.search_tags(partial_query, limit)
        tag_names = [tag.nome for tag in tag_suggestions]
        
        # Get category suggestions
        category_suggestions = db.session.query(Categoria).filter(
            Categoria.nome.ilike(search_pattern),
            Categoria.ativo == True
        ).limit(limit).all()
        category_names = [cat.nome for cat in category_suggestions]
        
        return {
            'documents': document_names,
            'tags': tag_names,
            'categories': category_names
        }
    
    def get_tag_autocomplete(
        self,
        partial_tag: str,
        limit: int = 10
    ) -> List[str]:
        """
        Get tag autocomplete suggestions
        
        Args:
            partial_tag: Partial tag name
            limit: Maximum number of suggestions
            
        Returns:
            List of matching tag names
            
        Requirements: 3.5
        """
        if not partial_tag or len(partial_tag) < 1:
            # Return popular tags if no query
            popular = self.tag_repository.get_popular_tags(limit)
            return [tag['nome'] for tag in popular]
        
        # Search for matching tags
        tags = self.tag_repository.search_tags(partial_tag, limit)
        return [tag.nome for tag in tags]
    
    def get_category_autocomplete(
        self,
        partial_category: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get category autocomplete suggestions
        
        Args:
            partial_category: Partial category name
            limit: Maximum number of suggestions
            
        Returns:
            List of dictionaries with category info:
            [
                {'id': 1, 'nome': 'Category Name', 'caminho': 'Parent > Category Name'},
                ...
            ]
            
        Requirements: 3.5
        """
        if not partial_category or len(partial_category) < 1:
            # Return root categories if no query
            categories = db.session.query(Categoria).filter(
                Categoria.ativo == True,
                Categoria.categoria_pai_id.is_(None)
            ).order_by(Categoria.ordem, Categoria.nome).limit(limit).all()
        else:
            # Search for matching categories
            search_pattern = f'%{partial_category}%'
            categories = db.session.query(Categoria).filter(
                Categoria.nome.ilike(search_pattern),
                Categoria.ativo == True
            ).order_by(Categoria.nome).limit(limit).all()
        
        return [
            {
                'id': cat.id,
                'nome': cat.nome,
                'caminho': cat.caminho_completo
            }
            for cat in categories
        ]
    
    def get_recent_searches(self, user_id: int, limit: int = 10) -> List[str]:
        """
        Get recent search queries for a user
        
        Note: This requires a search_history table to be implemented.
        For now, returns empty list as placeholder.
        
        Args:
            user_id: User ID
            limit: Maximum number of recent searches
            
        Returns:
            List of recent search queries
        """
        # TODO: Implement search history tracking
        # This would require a new table: search_history
        # For now, return empty list
        return []
