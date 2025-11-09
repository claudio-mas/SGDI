"""
Workflow service for approval processes
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from flask import current_app
from app import db
from app.models.workflow import Workflow, AprovacaoDocumento, HistoricoAprovacao
from app.models.document import Documento
from app.models.user import User
from app.repositories.workflow_repository import (
    WorkflowRepository,
    AprovacaoDocumentoRepository,
    HistoricoAprovacaoRepository
)
from app.services.notification_service import NotificationService


class WorkflowServiceError(Exception):
    """Base exception for workflow service errors"""
    pass


class WorkflowNotFoundError(WorkflowServiceError):
    """Raised when workflow is not found"""
    pass


class ApprovalNotFoundError(WorkflowServiceError):
    """Raised when approval is not found"""
    pass


class InvalidWorkflowConfigError(WorkflowServiceError):
    """Raised when workflow configuration is invalid"""
    pass


class UnauthorizedApproverError(WorkflowServiceError):
    """Raised when user is not authorized to approve"""
    pass


class WorkflowService:
    """Service for managing document approval workflows"""
    
    def __init__(self):
        """Initialize workflow service"""
        self.workflow_repo = WorkflowRepository()
        self.aprovacao_repo = AprovacaoDocumentoRepository()
        self.historico_repo = HistoricoAprovacaoRepository()
        self.notification_service = NotificationService()
    
    def create_workflow(
        self,
        nome: str,
        descricao: str,
        configuracao: Dict[str, Any],
        criado_por: int
    ) -> Workflow:
        """
        Create a new workflow template
        
        Args:
            nome: Workflow name
            descricao: Workflow description
            configuracao: Workflow configuration as dict with structure:
                {
                    "stages": [
                        {
                            "name": "Stage 1",
                            "approvers": [user_id1, user_id2],
                            "require_all": False  # If True, all approvers must approve
                        },
                        ...
                    ]
                }
            criado_por: ID of user creating the workflow
            
        Returns:
            Created Workflow instance
            
        Raises:
            InvalidWorkflowConfigError: If configuration is invalid
        """
        try:
            # Validate configuration
            self._validate_workflow_config(configuracao)
            
            # Check if workflow with same name exists
            existing = self.workflow_repo.get_by_name(nome)
            if existing:
                raise WorkflowServiceError(f"Workflow with name '{nome}' already exists")
            
            # Create workflow
            workflow = Workflow(
                nome=nome,
                descricao=descricao,
                criado_por=criado_por,
                ativo=True
            )
            workflow.configuracao = configuracao
            
            db.session.add(workflow)
            db.session.commit()
            
            current_app.logger.info(
                f"Workflow created: {workflow.id} by user {criado_por}"
            )
            
            return workflow
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error creating workflow: {e}")
            raise
    
    def update_workflow(
        self,
        workflow_id: int,
        nome: Optional[str] = None,
        descricao: Optional[str] = None,
        configuracao: Optional[Dict[str, Any]] = None,
        ativo: Optional[bool] = None
    ) -> Workflow:
        """
        Update an existing workflow template
        
        Args:
            workflow_id: Workflow ID
            nome: New workflow name (optional)
            descricao: New description (optional)
            configuracao: New configuration (optional)
            ativo: Active status (optional)
            
        Returns:
            Updated Workflow instance
            
        Raises:
            WorkflowNotFoundError: If workflow not found
            InvalidWorkflowConfigError: If configuration is invalid
        """
        try:
            workflow = self.workflow_repo.get_by_id(workflow_id)
            if not workflow:
                raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")
            
            # Update fields
            if nome is not None:
                workflow.nome = nome
            if descricao is not None:
                workflow.descricao = descricao
            if configuracao is not None:
                self._validate_workflow_config(configuracao)
                workflow.configuracao = configuracao
            if ativo is not None:
                workflow.ativo = ativo
            
            db.session.commit()
            
            current_app.logger.info(f"Workflow updated: {workflow_id}")
            
            return workflow
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating workflow: {e}")
            raise
    
    def get_workflow(self, workflow_id: int) -> Workflow:
        """
        Get workflow by ID
        
        Args:
            workflow_id: Workflow ID
            
        Returns:
            Workflow instance
            
        Raises:
            WorkflowNotFoundError: If workflow not found
        """
        workflow = self.workflow_repo.get_by_id(workflow_id)
        if not workflow:
            raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")
        return workflow
    
    def get_active_workflows(self) -> List[Workflow]:
        """
        Get all active workflows
        
        Returns:
            List of active Workflow instances
        """
        return self.workflow_repo.get_active_workflows()
    
    def submit_for_approval(
        self,
        documento_id: int,
        workflow_id: int,
        submetido_por: int
    ) -> AprovacaoDocumento:
        """
        Submit a document for approval workflow
        
        Args:
            documento_id: Document ID
            workflow_id: Workflow ID to use
            submetido_por: ID of user submitting the document
            
        Returns:
            Created AprovacaoDocumento instance
            
        Raises:
            WorkflowNotFoundError: If workflow not found
            WorkflowServiceError: If document or user not found
        """
        try:
            # Validate workflow exists and is active
            workflow = self.workflow_repo.get_by_id(workflow_id)
            if not workflow:
                raise WorkflowNotFoundError(f"Workflow {workflow_id} not found")
            if not workflow.ativo:
                raise WorkflowServiceError(f"Workflow {workflow_id} is not active")
            
            # Validate document exists
            documento = db.session.query(Documento).filter_by(id=documento_id).first()
            if not documento:
                raise WorkflowServiceError(f"Document {documento_id} not found")
            
            # Check if document already has pending approval
            pending = self.aprovacao_repo.get_pending_approvals(documento_id)
            if pending:
                raise WorkflowServiceError(
                    f"Document {documento_id} already has pending approval"
                )
            
            # Create approval instance
            aprovacao = AprovacaoDocumento(
                documento_id=documento_id,
                workflow_id=workflow_id,
                submetido_por=submetido_por,
                estagio_atual=1,
                status='pendente'
            )
            
            db.session.add(aprovacao)
            db.session.commit()
            
            # Send notifications to first stage approvers
            self._notify_stage_approvers(aprovacao)
            
            current_app.logger.info(
                f"Document {documento_id} submitted for approval by user {submetido_por}"
            )
            
            return aprovacao
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error submitting document for approval: {e}")
            raise
    
    def approve_document(
        self,
        aprovacao_id: int,
        aprovador_id: int,
        comentario: str
    ) -> AprovacaoDocumento:
        """
        Approve a document at current workflow stage
        
        Args:
            aprovacao_id: Approval ID
            aprovador_id: ID of user approving
            comentario: Approval comment (mandatory)
            
        Returns:
            Updated AprovacaoDocumento instance
            
        Raises:
            ApprovalNotFoundError: If approval not found
            UnauthorizedApproverError: If user not authorized to approve
            WorkflowServiceError: If approval is not pending
        """
        try:
            # Get approval
            aprovacao = self.aprovacao_repo.get_by_id(aprovacao_id)
            if not aprovacao:
                raise ApprovalNotFoundError(f"Approval {aprovacao_id} not found")
            
            if aprovacao.status != 'pendente':
                raise WorkflowServiceError(
                    f"Approval {aprovacao_id} is not pending (status: {aprovacao.status})"
                )
            
            # Validate user is authorized approver for current stage
            if not self._is_authorized_approver(aprovacao, aprovador_id):
                raise UnauthorizedApproverError(
                    f"User {aprovador_id} is not authorized to approve at current stage"
                )
            
            # Record approval in history
            historico = HistoricoAprovacao(
                aprovacao_id=aprovacao_id,
                estagio=aprovacao.estagio_atual,
                aprovador_id=aprovador_id,
                acao='aprovado',
                comentario=comentario
            )
            db.session.add(historico)
            
            # Check if stage is complete
            if self._is_stage_complete(aprovacao, 'aprovado'):
                # Move to next stage or complete workflow
                workflow = aprovacao.workflow
                config = workflow.configuracao
                total_stages = len(config.get('stages', []))
                
                if aprovacao.estagio_atual < total_stages:
                    # Move to next stage
                    aprovacao.estagio_atual += 1
                    db.session.commit()
                    
                    # Notify next stage approvers
                    self._notify_stage_approvers(aprovacao)
                    
                    current_app.logger.info(
                        f"Approval {aprovacao_id} moved to stage {aprovacao.estagio_atual}"
                    )
                else:
                    # Workflow complete - approve document
                    aprovacao.status = 'aprovado'
                    aprovacao.data_conclusao = datetime.utcnow()
                    db.session.commit()
                    
                    # Notify submitter
                    self._notify_approval_complete(aprovacao, 'aprovado')
                    
                    current_app.logger.info(
                        f"Approval {aprovacao_id} completed - document approved"
                    )
            else:
                db.session.commit()
                current_app.logger.info(
                    f"Approval recorded for {aprovacao_id} by user {aprovador_id}"
                )
            
            # Log workflow approval
            try:
                from app.services.audit_service import AuditService
                audit_service = AuditService()
                audit_service.log_workflow_action(
                    usuario_id=aprovador_id,
                    documento_id=aprovacao.documento_id,
                    acao='approve',
                    workflow_id=aprovacao.workflow_id,
                    comentario=comentario
                )
            except Exception as e:
                print(f"Warning: Failed to log workflow approval audit entry: {e}")
            
            return aprovacao
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error approving document: {e}")
            raise
    
    def reject_document(
        self,
        aprovacao_id: int,
        aprovador_id: int,
        comentario: str
    ) -> AprovacaoDocumento:
        """
        Reject a document at current workflow stage
        
        Args:
            aprovacao_id: Approval ID
            aprovador_id: ID of user rejecting
            comentario: Rejection comment (mandatory)
            
        Returns:
            Updated AprovacaoDocumento instance
            
        Raises:
            ApprovalNotFoundError: If approval not found
            UnauthorizedApproverError: If user not authorized to reject
            WorkflowServiceError: If approval is not pending or comment is empty
        """
        try:
            if not comentario or not comentario.strip():
                raise WorkflowServiceError("Rejection comment is mandatory")
            
            # Get approval
            aprovacao = self.aprovacao_repo.get_by_id(aprovacao_id)
            if not aprovacao:
                raise ApprovalNotFoundError(f"Approval {aprovacao_id} not found")
            
            if aprovacao.status != 'pendente':
                raise WorkflowServiceError(
                    f"Approval {aprovacao_id} is not pending (status: {aprovacao.status})"
                )
            
            # Validate user is authorized approver for current stage
            if not self._is_authorized_approver(aprovacao, aprovador_id):
                raise UnauthorizedApproverError(
                    f"User {aprovador_id} is not authorized to reject at current stage"
                )
            
            # Record rejection in history
            historico = HistoricoAprovacao(
                aprovacao_id=aprovacao_id,
                estagio=aprovacao.estagio_atual,
                aprovador_id=aprovador_id,
                acao='rejeitado',
                comentario=comentario
            )
            db.session.add(historico)
            
            # Reject the approval (one rejection ends the workflow)
            aprovacao.status = 'rejeitado'
            aprovacao.data_conclusao = datetime.utcnow()
            
            db.session.commit()
            
            # Notify submitter
            self._notify_approval_complete(aprovacao, 'rejeitado')
            
            current_app.logger.info(
                f"Approval {aprovacao_id} rejected by user {aprovador_id}"
            )
            
            # Log workflow rejection
            try:
                from app.services.audit_service import AuditService
                audit_service = AuditService()
                audit_service.log_workflow_action(
                    usuario_id=aprovador_id,
                    documento_id=aprovacao.documento_id,
                    acao='reject',
                    workflow_id=aprovacao.workflow_id,
                    comentario=comentario
                )
            except Exception as e:
                print(f"Warning: Failed to log workflow rejection audit entry: {e}")
            
            return aprovacao
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error rejecting document: {e}")
            raise
    
    def get_approval_history(self, aprovacao_id: int) -> List[HistoricoAprovacao]:
        """
        Get approval history for an approval
        
        Args:
            aprovacao_id: Approval ID
            
        Returns:
            List of HistoricoAprovacao instances ordered by date
        """
        return self.historico_repo.get_by_approval(aprovacao_id)
    
    def get_pending_approvals_for_user(self, user_id: int) -> List[AprovacaoDocumento]:
        """
        Get all pending approvals where user is an approver
        
        Args:
            user_id: User ID
            
        Returns:
            List of pending AprovacaoDocumento instances
        """
        return self.aprovacao_repo.get_pending_for_user(user_id)
    
    def get_document_approvals(self, documento_id: int) -> List[AprovacaoDocumento]:
        """
        Get all approvals for a document
        
        Args:
            documento_id: Document ID
            
        Returns:
            List of AprovacaoDocumento instances
        """
        return self.aprovacao_repo.get_by_document(documento_id)
    
    # Private helper methods
    
    def _validate_workflow_config(self, config: Dict[str, Any]) -> None:
        """
        Validate workflow configuration structure
        
        Args:
            config: Configuration dictionary
            
        Raises:
            InvalidWorkflowConfigError: If configuration is invalid
        """
        if not isinstance(config, dict):
            raise InvalidWorkflowConfigError("Configuration must be a dictionary")
        
        if 'stages' not in config:
            raise InvalidWorkflowConfigError("Configuration must contain 'stages' key")
        
        stages = config['stages']
        if not isinstance(stages, list) or len(stages) == 0:
            raise InvalidWorkflowConfigError("Stages must be a non-empty list")
        
        for i, stage in enumerate(stages):
            if not isinstance(stage, dict):
                raise InvalidWorkflowConfigError(f"Stage {i+1} must be a dictionary")
            
            if 'name' not in stage:
                raise InvalidWorkflowConfigError(f"Stage {i+1} must have a 'name'")
            
            if 'approvers' not in stage:
                raise InvalidWorkflowConfigError(f"Stage {i+1} must have 'approvers'")
            
            approvers = stage['approvers']
            if not isinstance(approvers, list) or len(approvers) == 0:
                raise InvalidWorkflowConfigError(
                    f"Stage {i+1} approvers must be a non-empty list"
                )
    
    def _is_authorized_approver(
        self,
        aprovacao: AprovacaoDocumento,
        user_id: int
    ) -> bool:
        """
        Check if user is authorized to approve at current stage
        
        Args:
            aprovacao: Approval instance
            user_id: User ID to check
            
        Returns:
            True if user is authorized approver
        """
        workflow = aprovacao.workflow
        config = workflow.configuracao
        
        if 'stages' not in config:
            return False
        
        stages = config['stages']
        current_stage_idx = aprovacao.estagio_atual - 1  # 0-indexed
        
        if current_stage_idx >= len(stages):
            return False
        
        stage = stages[current_stage_idx]
        approvers = stage.get('approvers', [])
        
        return user_id in approvers
    
    def _is_stage_complete(
        self,
        aprovacao: AprovacaoDocumento,
        acao: str
    ) -> bool:
        """
        Check if current stage is complete
        
        Args:
            aprovacao: Approval instance
            acao: Action taken ('aprovado' or 'rejeitado')
            
        Returns:
            True if stage is complete
        """
        # If rejected, stage is always complete (workflow ends)
        if acao == 'rejeitado':
            return True
        
        workflow = aprovacao.workflow
        config = workflow.configuracao
        stages = config.get('stages', [])
        current_stage_idx = aprovacao.estagio_atual - 1
        
        if current_stage_idx >= len(stages):
            return True
        
        stage = stages[current_stage_idx]
        require_all = stage.get('require_all', False)
        
        # If require_all is False, one approval completes the stage
        if not require_all:
            return True
        
        # If require_all is True, check if all approvers have approved
        approvers = stage.get('approvers', [])
        history = self.historico_repo.get_by_approval(aprovacao.id)
        
        # Get approvers who have approved at this stage
        approved_by = set()
        for h in history:
            if h.estagio == aprovacao.estagio_atual and h.acao == 'aprovado':
                approved_by.add(h.aprovador_id)
        
        # Check if all approvers have approved
        return len(approved_by) >= len(approvers)
    
    def _notify_stage_approvers(self, aprovacao: AprovacaoDocumento) -> None:
        """
        Send notifications to approvers of current stage
        
        Args:
            aprovacao: Approval instance
        """
        try:
            workflow = aprovacao.workflow
            config = workflow.configuracao
            stages = config.get('stages', [])
            current_stage_idx = aprovacao.estagio_atual - 1
            
            if current_stage_idx >= len(stages):
                return
            
            stage = stages[current_stage_idx]
            approvers = stage.get('approvers', [])
            
            documento = aprovacao.documento
            
            # Send notification to each approver
            for approver_id in approvers:
                self.notification_service.notify_workflow_submission(
                    documento=documento,
                    approver_id=approver_id,
                    workflow_id=workflow.id,
                    submitter_id=aprovacao.submetido_por
                )
                
        except Exception as e:
            current_app.logger.error(f"Error notifying stage approvers: {e}")
    
    def _notify_approval_complete(
        self,
        aprovacao: AprovacaoDocumento,
        status: str
    ) -> None:
        """
        Send notification when approval is complete
        
        Args:
            aprovacao: Approval instance
            status: Final status ('aprovado' or 'rejeitado')
        """
        try:
            # Get the last approver from history
            history = self.historico_repo.get_by_approval(aprovacao.id)
            if not history:
                return
            
            last_action = history[-1]  # Most recent action
            approver_id = last_action.aprovador_id
            comment = last_action.comentario
            
            documento = aprovacao.documento
            submitter_id = aprovacao.submetido_por
            workflow_id = aprovacao.workflow_id
            
            # Send appropriate notification based on status
            if status == 'aprovado':
                self.notification_service.notify_workflow_approved(
                    documento=documento,
                    approver_id=approver_id,
                    submitter_id=submitter_id,
                    workflow_id=workflow_id,
                    comment=comment
                )
            elif status == 'rejeitado':
                self.notification_service.notify_workflow_rejected(
                    documento=documento,
                    approver_id=approver_id,
                    submitter_id=submitter_id,
                    workflow_id=workflow_id,
                    comment=comment
                )
            
        except Exception as e:
            current_app.logger.error(f"Error notifying approval complete: {e}")
