"""
Audit service for logging and tracking all system operations
Handles automatic logging of user actions, audit trail queries, and reporting
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from flask import request
from app import db
from app.models.audit import LogAuditoria
from app.repositories.audit_repository import AuditRepository


class AuditServiceError(Exception):
    """Base exception for audit service errors"""
    pass


class AuditService:
    """Service for audit logging and reporting operations"""
    
    def __init__(self, audit_repository: Optional[AuditRepository] = None):
        """
        Initialize audit service
        
        Args:
            audit_repository: Repository for audit data access
        """
        self.audit_repository = audit_repository or AuditRepository()
    
    def log_action(
        self,
        usuario_id: Optional[int],
        acao: str,
        tabela: Optional[str] = None,
        registro_id: Optional[int] = None,
        dados: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> LogAuditoria:
        """
        Log a user action to the audit trail
        
        Args:
            usuario_id: ID of user performing the action (None for anonymous actions)
            acao: Action being performed (login, upload, download, edit, delete, etc.)
            tabela: Table/entity affected by the action
            registro_id: ID of the affected record
            dados: Additional context data as dictionary
            ip_address: IP address of the user (auto-detected if not provided)
            user_agent: User agent string (auto-detected if not provided)
            
        Returns:
            Created LogAuditoria instance
            
        Example:
            audit_service.log_action(
                usuario_id=1,
                acao='upload',
                tabela='documentos',
                registro_id=123,
                dados={'nome': 'contract.pdf', 'tamanho': 1024000}
            )
        """
        # Auto-detect IP address and user agent from Flask request context if available
        if ip_address is None:
            try:
                ip_address = self._get_client_ip()
            except RuntimeError:
                # Not in request context
                ip_address = None
        
        if user_agent is None:
            try:
                user_agent = request.headers.get('User-Agent')
            except RuntimeError:
                # Not in request context
                user_agent = None
        
        # Create audit log entry
        log_entry = LogAuditoria(
            usuario_id=usuario_id,
            acao=acao,
            tabela=tabela,
            registro_id=registro_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        
        # Set additional data if provided
        if dados:
            log_entry.dados = dados
        
        # Save to database
        db.session.add(log_entry)
        db.session.commit()
        
        return log_entry
    
    def _get_client_ip(self) -> Optional[str]:
        """
        Get client IP address from request, handling proxies
        
        Returns:
            Client IP address or None
        """
        # Check for X-Forwarded-For header (proxy/load balancer)
        if request.headers.get('X-Forwarded-For'):
            # Get first IP in the chain
            return request.headers.get('X-Forwarded-For').split(',')[0].strip()
        
        # Check for X-Real-IP header
        if request.headers.get('X-Real-IP'):
            return request.headers.get('X-Real-IP')
        
        # Fall back to remote_addr
        return request.remote_addr
    
    def log_login(
        self,
        usuario_id: Optional[int],
        success: bool,
        email: Optional[str] = None,
        reason: Optional[str] = None
    ) -> LogAuditoria:
        """
        Log a login attempt
        
        Args:
            usuario_id: ID of user attempting login (None if user not found)
            success: Whether login was successful
            email: Email used for login attempt
            reason: Reason for failure (if applicable)
            
        Returns:
            Created LogAuditoria instance
        """
        acao = 'login' if success else 'login_failed'
        dados = {}
        
        if email:
            dados['email'] = email
        if reason:
            dados['reason'] = reason
        
        return self.log_action(
            usuario_id=usuario_id,
            acao=acao,
            tabela='usuarios',
            registro_id=usuario_id,
            dados=dados if dados else None
        )
    
    def log_logout(self, usuario_id: int) -> LogAuditoria:
        """
        Log a user logout
        
        Args:
            usuario_id: ID of user logging out
            
        Returns:
            Created LogAuditoria instance
        """
        return self.log_action(
            usuario_id=usuario_id,
            acao='logout',
            tabela='usuarios',
            registro_id=usuario_id
        )
    
    def log_document_upload(
        self,
        usuario_id: int,
        documento_id: int,
        nome: str,
        tamanho_bytes: int,
        tipo_mime: str
    ) -> LogAuditoria:
        """
        Log a document upload
        
        Args:
            usuario_id: ID of user uploading
            documento_id: ID of uploaded document
            nome: Document name
            tamanho_bytes: File size in bytes
            tipo_mime: MIME type
            
        Returns:
            Created LogAuditoria instance
        """
        return self.log_action(
            usuario_id=usuario_id,
            acao='upload',
            tabela='documentos',
            registro_id=documento_id,
            dados={
                'nome': nome,
                'tamanho_bytes': tamanho_bytes,
                'tipo_mime': tipo_mime
            }
        )
    
    def log_document_download(
        self,
        usuario_id: int,
        documento_id: int,
        nome: str
    ) -> LogAuditoria:
        """
        Log a document download
        
        Args:
            usuario_id: ID of user downloading
            documento_id: ID of downloaded document
            nome: Document name
            
        Returns:
            Created LogAuditoria instance
        """
        return self.log_action(
            usuario_id=usuario_id,
            acao='download',
            tabela='documentos',
            registro_id=documento_id,
            dados={'nome': nome}
        )
    
    def log_document_view(
        self,
        usuario_id: int,
        documento_id: int,
        nome: str
    ) -> LogAuditoria:
        """
        Log a document view/preview
        
        Args:
            usuario_id: ID of user viewing
            documento_id: ID of viewed document
            nome: Document name
            
        Returns:
            Created LogAuditoria instance
        """
        return self.log_action(
            usuario_id=usuario_id,
            acao='view',
            tabela='documentos',
            registro_id=documento_id,
            dados={'nome': nome}
        )
    
    def log_document_edit(
        self,
        usuario_id: int,
        documento_id: int,
        nome: str,
        changes: Optional[Dict[str, Any]] = None
    ) -> LogAuditoria:
        """
        Log a document metadata edit
        
        Args:
            usuario_id: ID of user editing
            documento_id: ID of edited document
            nome: Document name
            changes: Dictionary of changed fields
            
        Returns:
            Created LogAuditoria instance
        """
        dados = {'nome': nome}
        if changes:
            dados['changes'] = changes
        
        return self.log_action(
            usuario_id=usuario_id,
            acao='edit',
            tabela='documentos',
            registro_id=documento_id,
            dados=dados
        )
    
    def log_document_delete(
        self,
        usuario_id: int,
        documento_id: int,
        nome: str,
        permanent: bool = False
    ) -> LogAuditoria:
        """
        Log a document deletion
        
        Args:
            usuario_id: ID of user deleting
            documento_id: ID of deleted document
            nome: Document name
            permanent: Whether this is a permanent deletion
            
        Returns:
            Created LogAuditoria instance
        """
        acao = 'permanent_delete' if permanent else 'delete'
        
        return self.log_action(
            usuario_id=usuario_id,
            acao=acao,
            tabela='documentos',
            registro_id=documento_id,
            dados={'nome': nome}
        )
    
    def log_document_restore(
        self,
        usuario_id: int,
        documento_id: int,
        nome: str
    ) -> LogAuditoria:
        """
        Log a document restoration from trash
        
        Args:
            usuario_id: ID of user restoring
            documento_id: ID of restored document
            nome: Document name
            
        Returns:
            Created LogAuditoria instance
        """
        return self.log_action(
            usuario_id=usuario_id,
            acao='restore',
            tabela='documentos',
            registro_id=documento_id,
            dados={'nome': nome}
        )
    
    def log_document_share(
        self,
        usuario_id: int,
        documento_id: int,
        shared_with_user_id: int,
        permission_type: str
    ) -> LogAuditoria:
        """
        Log a document share action
        
        Args:
            usuario_id: ID of user sharing
            documento_id: ID of shared document
            shared_with_user_id: ID of user receiving access
            permission_type: Type of permission granted
            
        Returns:
            Created LogAuditoria instance
        """
        return self.log_action(
            usuario_id=usuario_id,
            acao='share',
            tabela='documentos',
            registro_id=documento_id,
            dados={
                'shared_with_user_id': shared_with_user_id,
                'permission_type': permission_type
            }
        )
    
    def log_version_create(
        self,
        usuario_id: int,
        documento_id: int,
        version_number: int,
        comentario: str
    ) -> LogAuditoria:
        """
        Log creation of a new document version
        
        Args:
            usuario_id: ID of user creating version
            documento_id: ID of document
            version_number: New version number
            comentario: Version comment
            
        Returns:
            Created LogAuditoria instance
        """
        return self.log_action(
            usuario_id=usuario_id,
            acao='create_version',
            tabela='versoes',
            registro_id=documento_id,
            dados={
                'version_number': version_number,
                'comentario': comentario
            }
        )
    
    def log_workflow_action(
        self,
        usuario_id: int,
        documento_id: int,
        acao: str,
        workflow_id: Optional[int] = None,
        comentario: Optional[str] = None
    ) -> LogAuditoria:
        """
        Log a workflow-related action
        
        Args:
            usuario_id: ID of user performing action
            documento_id: ID of document in workflow
            acao: Action (submit, approve, reject)
            workflow_id: ID of workflow
            comentario: Optional comment
            
        Returns:
            Created LogAuditoria instance
        """
        dados = {}
        if workflow_id:
            dados['workflow_id'] = workflow_id
        if comentario:
            dados['comentario'] = comentario
        
        return self.log_action(
            usuario_id=usuario_id,
            acao=f'workflow_{acao}',
            tabela='documentos',
            registro_id=documento_id,
            dados=dados if dados else None
        )
    
    def log_user_action(
        self,
        admin_id: int,
        acao: str,
        target_user_id: int,
        dados: Optional[Dict[str, Any]] = None
    ) -> LogAuditoria:
        """
        Log an administrative action on a user account
        
        Args:
            admin_id: ID of administrator performing action
            acao: Action (create, edit, activate, deactivate, delete)
            target_user_id: ID of user being affected
            dados: Additional context data
            
        Returns:
            Created LogAuditoria instance
        """
        return self.log_action(
            usuario_id=admin_id,
            acao=f'user_{acao}',
            tabela='usuarios',
            registro_id=target_user_id,
            dados=dados
        )
    
    def get_user_activity(
        self,
        usuario_id: int,
        limit: Optional[int] = 100
    ) -> List[LogAuditoria]:
        """
        Get recent activity for a specific user
        
        Args:
            usuario_id: User ID
            limit: Maximum number of records to return
            
        Returns:
            List of LogAuditoria instances
        """
        return self.audit_repository.get_by_user(usuario_id, limit=limit)
    
    def get_document_audit_trail(self, documento_id: int) -> List[LogAuditoria]:
        """
        Get complete audit trail for a document
        
        Args:
            documento_id: Document ID
            
        Returns:
            List of LogAuditoria instances ordered by date descending
        """
        return self.audit_repository.get_document_history(documento_id)
    
    def get_recent_activity(
        self,
        hours: int = 24,
        limit: int = 100
    ) -> List[LogAuditoria]:
        """
        Get recent system activity
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of records to return
            
        Returns:
            List of recent LogAuditoria instances
        """
        return self.audit_repository.get_recent_activity(hours=hours, limit=limit)
    
    def get_login_history(
        self,
        usuario_id: Optional[int] = None,
        success_only: bool = False,
        hours: int = 24
    ) -> List[LogAuditoria]:
        """
        Get login attempt history
        
        Args:
            usuario_id: Optional user ID filter
            success_only: If True, only return successful logins
            hours: Number of hours to look back
            
        Returns:
            List of login LogAuditoria instances
        """
        return self.audit_repository.get_login_attempts(
            usuario_id=usuario_id,
            success_only=success_only,
            hours=hours
        )
    
    def check_failed_login_attempts(
        self,
        ip_address: str,
        minutes: int = 15
    ) -> int:
        """
        Check number of failed login attempts from an IP address
        
        Args:
            ip_address: IP address to check
            minutes: Time window in minutes
            
        Returns:
            Number of failed attempts
        """
        return self.audit_repository.get_failed_login_attempts(
            ip_address=ip_address,
            minutes=minutes
        )

    def filter_logs(
        self,
        usuario_id: Optional[int] = None,
        acao: Optional[str] = None,
        tabela: Optional[str] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        ip_address: Optional[str] = None,
        page: int = 1,
        per_page: int = 50
    ) -> Dict[str, Any]:
        """
        Filter audit logs with multiple criteria and pagination
        
        Args:
            usuario_id: Optional user ID filter
            acao: Optional action type filter
            tabela: Optional table name filter
            data_inicio: Optional start date filter
            data_fim: Optional end date filter
            ip_address: Optional IP address filter
            page: Page number for pagination
            per_page: Items per page
            
        Returns:
            Paginated results dictionary with items, total, page info
            
        Example:
            results = audit_service.filter_logs(
                usuario_id=1,
                acao='upload',
                data_inicio=datetime(2024, 1, 1),
                page=1,
                per_page=20
            )
        """
        return self.audit_repository.filter_logs(
            usuario_id=usuario_id,
            acao=acao,
            tabela=tabela,
            data_inicio=data_inicio,
            data_fim=data_fim,
            ip_address=ip_address,
            page=page,
            per_page=per_page
        )
    
    def get_action_statistics(
        self,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get statistics of actions performed in a time period
        
        Args:
            data_inicio: Optional start date
            data_fim: Optional end date
            
        Returns:
            List of dicts with action and count, ordered by count descending
            
        Example:
            stats = audit_service.get_action_statistics(
                data_inicio=datetime(2024, 1, 1),
                data_fim=datetime(2024, 12, 31)
            )
            # Returns: [{'acao': 'login', 'count': 1500}, {'acao': 'upload', 'count': 850}, ...]
        """
        return self.audit_repository.get_action_statistics(
            data_inicio=data_inicio,
            data_fim=data_fim
        )
    
    def get_user_activity_statistics(
        self,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get most active users by action count
        
        Args:
            data_inicio: Optional start date
            data_fim: Optional end date
            limit: Maximum number of users to return
            
        Returns:
            List of dicts with usuario_id and action count
            
        Example:
            stats = audit_service.get_user_activity_statistics(limit=5)
            # Returns: [{'usuario_id': 1, 'count': 250}, {'usuario_id': 5, 'count': 180}, ...]
        """
        return self.audit_repository.get_user_activity_statistics(
            data_inicio=data_inicio,
            data_fim=data_fim,
            limit=limit
        )
    
    def get_daily_activity(
        self,
        days: int = 30,
        acao: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get daily activity counts for the past N days
        
        Args:
            days: Number of days to look back
            acao: Optional action type filter
            
        Returns:
            List of dicts with date and count
            
        Example:
            activity = audit_service.get_daily_activity(days=7, acao='upload')
            # Returns: [{'date': '2024-01-01', 'count': 45}, {'date': '2024-01-02', 'count': 52}, ...]
        """
        return self.audit_repository.get_daily_activity(days=days, acao=acao)
    
    def export_logs(
        self,
        usuario_id: Optional[int] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        format: str = 'json'
    ) -> Any:
        """
        Export audit logs for reporting
        
        Args:
            usuario_id: Optional user ID filter
            data_inicio: Optional start date
            data_fim: Optional end date
            format: Export format ('json', 'csv', 'dict')
            
        Returns:
            Exported data in requested format
            
        Example:
            # Export as JSON
            json_data = audit_service.export_logs(
                usuario_id=1,
                data_inicio=datetime(2024, 1, 1),
                format='json'
            )
            
            # Export as CSV
            csv_data = audit_service.export_logs(
                data_inicio=datetime(2024, 1, 1),
                format='csv'
            )
        """
        # Get logs as dictionaries
        logs = self.audit_repository.export_logs(
            usuario_id=usuario_id,
            data_inicio=data_inicio,
            data_fim=data_fim
        )
        
        if format == 'json':
            import json
            return json.dumps(logs, indent=2, default=str)
        
        elif format == 'csv':
            import csv
            import io
            
            if not logs:
                return ''
            
            output = io.StringIO()
            
            # Get all possible keys from logs
            fieldnames = ['id', 'usuario_id', 'acao', 'tabela', 'registro_id', 
                         'ip_address', 'user_agent', 'data_hora', 'dados']
            
            writer = csv.DictWriter(output, fieldnames=fieldnames)
            writer.writeheader()
            
            for log in logs:
                # Convert dados dict to string for CSV
                if 'dados' in log and log['dados']:
                    log['dados'] = str(log['dados'])
                writer.writerow(log)
            
            return output.getvalue()
        
        else:  # format == 'dict' or default
            return logs
    
    def generate_audit_report(
        self,
        report_type: str,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Generate comprehensive audit report
        
        Args:
            report_type: Type of report ('summary', 'user_activity', 'document_activity', 'security')
            data_inicio: Optional start date
            data_fim: Optional end date
            **kwargs: Additional parameters specific to report type
            
        Returns:
            Dictionary containing report data
            
        Example:
            # Summary report
            report = audit_service.generate_audit_report(
                report_type='summary',
                data_inicio=datetime(2024, 1, 1),
                data_fim=datetime(2024, 12, 31)
            )
            
            # User activity report
            report = audit_service.generate_audit_report(
                report_type='user_activity',
                usuario_id=1,
                data_inicio=datetime(2024, 1, 1)
            )
        """
        if report_type == 'summary':
            return self._generate_summary_report(data_inicio, data_fim)
        
        elif report_type == 'user_activity':
            usuario_id = kwargs.get('usuario_id')
            return self._generate_user_activity_report(usuario_id, data_inicio, data_fim)
        
        elif report_type == 'document_activity':
            documento_id = kwargs.get('documento_id')
            return self._generate_document_activity_report(documento_id, data_inicio, data_fim)
        
        elif report_type == 'security':
            return self._generate_security_report(data_inicio, data_fim)
        
        else:
            raise AuditServiceError(f"Unknown report type: {report_type}")
    
    def _generate_summary_report(
        self,
        data_inicio: Optional[datetime],
        data_fim: Optional[datetime]
    ) -> Dict[str, Any]:
        """Generate summary audit report"""
        # Get action statistics
        action_stats = self.get_action_statistics(data_inicio, data_fim)
        
        # Get user activity statistics
        user_stats = self.get_user_activity_statistics(data_inicio, data_fim, limit=10)
        
        # Get daily activity
        days = 30
        if data_inicio and data_fim:
            days = (data_fim - data_inicio).days
        daily_activity = self.get_daily_activity(days=min(days, 90))
        
        # Calculate total actions
        total_actions = sum(stat['count'] for stat in action_stats)
        
        return {
            'report_type': 'summary',
            'period': {
                'data_inicio': data_inicio.isoformat() if data_inicio else None,
                'data_fim': data_fim.isoformat() if data_fim else None
            },
            'total_actions': total_actions,
            'action_statistics': action_stats,
            'top_users': user_stats,
            'daily_activity': daily_activity,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _generate_user_activity_report(
        self,
        usuario_id: Optional[int],
        data_inicio: Optional[datetime],
        data_fim: Optional[datetime]
    ) -> Dict[str, Any]:
        """Generate user activity audit report"""
        if not usuario_id:
            raise AuditServiceError("usuario_id is required for user_activity report")
        
        # Get user's logs
        logs_result = self.filter_logs(
            usuario_id=usuario_id,
            data_inicio=data_inicio,
            data_fim=data_fim,
            per_page=1000  # Get more for report
        )
        
        # Count actions by type
        action_counts = {}
        for log in logs_result['items']:
            action_counts[log.acao] = action_counts.get(log.acao, 0) + 1
        
        # Get login history
        login_history = self.get_login_history(usuario_id=usuario_id, hours=24*30)
        
        return {
            'report_type': 'user_activity',
            'usuario_id': usuario_id,
            'period': {
                'data_inicio': data_inicio.isoformat() if data_inicio else None,
                'data_fim': data_fim.isoformat() if data_fim else None
            },
            'total_actions': logs_result['total'],
            'action_breakdown': action_counts,
            'recent_logins': len([l for l in login_history if l.acao == 'login']),
            'failed_logins': len([l for l in login_history if l.acao == 'login_failed']),
            'recent_activity': [
                {
                    'acao': log.acao,
                    'tabela': log.tabela,
                    'registro_id': log.registro_id,
                    'data_hora': log.data_hora.isoformat() if log.data_hora else None,
                    'ip_address': log.ip_address
                }
                for log in logs_result['items'][:50]  # Last 50 actions
            ],
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _generate_document_activity_report(
        self,
        documento_id: Optional[int],
        data_inicio: Optional[datetime],
        data_fim: Optional[datetime]
    ) -> Dict[str, Any]:
        """Generate document activity audit report"""
        if not documento_id:
            raise AuditServiceError("documento_id is required for document_activity report")
        
        # Get document audit trail
        logs = self.get_document_audit_trail(documento_id)
        
        # Filter by date if provided
        if data_inicio:
            logs = [l for l in logs if l.data_hora >= data_inicio]
        if data_fim:
            logs = [l for l in logs if l.data_hora <= data_fim]
        
        # Count actions by type
        action_counts = {}
        unique_users = set()
        for log in logs:
            action_counts[log.acao] = action_counts.get(log.acao, 0) + 1
            if log.usuario_id:
                unique_users.add(log.usuario_id)
        
        return {
            'report_type': 'document_activity',
            'documento_id': documento_id,
            'period': {
                'data_inicio': data_inicio.isoformat() if data_inicio else None,
                'data_fim': data_fim.isoformat() if data_fim else None
            },
            'total_actions': len(logs),
            'unique_users': len(unique_users),
            'action_breakdown': action_counts,
            'views': action_counts.get('view', 0),
            'downloads': action_counts.get('download', 0),
            'edits': action_counts.get('edit', 0),
            'timeline': [
                {
                    'acao': log.acao,
                    'usuario_id': log.usuario_id,
                    'data_hora': log.data_hora.isoformat() if log.data_hora else None,
                    'ip_address': log.ip_address,
                    'dados': log.dados
                }
                for log in logs
            ],
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def _generate_security_report(
        self,
        data_inicio: Optional[datetime],
        data_fim: Optional[datetime]
    ) -> Dict[str, Any]:
        """Generate security audit report"""
        # Get all login attempts
        all_logins = self.audit_repository.filter_logs(
            acao='login',
            data_inicio=data_inicio,
            data_fim=data_fim,
            per_page=10000
        )
        
        failed_logins = self.audit_repository.filter_logs(
            acao='login_failed',
            data_inicio=data_inicio,
            data_fim=data_fim,
            per_page=10000
        )
        
        # Analyze failed login patterns
        failed_by_ip = {}
        failed_by_user = {}
        
        for log in failed_logins['items']:
            if log.ip_address:
                failed_by_ip[log.ip_address] = failed_by_ip.get(log.ip_address, 0) + 1
            if log.usuario_id:
                failed_by_user[log.usuario_id] = failed_by_user.get(log.usuario_id, 0) + 1
        
        # Get top suspicious IPs (most failed logins)
        suspicious_ips = sorted(
            [{'ip': ip, 'failed_attempts': count} for ip, count in failed_by_ip.items()],
            key=lambda x: x['failed_attempts'],
            reverse=True
        )[:10]
        
        # Get users with most failed logins
        users_with_failures = sorted(
            [{'usuario_id': uid, 'failed_attempts': count} for uid, count in failed_by_user.items()],
            key=lambda x: x['failed_attempts'],
            reverse=True
        )[:10]
        
        return {
            'report_type': 'security',
            'period': {
                'data_inicio': data_inicio.isoformat() if data_inicio else None,
                'data_fim': data_fim.isoformat() if data_fim else None
            },
            'successful_logins': all_logins['total'],
            'failed_logins': failed_logins['total'],
            'success_rate': (all_logins['total'] / (all_logins['total'] + failed_logins['total']) * 100) 
                           if (all_logins['total'] + failed_logins['total']) > 0 else 0,
            'suspicious_ips': suspicious_ips,
            'users_with_failures': users_with_failures,
            'generated_at': datetime.utcnow().isoformat()
        }
    
    def cleanup_old_logs(self, days: int = 365) -> int:
        """
        Delete audit logs older than specified days
        
        Args:
            days: Delete logs older than this many days (default: 365)
            
        Returns:
            Number of logs deleted
            
        Note:
            This should be used carefully as it permanently deletes audit data.
            Ensure compliance with data retention policies before using.
        """
        return self.audit_repository.cleanup_old_logs(days=days)
