"""
Domain models for SGDI
"""
from app.models.user import User, Perfil, PasswordReset
from app.models.document import Documento, Categoria, Pasta, Tag, DocumentoTag
from app.models.version import Versao
from app.models.permission import Permissao
from app.models.workflow import Workflow, AprovacaoDocumento, HistoricoAprovacao
from app.models.audit import LogAuditoria
from app.models.settings import SystemSettings

__all__ = [
    'User',
    'Perfil',
    'PasswordReset',
    'Documento',
    'Categoria',
    'Pasta',
    'Tag',
    'DocumentoTag',
    'Versao',
    'Permissao',
    'Workflow',
    'AprovacaoDocumento',
    'HistoricoAprovacao',
    'LogAuditoria',
    'SystemSettings'
]
