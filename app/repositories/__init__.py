"""
Repository layer for data access
"""
from app.repositories.base_repository import BaseRepository
from app.repositories.user_repository import UserRepository, PerfilRepository, PasswordResetRepository
from app.repositories.document_repository import DocumentRepository, TagRepository
from app.repositories.category_repository import CategoryRepository, FolderRepository
from app.repositories.audit_repository import AuditRepository
from app.repositories.permission_repository import PermissionRepository
from app.repositories.workflow_repository import WorkflowRepository, AprovacaoDocumentoRepository, HistoricoAprovacaoRepository

__all__ = [
    'BaseRepository',
    'UserRepository',
    'PerfilRepository',
    'PasswordResetRepository',
    'DocumentRepository',
    'TagRepository',
    'CategoryRepository',
    'FolderRepository',
    'AuditRepository',
    'PermissionRepository',
    'WorkflowRepository',
    'AprovacaoDocumentoRepository',
    'HistoricoAprovacaoRepository'
]
