"""
Notification service for sending email notifications
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from flask import current_app, render_template, url_for
from flask_mail import Message
from app import mail, db
from app.models.document import Documento
from app.models.user import User
from app.models.workflow import Workflow, AprovacaoDocumento
import threading
from queue import Queue


class NotificationServiceError(Exception):
    """Base exception for notification service errors"""
    pass


class NotificationQueue:
    """Simple in-memory notification queue for async email sending"""
    
    def __init__(self):
        self.queue = Queue()
        self.worker_thread = None
        self.running = False
    
    def start(self):
        """Start the notification worker thread"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.worker_thread.start()
    
    def stop(self):
        """Stop the notification worker thread"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def enqueue(self, notification_func, *args, **kwargs):
        """Add a notification to the queue"""
        self.queue.put((notification_func, args, kwargs))
    
    def _process_queue(self):
        """Process notifications from the queue"""
        while self.running:
            try:
                if not self.queue.empty():
                    notification_func, args, kwargs = self.queue.get(timeout=1)
                    try:
                        notification_func(*args, **kwargs)
                    except Exception as e:
                        current_app.logger.error(f"Error processing notification: {e}")
                    finally:
                        self.queue.task_done()
            except Exception:
                pass


# Global notification queue instance
notification_queue = NotificationQueue()


class NotificationService:
    """Service for sending notifications"""
    
    def __init__(self):
        """Initialize notification service"""
        # Start the notification queue if not already running
        if not notification_queue.running:
            notification_queue.start()
    
    def notify_share(
        self,
        documento: Documento,
        from_user_id: int,
        to_user_id: int,
        permission_types: List[str],
        expiration_date: Optional[datetime] = None
    ) -> bool:
        """
        Send notification when document is shared
        
        Args:
            documento: Document being shared
            from_user_id: ID of user sharing the document
            to_user_id: ID of user receiving the share
            permission_types: List of permission types granted
            expiration_date: Optional expiration date
            
        Returns:
            True if notification queued successfully
            
        Requirements: 12.4
        """
        try:
            # Get users
            from_user = db.session.query(User).filter_by(id=from_user_id).first()
            to_user = db.session.query(User).filter_by(id=to_user_id).first()
            
            if not from_user or not to_user:
                return False
            
            # Format permission types for display
            permission_display = {
                'visualizar': 'Visualizar',
                'editar': 'Editar',
                'excluir': 'Excluir',
                'compartilhar': 'Compartilhar'
            }
            permissions_text = ', '.join([permission_display.get(p, p) for p in permission_types])
            
            # Format expiration date
            expiration_text = None
            if expiration_date:
                expiration_text = expiration_date.strftime('%d/%m/%Y')
            
            # Generate document URL
            document_url = url_for('documents.view', id=documento.id, _external=True)
            
            # Prepare template context
            context = {
                'recipient_name': to_user.nome,
                'sender_name': from_user.nome,
                'document_name': documento.nome,
                'document_description': documento.descricao,
                'permissions': permissions_text,
                'expiration_date': expiration_text,
                'document_url': document_url
            }
            
            # Queue email for sending
            notification_queue.enqueue(
                self._send_template_email,
                to_user.email,
                f"Documento Compartilhado: {documento.nome}",
                'emails/document_shared.html',
                context
            )
            
            current_app.logger.info(
                f"Share notification queued: {from_user.email} -> {to_user.email} "
                f"for document {documento.id}"
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error queueing share notification: {e}")
            return False
    
    def notify_upload(
        self,
        documento: Documento,
        user_id: int
    ) -> bool:
        """
        Send notification when document is uploaded
        
        Args:
            documento: Document that was uploaded
            user_id: ID of user who uploaded the document
            
        Returns:
            True if notification queued successfully
            
        Requirements: 12.4
        """
        try:
            user = db.session.query(User).filter_by(id=user_id).first()
            if not user:
                return False
            
            # Get category name
            category_name = documento.categoria.nome if documento.categoria else 'Sem categoria'
            
            # Format file size
            file_size = self._format_file_size(documento.tamanho_bytes)
            
            # Format upload date
            upload_date = documento.data_upload.strftime('%d/%m/%Y %H:%M')
            
            # Generate document URL
            document_url = url_for('documents.view', id=documento.id, _external=True)
            
            # Prepare template context
            context = {
                'user_name': user.nome,
                'document_name': documento.nome,
                'document_description': documento.descricao,
                'category_name': category_name,
                'file_size': file_size,
                'upload_date': upload_date,
                'document_url': document_url
            }
            
            # Queue email for sending
            notification_queue.enqueue(
                self._send_template_email,
                user.email,
                f"Documento Enviado: {documento.nome}",
                'emails/document_upload.html',
                context
            )
            
            current_app.logger.info(
                f"Upload notification queued: {user.email} uploaded document {documento.id}"
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error queueing upload notification: {e}")
            return False
    
    def notify_workflow_submission(
        self,
        documento: Documento,
        approver_id: int,
        workflow_id: int,
        submitter_id: int
    ) -> bool:
        """
        Send notification for workflow approval request
        
        Args:
            documento: Document submitted for approval
            approver_id: ID of user who needs to approve
            workflow_id: ID of the workflow
            submitter_id: ID of user who submitted the document
            
        Returns:
            True if notification queued successfully
            
        Requirements: 7.2
        """
        try:
            approver = db.session.query(User).filter_by(id=approver_id).first()
            submitter = db.session.query(User).filter_by(id=submitter_id).first()
            workflow = db.session.query(Workflow).filter_by(id=workflow_id).first()
            
            if not approver or not submitter or not workflow:
                return False
            
            # Get approval record to determine stage
            aprovacao = db.session.query(AprovacaoDocumento).filter_by(
                documento_id=documento.id,
                workflow_id=workflow_id
            ).order_by(AprovacaoDocumento.data_submissao.desc()).first()
            
            stage_name = f"Etapa {aprovacao.etapa_atual}" if aprovacao else "Etapa 1"
            submission_date = aprovacao.data_submissao.strftime('%d/%m/%Y %H:%M') if aprovacao else datetime.now().strftime('%d/%m/%Y %H:%M')
            
            # Generate approval URL
            approval_url = url_for('workflow.approvals', _external=True)
            
            # Prepare template context
            context = {
                'approver_name': approver.nome,
                'submitter_name': submitter.nome,
                'document_name': documento.nome,
                'document_description': documento.descricao,
                'workflow_name': workflow.nome,
                'stage_name': stage_name,
                'submission_date': submission_date,
                'approval_url': approval_url
            }
            
            # Queue email for sending
            notification_queue.enqueue(
                self._send_template_email,
                approver.email,
                f"Solicitação de Aprovação: {documento.nome}",
                'emails/workflow_submission.html',
                context
            )
            
            current_app.logger.info(
                f"Workflow notification queued: approval request sent to {approver.email} "
                f"for document {documento.id}"
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error queueing workflow notification: {e}")
            return False
    
    def notify_workflow_approved(
        self,
        documento: Documento,
        approver_id: int,
        submitter_id: int,
        workflow_id: int,
        comment: Optional[str] = None
    ) -> bool:
        """
        Send notification when document is approved
        
        Args:
            documento: Document that was approved
            approver_id: ID of user who approved
            submitter_id: ID of user who submitted the document
            workflow_id: ID of the workflow
            comment: Optional approval comment
            
        Returns:
            True if notification queued successfully
            
        Requirements: 7.2
        """
        try:
            approver = db.session.query(User).filter_by(id=approver_id).first()
            submitter = db.session.query(User).filter_by(id=submitter_id).first()
            workflow = db.session.query(Workflow).filter_by(id=workflow_id).first()
            
            if not approver or not submitter or not workflow:
                return False
            
            # Generate document URL
            document_url = url_for('documents.view', id=documento.id, _external=True)
            
            # Prepare template context
            context = {
                'submitter_name': submitter.nome,
                'approver_name': approver.nome,
                'document_name': documento.nome,
                'workflow_name': workflow.nome,
                'approval_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'comment': comment,
                'document_url': document_url
            }
            
            # Queue email for sending
            notification_queue.enqueue(
                self._send_template_email,
                submitter.email,
                f"Documento Aprovado: {documento.nome}",
                'emails/workflow_approved.html',
                context
            )
            
            current_app.logger.info(
                f"Approval notification queued: document {documento.id} approved by {approver.email}"
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error queueing approval notification: {e}")
            return False
    
    def notify_workflow_rejected(
        self,
        documento: Documento,
        approver_id: int,
        submitter_id: int,
        workflow_id: int,
        comment: Optional[str] = None
    ) -> bool:
        """
        Send notification when document is rejected
        
        Args:
            documento: Document that was rejected
            approver_id: ID of user who rejected
            submitter_id: ID of user who submitted the document
            workflow_id: ID of the workflow
            comment: Optional rejection comment
            
        Returns:
            True if notification queued successfully
            
        Requirements: 7.2
        """
        try:
            approver = db.session.query(User).filter_by(id=approver_id).first()
            submitter = db.session.query(User).filter_by(id=submitter_id).first()
            workflow = db.session.query(Workflow).filter_by(id=workflow_id).first()
            
            if not approver or not submitter or not workflow:
                return False
            
            # Generate document URL
            document_url = url_for('documents.view', id=documento.id, _external=True)
            
            # Prepare template context
            context = {
                'submitter_name': submitter.nome,
                'approver_name': approver.nome,
                'document_name': documento.nome,
                'workflow_name': workflow.nome,
                'rejection_date': datetime.now().strftime('%d/%m/%Y %H:%M'),
                'comment': comment,
                'document_url': document_url
            }
            
            # Queue email for sending
            notification_queue.enqueue(
                self._send_template_email,
                submitter.email,
                f"Documento Rejeitado: {documento.nome}",
                'emails/workflow_rejected.html',
                context
            )
            
            current_app.logger.info(
                f"Rejection notification queued: document {documento.id} rejected by {approver.email}"
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error queueing rejection notification: {e}")
            return False
    
    def send_password_reset_email(
        self,
        user: User,
        token: str
    ) -> bool:
        """
        Send password reset email with token
        
        Args:
            user: User requesting password reset
            token: Password reset token
            
        Returns:
            True if email queued successfully
            
        Requirements: 1.3
        """
        try:
            # Generate reset URL
            reset_url = url_for('auth.reset_password', token=token, _external=True)
            
            # Prepare template context
            context = {
                'user_name': user.nome,
                'reset_url': reset_url
            }
            
            # Queue email for sending
            notification_queue.enqueue(
                self._send_template_email,
                user.email,
                "Recuperação de Senha - SGDI",
                'emails/password_reset.html',
                context
            )
            
            current_app.logger.info(f"Password reset email queued for {user.email}")
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error queueing password reset email: {e}")
            return False
    
    def send_email(
        self,
        to: str,
        subject: str,
        body: str,
        html_body: Optional[str] = None
    ) -> bool:
        """
        Generic email sending method (synchronous)
        
        Args:
            to: Recipient email address
            subject: Email subject
            body: Plain text email body
            html_body: Optional HTML email body
            
        Returns:
            True if email sent successfully
        """
        try:
            msg = Message(
                subject=subject,
                recipients=[to],
                body=body,
                html=html_body,
                sender=current_app.config['MAIL_DEFAULT_SENDER']
            )
            
            mail.send(msg)
            current_app.logger.info(f"Email sent to {to}: {subject}")
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error sending email to {to}: {e}")
            return False
    
    def _send_template_email(
        self,
        to: str,
        subject: str,
        template: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Send email using HTML template (internal method for queue processing)
        
        Args:
            to: Recipient email address
            subject: Email subject
            template: Template path relative to templates directory
            context: Template context variables
            
        Returns:
            True if email sent successfully
        """
        try:
            # Render HTML template
            html_body = render_template(template, **context)
            
            # Create plain text version (simple strip of HTML tags)
            import re
            text_body = re.sub('<[^<]+?>', '', html_body)
            
            # Send email
            return self.send_email(to, subject, text_body, html_body)
            
        except Exception as e:
            current_app.logger.error(f"Error sending template email to {to}: {e}")
            return False
    
    def _format_file_size(self, size_bytes: int) -> str:
        """
        Format file size in human-readable format
        
        Args:
            size_bytes: File size in bytes
            
        Returns:
            Formatted file size string
        """
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
