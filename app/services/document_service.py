"""
Document service for document management operations
Handles document upload, retrieval, update, deletion, and versioning
"""
from typing import Optional, List, Dict, Any, BinaryIO
from datetime import datetime, timedelta
from werkzeug.datastructures import FileStorage
from app import db
from app.models.document import Documento, Tag, DocumentoTag
from app.models.version import Versao
from app.models.permission import Permissao
from app.repositories.document_repository import DocumentRepository, TagRepository
from app.services.storage_service import StorageService
from app.utils.file_handler import FileHandler, FileValidationError


class DocumentServiceError(Exception):
    """Base exception for document service errors"""
    pass


class DuplicateDocumentError(DocumentServiceError):
    """Raised when attempting to upload a duplicate document"""
    pass


class PermissionDeniedError(DocumentServiceError):
    """Raised when user lacks permission for an operation"""
    pass


class DocumentNotFoundError(DocumentServiceError):
    """Raised when document is not found"""
    pass


class VersionLimitExceededError(DocumentServiceError):
    """Raised when version limit is exceeded"""
    pass


class DocumentService:
    """Service for document management operations"""
    
    def __init__(
        self,
        storage_service: StorageService,
        file_handler: FileHandler,
        document_repository: Optional[DocumentRepository] = None,
        tag_repository: Optional[TagRepository] = None
    ):
        """
        Initialize document service
        
        Args:
            storage_service: Service for file storage operations
            file_handler: Handler for file validation
            document_repository: Repository for document data access
            tag_repository: Repository for tag data access
        """
        self.storage_service = storage_service
        self.file_handler = file_handler
        self.document_repository = document_repository or DocumentRepository()
        self.tag_repository = tag_repository or TagRepository()
    
    def upload_document(
        self,
        file: FileStorage,
        user_id: int,
        nome: Optional[str] = None,
        descricao: Optional[str] = None,
        categoria_id: Optional[int] = None,
        pasta_id: Optional[int] = None,
        tags: Optional[List[str]] = None,
        check_duplicates: bool = True
    ) -> Documento:
        """
        Upload a new document with validation and metadata
        
        Args:
            file: File to upload
            user_id: ID of user uploading the document
            nome: Document name (defaults to filename if not provided)
            descricao: Document description
            categoria_id: Category ID
            pasta_id: Folder ID
            tags: List of tag names
            check_duplicates: Whether to check for duplicate files
            
        Returns:
            Created Documento instance
            
        Raises:
            FileValidationError: If file validation fails
            DuplicateDocumentError: If duplicate file is detected
        """
        # Validate file
        validation_result = self.file_handler.validate_file(file.stream, file.filename)
        
        # Check for duplicates if enabled
        if check_duplicates:
            existing_doc = self.document_repository.get_by_hash(validation_result['file_hash'])
            if existing_doc:
                raise DuplicateDocumentError(
                    f"Document with same content already exists: {existing_doc.nome}"
                )
        
        # Save file to storage
        storage_result = self.storage_service.save_file(
            file.stream,
            file.filename,
            user_id
        )
        
        # Use provided name or default to original filename
        document_name = nome or storage_result['original_filename']
        
        # Create document record
        documento = self.document_repository.create(
            nome=document_name,
            descricao=descricao or '',
            caminho_arquivo=storage_result['file_path'],
            nome_arquivo_original=storage_result['original_filename'],
            tamanho_bytes=validation_result['file_size'],
            tipo_mime=validation_result['mime_type'],
            hash_arquivo=validation_result['file_hash'],
            categoria_id=categoria_id,
            pasta_id=pasta_id,
            usuario_id=user_id,
            versao_atual=1,
            status='ativo'
        )
        
        # Process and associate tags
        if tags:
            self._associate_tags(documento, tags)
        
        # Create initial version record
        self._create_version_record(
            documento=documento,
            user_id=user_id,
            caminho_arquivo=storage_result['file_path'],
            tamanho_bytes=validation_result['file_size'],
            comentario='Initial version'
        )
        
        # Log document upload
        try:
            from app.services.audit_service import AuditService
            audit_service = AuditService()
            audit_service.log_document_upload(
                usuario_id=user_id,
                documento_id=documento.id,
                nome=documento.nome,
                tamanho_bytes=documento.tamanho_bytes,
                tipo_mime=documento.tipo_mime
            )
        except Exception as e:
            # Don't fail the operation if audit logging fails
            print(f"Warning: Failed to log upload audit entry: {e}")
        
        # Send upload notification
        try:
            from app.services.notification_service import NotificationService
            notification_service = NotificationService()
            notification_service.notify_upload(documento, user_id)
        except Exception as e:
            # Don't fail the operation if notification fails
            print(f"Warning: Failed to send upload notification: {e}")
        
        return documento
    
    def _associate_tags(self, documento: Documento, tag_names: List[str]) -> None:
        """
        Associate tags with a document
        
        Args:
            documento: Document to associate tags with
            tag_names: List of tag names
        """
        for tag_name in tag_names:
            # Clean and normalize tag name
            tag_name = tag_name.strip().lower()
            if not tag_name:
                continue
            
            # Get or create tag
            tag = self.tag_repository.get_or_create(nome=tag_name)
            
            # Check if association already exists
            existing = db.session.query(DocumentoTag).filter_by(
                documento_id=documento.id,
                tag_id=tag.id
            ).first()
            
            if not existing:
                # Create association
                doc_tag = DocumentoTag(
                    documento_id=documento.id,
                    tag_id=tag.id
                )
                db.session.add(doc_tag)
        
        db.session.commit()
    
    def _create_version_record(
        self,
        documento: Documento,
        user_id: int,
        caminho_arquivo: str,
        tamanho_bytes: int,
        comentario: str
    ) -> Versao:
        """
        Create a version record for a document
        
        Args:
            documento: Document to create version for
            user_id: ID of user creating the version
            caminho_arquivo: Path to version file
            tamanho_bytes: Size of version file
            comentario: Version comment
            
        Returns:
            Created Versao instance
        """
        versao = Versao(
            documento_id=documento.id,
            numero_versao=documento.versao_atual,
            caminho_arquivo=caminho_arquivo,
            tamanho_bytes=tamanho_bytes,
            usuario_id=user_id,
            comentario=comentario
        )
        db.session.add(versao)
        db.session.commit()
        return versao

    def get_document(self, document_id: int, user_id: int) -> Documento:
        """
        Get document by ID with permission check
        
        Args:
            document_id: Document ID
            user_id: ID of user requesting the document
            
        Returns:
            Documento instance
            
        Raises:
            DocumentNotFoundError: If document not found
            PermissionDeniedError: If user lacks permission
        """
        documento = self.document_repository.get_by_id(document_id)
        
        if not documento:
            raise DocumentNotFoundError(f"Document with ID {document_id} not found")
        
        # Check if user has permission to view
        if not self._has_permission(documento, user_id, 'visualizar'):
            raise PermissionDeniedError("You don't have permission to view this document")
        
        return documento
    
    def _has_permission(
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
        # Owner has all permissions
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
        
        # For view permission, also check if user has edit, delete, or share permission
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
    
    def download_document(self, document_id: int, user_id: int) -> Dict[str, Any]:
        """
        Prepare document for download with permission check
        
        Args:
            document_id: Document ID
            user_id: ID of user downloading the document
            
        Returns:
            Dictionary with file path and metadata
            {
                'file_path': Path object,
                'filename': 'original_filename.ext',
                'mime_type': 'application/pdf',
                'size': 1024000
            }
            
        Raises:
            DocumentNotFoundError: If document not found
            PermissionDeniedError: If user lacks permission
        """
        # Get document with permission check
        documento = self.get_document(document_id, user_id)
        
        # Get file from storage
        file_path = self.storage_service.get_file(documento.caminho_arquivo)
        
        if not file_path:
            raise DocumentServiceError(f"File not found in storage: {documento.caminho_arquivo}")
        
        # Log access for audit trail
        self._log_access(documento, user_id, 'download')
        
        return {
            'file_path': file_path,
            'filename': documento.nome_arquivo_original,
            'mime_type': documento.tipo_mime,
            'size': documento.tamanho_bytes
        }
    
    def view_document(self, document_id: int, user_id: int) -> Dict[str, Any]:
        """
        Get document for viewing/preview with permission check
        
        Args:
            document_id: Document ID
            user_id: ID of user viewing the document
            
        Returns:
            Dictionary with document data and file path
            
        Raises:
            DocumentNotFoundError: If document not found
            PermissionDeniedError: If user lacks permission
        """
        # Get document with permission check
        documento = self.get_document(document_id, user_id)
        
        # Get file from storage
        file_path = self.storage_service.get_file(documento.caminho_arquivo)
        
        if not file_path:
            raise DocumentServiceError(f"File not found in storage: {documento.caminho_arquivo}")
        
        # Log access for audit trail
        self._log_access(documento, user_id, 'view')
        
        return {
            'documento': documento,
            'file_path': file_path
        }
    
    def _log_access(self, documento: Documento, user_id: int, action: str) -> None:
        """
        Log document access for audit trail
        
        Args:
            documento: Document being accessed
            user_id: ID of user accessing the document
            action: Action being performed (view, download, etc.)
        """
        try:
            from app.services.audit_service import AuditService
            audit_service = AuditService()
            
            # Map action to appropriate audit service method
            if action == 'download':
                audit_service.log_document_download(user_id, documento.id, documento.nome)
            elif action == 'view':
                audit_service.log_document_view(user_id, documento.id, documento.nome)
            elif action == 'update_metadata':
                audit_service.log_document_edit(user_id, documento.id, documento.nome)
            elif action == 'soft_delete':
                audit_service.log_document_delete(user_id, documento.id, documento.nome, permanent=False)
            elif action == 'permanent_delete':
                audit_service.log_document_delete(user_id, documento.id, documento.nome, permanent=True)
            elif action == 'restore':
                audit_service.log_document_restore(user_id, documento.id, documento.nome)
            elif action == 'create_version':
                audit_service.log_action(
                    usuario_id=user_id,
                    acao='create_version',
                    tabela='documentos',
                    registro_id=documento.id,
                    dados={'nome': documento.nome}
                )
            elif action.startswith('restore_version_'):
                version_number = action.split('_')[-1]
                audit_service.log_action(
                    usuario_id=user_id,
                    acao='restore_version',
                    tabela='documentos',
                    registro_id=documento.id,
                    dados={'nome': documento.nome, 'version_number': version_number}
                )
            else:
                # Generic logging for other actions
                audit_service.log_action(
                    usuario_id=user_id,
                    acao=action,
                    tabela='documentos',
                    registro_id=documento.id,
                    dados={'nome': documento.nome, 'tipo': documento.tipo_mime}
                )
        except Exception as e:
            # Don't fail the operation if audit logging fails
            print(f"Warning: Failed to log audit entry: {e}")

    def update_document_metadata(
        self,
        document_id: int,
        user_id: int,
        nome: Optional[str] = None,
        descricao: Optional[str] = None,
        categoria_id: Optional[int] = None,
        pasta_id: Optional[int] = None,
        tags: Optional[List[str]] = None
    ) -> Documento:
        """
        Update document metadata
        
        Args:
            document_id: Document ID
            user_id: ID of user updating the document
            nome: New document name
            descricao: New description
            categoria_id: New category ID
            pasta_id: New folder ID
            tags: New list of tag names (replaces existing tags)
            
        Returns:
            Updated Documento instance
            
        Raises:
            DocumentNotFoundError: If document not found
            PermissionDeniedError: If user lacks permission
        """
        # Get document with permission check
        documento = self.document_repository.get_by_id(document_id)
        
        if not documento:
            raise DocumentNotFoundError(f"Document with ID {document_id} not found")
        
        # Check if user has permission to edit
        if not self._has_permission(documento, user_id, 'editar'):
            raise PermissionDeniedError("You don't have permission to edit this document")
        
        # Update fields if provided
        if nome is not None:
            documento.nome = nome
        if descricao is not None:
            documento.descricao = descricao
        if categoria_id is not None:
            documento.categoria_id = categoria_id
        if pasta_id is not None:
            documento.pasta_id = pasta_id
        
        documento.data_modificacao = datetime.utcnow()
        
        # Update tags if provided
        if tags is not None:
            # Remove existing tag associations
            db.session.query(DocumentoTag).filter_by(documento_id=documento.id).delete()
            db.session.commit()
            
            # Add new tags
            self._associate_tags(documento, tags)
        
        db.session.commit()
        
        # Log update
        self._log_access(documento, user_id, 'update_metadata')
        
        return documento
    
    def delete_document(self, document_id: int, user_id: int) -> Documento:
        """
        Soft delete a document (move to trash)
        
        Args:
            document_id: Document ID
            user_id: ID of user deleting the document
            
        Returns:
            Deleted Documento instance
            
        Raises:
            DocumentNotFoundError: If document not found
            PermissionDeniedError: If user lacks permission
        """
        # Get document
        documento = self.document_repository.get_by_id(document_id)
        
        if not documento:
            raise DocumentNotFoundError(f"Document with ID {document_id} not found")
        
        # Check if user has permission to delete
        if not self._has_permission(documento, user_id, 'excluir'):
            raise PermissionDeniedError("You don't have permission to delete this document")
        
        # Perform soft delete
        documento.soft_delete()
        
        # Log deletion
        self._log_access(documento, user_id, 'soft_delete')
        
        return documento
    
    def restore_document(self, document_id: int, user_id: int) -> Documento:
        """
        Restore a document from trash
        
        Args:
            document_id: Document ID
            user_id: ID of user restoring the document
            
        Returns:
            Restored Documento instance
            
        Raises:
            DocumentNotFoundError: If document not found
            PermissionDeniedError: If user lacks permission
        """
        # Get document
        documento = self.document_repository.get_by_id(document_id)
        
        if not documento:
            raise DocumentNotFoundError(f"Document with ID {document_id} not found")
        
        # Only owner can restore
        if documento.usuario_id != user_id:
            raise PermissionDeniedError("Only the document owner can restore it")
        
        # Check if document is actually deleted
        if documento.status != 'excluido':
            raise DocumentServiceError("Document is not in trash")
        
        # Restore document
        documento.restore()
        
        # Log restoration
        self._log_access(documento, user_id, 'restore')
        
        return documento
    
    def permanent_delete_document(self, document_id: int, user_id: int) -> bool:
        """
        Permanently delete a document and its file
        
        Args:
            document_id: Document ID
            user_id: ID of user permanently deleting the document
            
        Returns:
            True if deleted successfully
            
        Raises:
            DocumentNotFoundError: If document not found
            PermissionDeniedError: If user lacks permission
        """
        # Get document
        documento = self.document_repository.get_by_id(document_id)
        
        if not documento:
            raise DocumentNotFoundError(f"Document with ID {document_id} not found")
        
        # Only owner can permanently delete
        if documento.usuario_id != user_id:
            raise PermissionDeniedError("Only the document owner can permanently delete it")
        
        # Log before deletion
        self._log_access(documento, user_id, 'permanent_delete')
        
        # Delete all version files
        for versao in documento.versoes:
            self.storage_service.delete_file(versao.caminho_arquivo)
        
        # Delete main file
        self.storage_service.delete_file(documento.caminho_arquivo)
        
        # Delete database record (cascade will handle related records)
        self.document_repository.permanent_delete(document_id)
        
        return True
    
    def cleanup_expired_trash(self, days: int = 30) -> int:
        """
        Permanently delete documents that have been in trash for more than specified days
        
        Args:
            days: Number of days after which to permanently delete
            
        Returns:
            Number of documents permanently deleted
        """
        expired_docs = self.document_repository.get_expired_trash(days)
        count = 0
        
        for documento in expired_docs:
            try:
                # Delete all version files
                for versao in documento.versoes:
                    self.storage_service.delete_file(versao.caminho_arquivo)
                
                # Delete main file
                self.storage_service.delete_file(documento.caminho_arquivo)
                
                # Delete database record
                self.document_repository.permanent_delete(documento.id)
                count += 1
            except Exception as e:
                # Log error but continue with other documents
                print(f"Error permanently deleting document {documento.id}: {e}")
        
        return count

    def create_version(
        self,
        document_id: int,
        file: FileStorage,
        user_id: int,
        comentario: str
    ) -> Versao:
        """
        Create a new version of a document
        
        Args:
            document_id: Document ID
            file: New version file
            user_id: ID of user creating the version
            comentario: Comment describing the changes
            
        Returns:
            Created Versao instance
            
        Raises:
            DocumentNotFoundError: If document not found
            PermissionDeniedError: If user lacks permission
            VersionLimitExceededError: If version limit is exceeded
            FileValidationError: If file validation fails
        """
        # Get document
        documento = self.document_repository.get_by_id(document_id)
        
        if not documento:
            raise DocumentNotFoundError(f"Document with ID {document_id} not found")
        
        # Check if user has permission to edit
        if not self._has_permission(documento, user_id, 'editar'):
            raise PermissionDeniedError("You don't have permission to create a new version")
        
        # Check version limit (max 10 versions)
        version_count = documento.versoes.count()
        if version_count >= 10:
            raise VersionLimitExceededError(
                "Maximum version limit (10) reached. Please delete old versions first."
            )
        
        # Validate file
        validation_result = self.file_handler.validate_file(file.stream, file.filename)
        
        # Verify file type matches original document
        if validation_result['mime_type'] != documento.tipo_mime:
            raise FileValidationError(
                f"New version must be same file type as original. "
                f"Expected: {documento.tipo_mime}, Got: {validation_result['mime_type']}"
            )
        
        # Save file to storage
        storage_result = self.storage_service.save_file(
            file.stream,
            file.filename,
            user_id
        )
        
        # Increment version number
        new_version_number = documento.versao_atual + 1
        
        # Create version record
        versao = self._create_version_record(
            documento=documento,
            user_id=user_id,
            caminho_arquivo=storage_result['file_path'],
            tamanho_bytes=validation_result['file_size'],
            comentario=comentario
        )
        
        # Update document with new version info
        documento.versao_atual = new_version_number
        documento.caminho_arquivo = storage_result['file_path']
        documento.tamanho_bytes = validation_result['file_size']
        documento.hash_arquivo = validation_result['file_hash']
        documento.data_modificacao = datetime.utcnow()
        
        db.session.commit()
        
        # Log version creation
        self._log_access(documento, user_id, 'create_version')
        
        return versao
    
    def get_version_history(self, document_id: int, user_id: int) -> List[Versao]:
        """
        Get version history for a document
        
        Args:
            document_id: Document ID
            user_id: ID of user requesting version history
            
        Returns:
            List of Versao instances ordered by version number descending
            
        Raises:
            DocumentNotFoundError: If document not found
            PermissionDeniedError: If user lacks permission
        """
        # Get document with permission check
        documento = self.get_document(document_id, user_id)
        
        # Get all versions ordered by version number descending
        versoes = documento.versoes.order_by(Versao.numero_versao.desc()).all()
        
        return versoes
    
    def restore_version(
        self,
        document_id: int,
        version_number: int,
        user_id: int
    ) -> Documento:
        """
        Restore a previous version of a document
        
        Args:
            document_id: Document ID
            version_number: Version number to restore
            user_id: ID of user restoring the version
            
        Returns:
            Updated Documento instance
            
        Raises:
            DocumentNotFoundError: If document or version not found
            PermissionDeniedError: If user lacks permission
            VersionLimitExceededError: If version limit would be exceeded
        """
        # Get document
        documento = self.document_repository.get_by_id(document_id)
        
        if not documento:
            raise DocumentNotFoundError(f"Document with ID {document_id} not found")
        
        # Check if user has permission to edit
        if not self._has_permission(documento, user_id, 'editar'):
            raise PermissionDeniedError("You don't have permission to restore versions")
        
        # Get the version to restore
        versao = db.session.query(Versao).filter_by(
            documento_id=document_id,
            numero_versao=version_number
        ).first()
        
        if not versao:
            raise DocumentNotFoundError(
                f"Version {version_number} not found for document {document_id}"
            )
        
        # Check if we can create a new version (limit check)
        version_count = documento.versoes.count()
        if version_count >= 10:
            raise VersionLimitExceededError(
                "Maximum version limit (10) reached. Cannot restore version."
            )
        
        # Create a new version with the restored content
        new_version_number = documento.versao_atual + 1
        
        # Create version record pointing to the same file as the restored version
        new_versao = Versao(
            documento_id=documento.id,
            numero_versao=new_version_number,
            caminho_arquivo=versao.caminho_arquivo,
            tamanho_bytes=versao.tamanho_bytes,
            usuario_id=user_id,
            comentario=f"Restored from version {version_number}"
        )
        db.session.add(new_versao)
        
        # Update document to point to restored version
        documento.versao_atual = new_version_number
        documento.caminho_arquivo = versao.caminho_arquivo
        documento.tamanho_bytes = versao.tamanho_bytes
        documento.data_modificacao = datetime.utcnow()
        
        db.session.commit()
        
        # Log version restoration
        self._log_access(documento, user_id, f'restore_version_{version_number}')
        
        return documento
    
    def get_document_tags(self, document_id: int, user_id: int) -> List[str]:
        """
        Get tags for a document
        
        Args:
            document_id: Document ID
            user_id: ID of user requesting tags
            
        Returns:
            List of tag names
            
        Raises:
            DocumentNotFoundError: If document not found
            PermissionDeniedError: If user lacks permission
        """
        # Get document with permission check
        documento = self.get_document(document_id, user_id)
        
        # Get tag names
        tag_associations = db.session.query(DocumentoTag, Tag).join(
            Tag, DocumentoTag.tag_id == Tag.id
        ).filter(
            DocumentoTag.documento_id == document_id
        ).all()
        
        return [tag.nome for _, tag in tag_associations]
    
    def search_documents(
        self,
        query: str,
        user_id: int,
        filters: Optional[Dict[str, Any]] = None,
        include_shared: bool = True
    ) -> List[Documento]:
        """
        Search documents accessible by user
        
        Args:
            query: Search term
            user_id: User ID
            filters: Optional filters (categoria_id, tipo_mime, date ranges, etc.)
            include_shared: Whether to include documents shared with user
            
        Returns:
            List of matching Documento instances
        """
        if include_shared:
            return self.document_repository.search_with_permissions(query, user_id, filters)
        else:
            return self.document_repository.search(query, user_id, filters)
