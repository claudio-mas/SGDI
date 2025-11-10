"""
Admin service for system administration operations
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func
from sqlalchemy.types import Date
from app import db
from app.models import User, Documento, LogAuditoria, Perfil
from app.repositories.user_repository import UserRepository, PerfilRepository
from app.repositories.document_repository import DocumentRepository
from app.repositories.audit_repository import AuditRepository


class AdminService:
    """
    Service for administrative operations including dashboard statistics,
    user management, and system configuration.
    """
    
    def __init__(self):
        """Initialize AdminService with required repositories."""
        self.user_repository = UserRepository()
        self.perfil_repository = PerfilRepository()
        self.document_repository = DocumentRepository()
        self.audit_repository = AuditRepository()
    
    def get_dashboard_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard statistics.
        
        Returns:
            Dictionary with system statistics
        """
        # Total counts
        total_users = self.user_repository.count()
        active_users = len(self.user_repository.get_active_users())
        total_documents = self.document_repository.count()
        
        # Storage statistics
        total_storage = self.document_repository.get_total_storage_usage()
        storage_capacity = 2 * 1024 * 1024 * 1024 * 1024  # 2TB in bytes
        storage_percentage = (total_storage / storage_capacity * 100) if storage_capacity > 0 else 0
        
        # Recent activity (last 24 hours)
        recent_uploads = self._get_recent_uploads_count(hours=24)
        recent_logins = self._get_recent_logins_count(hours=24)
        
        # Document statistics by type
        documents_by_type = self.document_repository.get_document_count_by_type()
        
        return {
            'total_users': total_users,
            'active_users': active_users,
            'total_documents': total_documents,
            'total_storage_bytes': total_storage,
            'total_storage_formatted': self._format_bytes(total_storage),
            'storage_capacity_bytes': storage_capacity,
            'storage_capacity_formatted': self._format_bytes(storage_capacity),
            'storage_percentage': round(storage_percentage, 2),
            'recent_uploads_24h': recent_uploads,
            'recent_logins_24h': recent_logins,
            'documents_by_type': documents_by_type
        }
    
    def get_upload_statistics(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get document upload statistics over time.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of daily upload counts
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        # Use CAST for SQL Server compatibility
        # (instead of func.date which is SQLite-specific)
        date_column = func.cast(Documento.data_upload, Date).label('date')
        
        results = db.session.query(
            date_column,
            func.count(Documento.id).label('count')
        ).filter(
            Documento.data_upload >= cutoff_date
        ).group_by(
            func.cast(Documento.data_upload, Date)
        ).order_by('date').all()
        
        return [
            {
                'date': r.date.isoformat() if r.date else None,
                'count': r.count
            }
            for r in results
        ]
    
    def get_storage_by_user(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get storage usage by user (top users).
        
        Args:
            limit: Maximum number of users to return
            
        Returns:
            List of users with storage usage
        """
        results = db.session.query(
            User.id,
            User.nome,
            User.email,
            func.count(Documento.id).label('document_count'),
            func.sum(Documento.tamanho_bytes).label('total_bytes')
        ).join(
            Documento, User.id == Documento.usuario_id
        ).filter(
            Documento.status == 'ativo'
        ).group_by(
            User.id, User.nome, User.email
        ).order_by(
            func.sum(Documento.tamanho_bytes).desc()
        ).limit(limit).all()
        
        return [
            {
                'user_id': r.id,
                'user_name': r.nome,
                'user_email': r.email,
                'document_count': r.document_count,
                'total_bytes': r.total_bytes or 0,
                'total_formatted': self._format_bytes(r.total_bytes or 0)
            }
            for r in results
        ]
    
    def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        Get recent system activity from audit logs.
        
        Args:
            limit: Maximum number of activities to return
            
        Returns:
            List of recent activities
        """
        logs = self.audit_repository.get_recent_activity(hours=24, limit=limit)
        
        return [
            {
                'id': log.id,
                'user_name': log.usuario.nome if log.usuario else 'System',
                'action': log.acao,
                'table': log.tabela,
                'timestamp': log.data_hora.isoformat() if log.data_hora else None,
                'ip_address': log.ip_address
            }
            for log in logs
        ]
    
    def get_user_statistics(self) -> Dict[str, Any]:
        """
        Get user statistics by profile.
        
        Returns:
            Dictionary with user counts by profile
        """
        results = db.session.query(
            Perfil.nome,
            func.count(User.id).label('count')
        ).join(
            User, Perfil.id == User.perfil_id
        ).group_by(
            Perfil.nome
        ).all()
        
        users_by_profile = {r.nome: r.count for r in results}
        
        # Get locked accounts
        locked_accounts = len(self.user_repository.get_locked_accounts())
        
        return {
            'by_profile': users_by_profile,
            'locked_accounts': locked_accounts
        }
    
    def _get_recent_uploads_count(self, hours: int = 24) -> int:
        """Get count of documents uploaded in last N hours."""
        cutoff_date = datetime.utcnow() - timedelta(hours=hours)
        return db.session.query(func.count(Documento.id)).filter(
            Documento.data_upload >= cutoff_date
        ).scalar() or 0
    
    def _get_recent_logins_count(self, hours: int = 24) -> int:
        """Get count of successful logins in last N hours."""
        cutoff_date = datetime.utcnow() - timedelta(hours=hours)
        return db.session.query(func.count(LogAuditoria.id)).filter(
            LogAuditoria.acao == 'login_success',
            LogAuditoria.data_hora >= cutoff_date
        ).scalar() or 0
    
    def _format_bytes(self, bytes_value: int) -> str:
        """
        Format bytes to human-readable string.
        
        Args:
            bytes_value: Number of bytes
            
        Returns:
            Formatted string (e.g., "1.5 GB")
        """
        if bytes_value == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        value = float(bytes_value)
        
        while value >= 1024 and unit_index < len(units) - 1:
            value /= 1024
            unit_index += 1
        
        return f"{value:.2f} {units[unit_index]}"
