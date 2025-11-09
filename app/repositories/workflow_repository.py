"""
Workflow repository for data access
"""
from typing import List, Optional
from app.repositories.base_repository import BaseRepository
from app.models.workflow import Workflow, AprovacaoDocumento, HistoricoAprovacao
from app import db


class WorkflowRepository(BaseRepository[Workflow]):
    """Repository for Workflow model"""
    
    def __init__(self):
        super().__init__(Workflow)
    
    def get_active_workflows(self) -> List[Workflow]:
        """
        Get all active workflows
        
        Returns:
            List of active workflow instances
        """
        return self.filter_by(ativo=True)
    
    def get_by_name(self, nome: str) -> Optional[Workflow]:
        """
        Get workflow by name
        
        Args:
            nome: Workflow name
            
        Returns:
            Workflow instance or None
        """
        return self.get_one_by(nome=nome)


class AprovacaoDocumentoRepository(BaseRepository[AprovacaoDocumento]):
    """Repository for AprovacaoDocumento model"""
    
    def __init__(self):
        super().__init__(AprovacaoDocumento)
    
    def get_by_document(self, documento_id: int) -> List[AprovacaoDocumento]:
        """
        Get all approvals for a document
        
        Args:
            documento_id: Document ID
            
        Returns:
            List of approval instances
        """
        return self.filter_by(documento_id=documento_id)
    
    def get_pending_approvals(self, documento_id: int) -> List[AprovacaoDocumento]:
        """
        Get pending approvals for a document
        
        Args:
            documento_id: Document ID
            
        Returns:
            List of pending approval instances
        """
        return self.session.query(self.model).filter_by(
            documento_id=documento_id,
            status='pendente'
        ).all()
    
    def get_pending_for_user(self, user_id: int) -> List[AprovacaoDocumento]:
        """
        Get all pending approvals where user is an approver
        
        Args:
            user_id: User ID
            
        Returns:
            List of pending approval instances
        """
        # Get all pending approvals and filter by current stage approvers
        pending = self.filter_by(status='pendente')
        result = []
        
        for aprovacao in pending:
            workflow = aprovacao.workflow
            config = workflow.configuracao
            
            # Check if user is an approver for current stage
            if 'stages' in config:
                current_stage = aprovacao.estagio_atual - 1  # 0-indexed
                if current_stage < len(config['stages']):
                    stage = config['stages'][current_stage]
                    if user_id in stage.get('approvers', []):
                        result.append(aprovacao)
        
        return result


class HistoricoAprovacaoRepository(BaseRepository[HistoricoAprovacao]):
    """Repository for HistoricoAprovacao model"""
    
    def __init__(self):
        super().__init__(HistoricoAprovacao)
    
    def get_by_approval(self, aprovacao_id: int) -> List[HistoricoAprovacao]:
        """
        Get history for an approval
        
        Args:
            aprovacao_id: Approval ID
            
        Returns:
            List of history records ordered by date
        """
        return self.session.query(self.model).filter_by(
            aprovacao_id=aprovacao_id
        ).order_by(self.model.data_acao).all()
