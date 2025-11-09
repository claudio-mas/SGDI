"""
Audit repository for log queries
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from app.repositories.base_repository import BaseRepository
from app.models.audit import LogAuditoria


class AuditRepository(BaseRepository[LogAuditoria]):
    """
    Repository for LogAuditoria model with specialized audit queries.
    Handles audit log filtering, reporting, and analysis.
    """
    
    def __init__(self):
        """Initialize AuditRepository with LogAuditoria model."""
        super().__init__(LogAuditoria)
    
    def get_by_user(
        self,
        usuario_id: int,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> List[LogAuditoria]:
        """
        Get audit logs for a specific user.
        
        Args:
            usuario_id: User ID
            limit: Maximum number of records to return
            offset: Number of records to skip
            
        Returns:
            List of LogAuditoria instances
        """
        query = self.get_query().filter(
            LogAuditoria.usuario_id == usuario_id
        ).order_by(LogAuditoria.data_hora.desc())
        
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_by_action(self, acao: str, limit: Optional[int] = None) -> List[LogAuditoria]:
        """
        Get audit logs for a specific action type.
        
        Args:
            acao: Action type (login, upload, download, etc.)
            limit: Maximum number of records to return
            
        Returns:
            List of LogAuditoria instances
        """
        query = self.get_query().filter(
            LogAuditoria.acao == acao
        ).order_by(LogAuditoria.data_hora.desc())
        
        if limit:
            query = query.limit(limit)
        
        return query.all()
    
    def get_by_entity(self, tabela: str, registro_id: int) -> List[LogAuditoria]:
        """
        Get audit logs for a specific entity/record.
        
        Args:
            tabela: Table name
            registro_id: Record ID
            
        Returns:
            List of LogAuditoria instances
        """
        return self.get_query().filter(
            LogAuditoria.tabela == tabela,
            LogAuditoria.registro_id == registro_id
        ).order_by(LogAuditoria.data_hora.desc()).all()
    
    def get_document_history(self, documento_id: int) -> List[LogAuditoria]:
        """
        Get complete audit history for a document.
        
        Args:
            documento_id: Document ID
            
        Returns:
            List of LogAuditoria instances
        """
        return self.get_by_entity('documentos', documento_id)
    
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
        Filter audit logs with multiple criteria.
        
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
            Paginated results dictionary
        """
        query = self.get_query()
        
        # Apply filters
        if usuario_id:
            query = query.filter(LogAuditoria.usuario_id == usuario_id)
        if acao:
            query = query.filter(LogAuditoria.acao == acao)
        if tabela:
            query = query.filter(LogAuditoria.tabela == tabela)
        if data_inicio:
            query = query.filter(LogAuditoria.data_hora >= data_inicio)
        if data_fim:
            query = query.filter(LogAuditoria.data_hora <= data_fim)
        if ip_address:
            query = query.filter(LogAuditoria.ip_address == ip_address)
        
        # Order by date descending
        query = query.order_by(LogAuditoria.data_hora.desc())
        
        # Get total count
        total = query.count()
        
        # Calculate pagination
        pages = (total + per_page - 1) // per_page
        page = max(1, min(page, pages)) if pages > 0 else 1
        offset = (page - 1) * per_page
        
        # Get paginated results
        items = query.limit(per_page).offset(offset).all()
        
        return {
            'items': items,
            'total': total,
            'page': page,
            'per_page': per_page,
            'pages': pages,
            'has_prev': page > 1,
            'has_next': page < pages
        }
    
    def get_recent_activity(self, hours: int = 24, limit: int = 100) -> List[LogAuditoria]:
        """
        Get recent activity within specified hours.
        
        Args:
            hours: Number of hours to look back
            limit: Maximum number of records to return
            
        Returns:
            List of recent LogAuditoria instances
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        return self.get_query().filter(
            LogAuditoria.data_hora >= cutoff_time
        ).order_by(LogAuditoria.data_hora.desc()).limit(limit).all()
    
    def get_login_attempts(
        self,
        usuario_id: Optional[int] = None,
        success_only: bool = False,
        hours: int = 24
    ) -> List[LogAuditoria]:
        """
        Get login attempts within specified time period.
        
        Args:
            usuario_id: Optional user ID filter
            success_only: If True, only return successful logins
            hours: Number of hours to look back
            
        Returns:
            List of login LogAuditoria instances
        """
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        query = self.get_query().filter(
            LogAuditoria.acao.in_(['login', 'login_failed']),
            LogAuditoria.data_hora >= cutoff_time
        )
        
        if usuario_id:
            query = query.filter(LogAuditoria.usuario_id == usuario_id)
        
        if success_only:
            query = query.filter(LogAuditoria.acao == 'login')
        
        return query.order_by(LogAuditoria.data_hora.desc()).all()
    
    def get_failed_login_attempts(self, ip_address: str, minutes: int = 15) -> int:
        """
        Count failed login attempts from an IP address within time window.
        
        Args:
            ip_address: IP address to check
            minutes: Time window in minutes
            
        Returns:
            Number of failed attempts
        """
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
        count = self.get_query().filter(
            LogAuditoria.acao == 'login_failed',
            LogAuditoria.ip_address == ip_address,
            LogAuditoria.data_hora >= cutoff_time
        ).count()
        return count
    
    def get_action_statistics(
        self,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get statistics of actions performed.
        
        Args:
            data_inicio: Optional start date
            data_fim: Optional end date
            
        Returns:
            List of dicts with action and count
        """
        query = self.session.query(
            LogAuditoria.acao,
            func.count(LogAuditoria.id).label('count')
        )
        
        if data_inicio:
            query = query.filter(LogAuditoria.data_hora >= data_inicio)
        if data_fim:
            query = query.filter(LogAuditoria.data_hora <= data_fim)
        
        results = query.group_by(LogAuditoria.acao).order_by(
            func.count(LogAuditoria.id).desc()
        ).all()
        
        return [{'acao': r[0], 'count': r[1]} for r in results]
    
    def get_user_activity_statistics(
        self,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Get most active users by action count.
        
        Args:
            data_inicio: Optional start date
            data_fim: Optional end date
            limit: Maximum number of users to return
            
        Returns:
            List of dicts with usuario_id and action count
        """
        query = self.session.query(
            LogAuditoria.usuario_id,
            func.count(LogAuditoria.id).label('count')
        ).filter(LogAuditoria.usuario_id.isnot(None))
        
        if data_inicio:
            query = query.filter(LogAuditoria.data_hora >= data_inicio)
        if data_fim:
            query = query.filter(LogAuditoria.data_hora <= data_fim)
        
        results = query.group_by(LogAuditoria.usuario_id).order_by(
            func.count(LogAuditoria.id).desc()
        ).limit(limit).all()
        
        return [{'usuario_id': r[0], 'count': r[1]} for r in results]
    
    def get_daily_activity(
        self,
        days: int = 30,
        acao: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get daily activity counts for the past N days.
        
        Args:
            days: Number of days to look back
            acao: Optional action type filter
            
        Returns:
            List of dicts with date and count
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        query = self.session.query(
            func.date(LogAuditoria.data_hora).label('date'),
            func.count(LogAuditoria.id).label('count')
        ).filter(LogAuditoria.data_hora >= cutoff_date)
        
        if acao:
            query = query.filter(LogAuditoria.acao == acao)
        
        results = query.group_by(func.date(LogAuditoria.data_hora)).order_by(
            func.date(LogAuditoria.data_hora)
        ).all()
        
        return [{'date': r[0].isoformat() if r[0] else None, 'count': r[1]} for r in results]
    
    def cleanup_old_logs(self, days: int = 365) -> int:
        """
        Delete audit logs older than specified days.
        
        Args:
            days: Delete logs older than this many days
            
        Returns:
            Number of logs deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        count = self.get_query().filter(
            LogAuditoria.data_hora < cutoff_date
        ).delete(synchronize_session=False)
        self.session.commit()
        return count
    
    def export_logs(
        self,
        usuario_id: Optional[int] = None,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Export audit logs as list of dictionaries for reporting.
        
        Args:
            usuario_id: Optional user ID filter
            data_inicio: Optional start date
            data_fim: Optional end date
            
        Returns:
            List of log dictionaries
        """
        query = self.get_query()
        
        if usuario_id:
            query = query.filter(LogAuditoria.usuario_id == usuario_id)
        if data_inicio:
            query = query.filter(LogAuditoria.data_hora >= data_inicio)
        if data_fim:
            query = query.filter(LogAuditoria.data_hora <= data_fim)
        
        logs = query.order_by(LogAuditoria.data_hora.desc()).all()
        
        return [{
            'id': log.id,
            'usuario_id': log.usuario_id,
            'acao': log.acao,
            'tabela': log.tabela,
            'registro_id': log.registro_id,
            'dados': log.dados,
            'ip_address': log.ip_address,
            'user_agent': log.user_agent,
            'data_hora': log.data_hora.isoformat() if log.data_hora else None
        } for log in logs]
