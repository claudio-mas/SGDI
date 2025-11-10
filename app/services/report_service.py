"""
Report service for generating system reports
"""
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy import func, and_
from sqlalchemy.types import Date
from io import BytesIO
import csv
from app import db
from app.models import User, Documento, LogAuditoria, Perfil
from app.repositories.document_repository import DocumentRepository
from app.repositories.user_repository import UserRepository
from app.repositories.audit_repository import AuditRepository


class ReportService:
    """
    Service for generating various system reports including usage,
    access, and storage reports with export capabilities.
    """
    
    def __init__(self):
        """Initialize ReportService with required repositories."""
        self.document_repository = DocumentRepository()
        self.user_repository = UserRepository()
        self.audit_repository = AuditRepository()
    
    def generate_usage_report(
        self,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Generate system usage report.
        
        Args:
            data_inicio: Start date for report
            data_fim: End date for report
            
        Returns:
            Dictionary with usage statistics
        """
        if not data_inicio:
            data_inicio = datetime.utcnow() - timedelta(days=30)
        if not data_fim:
            data_fim = datetime.utcnow()
        
        # Document uploads in period
        uploads = db.session.query(func.count(Documento.id)).filter(
            Documento.data_upload.between(data_inicio, data_fim)
        ).scalar() or 0
        
        # User logins in period
        logins = db.session.query(func.count(LogAuditoria.id)).filter(
            LogAuditoria.acao == 'login_success',
            LogAuditoria.data_hora.between(data_inicio, data_fim)
        ).scalar() or 0
        
        # Document downloads in period
        downloads = db.session.query(func.count(LogAuditoria.id)).filter(
            LogAuditoria.acao == 'document_download',
            LogAuditoria.data_hora.between(data_inicio, data_fim)
        ).scalar() or 0
        
        # Active users in period
        active_users = db.session.query(func.count(func.distinct(LogAuditoria.usuario_id))).filter(
            LogAuditoria.data_hora.between(data_inicio, data_fim)
        ).scalar() or 0
        
        # Top users by activity
        top_users = db.session.query(
            User.id,
            User.nome,
            User.email,
            func.count(LogAuditoria.id).label('activity_count')
        ).join(
            LogAuditoria, User.id == LogAuditoria.usuario_id
        ).filter(
            LogAuditoria.data_hora.between(data_inicio, data_fim)
        ).group_by(
            User.id, User.nome, User.email
        ).order_by(
            func.count(LogAuditoria.id).desc()
        ).limit(10).all()
        
        # Daily activity - Use CAST for SQL Server compatibility
        daily_activity = db.session.query(
            func.cast(LogAuditoria.data_hora, Date).label('date'),
            func.count(LogAuditoria.id).label('count')
        ).filter(
            LogAuditoria.data_hora.between(data_inicio, data_fim)
        ).group_by(
            func.cast(LogAuditoria.data_hora, Date)
        ).order_by('date').all()
        
        return {
            'period': {
                'start': data_inicio.isoformat(),
                'end': data_fim.isoformat()
            },
            'summary': {
                'total_uploads': uploads,
                'total_logins': logins,
                'total_downloads': downloads,
                'active_users': active_users
            },
            'top_users': [
                {
                    'user_id': u.id,
                    'name': u.nome,
                    'email': u.email,
                    'activity_count': u.activity_count
                }
                for u in top_users
            ],
            'daily_activity': [
                {
                    'date': d.date.isoformat() if d.date else None,
                    'count': d.count
                }
                for d in daily_activity
            ]
        }
    
    def generate_access_report(
        self,
        data_inicio: Optional[datetime] = None,
        data_fim: Optional[datetime] = None,
        usuario_id: Optional[int] = None,
        documento_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Generate document access report.
        
        Args:
            data_inicio: Start date for report
            data_fim: End date for report
            usuario_id: Filter by specific user
            documento_id: Filter by specific document
            
        Returns:
            Dictionary with access statistics
        """
        if not data_inicio:
            data_inicio = datetime.utcnow() - timedelta(days=30)
        if not data_fim:
            data_fim = datetime.utcnow()
        
        # Build query
        query = db.session.query(
            LogAuditoria.id,
            LogAuditoria.usuario_id,
            User.nome.label('user_name'),
            LogAuditoria.acao,
            LogAuditoria.registro_id,
            LogAuditoria.data_hora,
            LogAuditoria.ip_address
        ).join(
            User, LogAuditoria.usuario_id == User.id
        ).filter(
            LogAuditoria.tabela == 'documentos',
            LogAuditoria.acao.in_(['document_view', 'document_download', 'document_upload']),
            LogAuditoria.data_hora.between(data_inicio, data_fim)
        )
        
        if usuario_id:
            query = query.filter(LogAuditoria.usuario_id == usuario_id)
        
        if documento_id:
            query = query.filter(LogAuditoria.registro_id == documento_id)
        
        access_logs = query.order_by(LogAuditoria.data_hora.desc()).limit(1000).all()
        
        # Access summary by action
        action_summary = db.session.query(
            LogAuditoria.acao,
            func.count(LogAuditoria.id).label('count')
        ).filter(
            LogAuditoria.tabela == 'documentos',
            LogAuditoria.acao.in_(['document_view', 'document_download', 'document_upload']),
            LogAuditoria.data_hora.between(data_inicio, data_fim)
        )
        
        if usuario_id:
            action_summary = action_summary.filter(LogAuditoria.usuario_id == usuario_id)
        
        if documento_id:
            action_summary = action_summary.filter(LogAuditoria.registro_id == documento_id)
        
        action_summary = action_summary.group_by(LogAuditoria.acao).all()
        
        return {
            'period': {
                'start': data_inicio.isoformat(),
                'end': data_fim.isoformat()
            },
            'filters': {
                'usuario_id': usuario_id,
                'documento_id': documento_id
            },
            'summary': {
                action.acao: action.count for action in action_summary
            },
            'access_logs': [
                {
                    'id': log.id,
                    'user_id': log.usuario_id,
                    'user_name': log.user_name,
                    'action': log.acao,
                    'document_id': log.registro_id,
                    'timestamp': log.data_hora.isoformat() if log.data_hora else None,
                    'ip_address': log.ip_address
                }
                for log in access_logs
            ]
        }
    
    def generate_storage_report(self) -> Dict[str, Any]:
        """
        Generate storage usage report by user.
        
        Returns:
            Dictionary with storage statistics
        """
        # Storage by user
        storage_by_user = db.session.query(
            User.id,
            User.nome,
            User.email,
            Perfil.nome.label('perfil_nome'),
            func.count(Documento.id).label('document_count'),
            func.sum(Documento.tamanho_bytes).label('total_bytes')
        ).join(
            Documento, User.id == Documento.usuario_id
        ).join(
            Perfil, User.perfil_id == Perfil.id
        ).filter(
            Documento.status == 'ativo'
        ).group_by(
            User.id, User.nome, User.email, Perfil.nome
        ).order_by(
            func.sum(Documento.tamanho_bytes).desc()
        ).all()
        
        # Storage by file type
        storage_by_type = db.session.query(
            Documento.tipo_mime,
            func.count(Documento.id).label('document_count'),
            func.sum(Documento.tamanho_bytes).label('total_bytes')
        ).filter(
            Documento.status == 'ativo'
        ).group_by(
            Documento.tipo_mime
        ).order_by(
            func.sum(Documento.tamanho_bytes).desc()
        ).all()
        
        # Total storage
        total_storage = db.session.query(
            func.sum(Documento.tamanho_bytes)
        ).filter(
            Documento.status == 'ativo'
        ).scalar() or 0
        
        return {
            'total_storage_bytes': total_storage,
            'total_storage_formatted': self._format_bytes(total_storage),
            'by_user': [
                {
                    'user_id': u.id,
                    'name': u.nome,
                    'email': u.email,
                    'profile': u.perfil_nome,
                    'document_count': u.document_count,
                    'total_bytes': u.total_bytes or 0,
                    'total_formatted': self._format_bytes(u.total_bytes or 0)
                }
                for u in storage_by_user
            ],
            'by_type': [
                {
                    'mime_type': t.tipo_mime,
                    'document_count': t.document_count,
                    'total_bytes': t.total_bytes or 0,
                    'total_formatted': self._format_bytes(t.total_bytes or 0)
                }
                for t in storage_by_type
            ]
        }
    
    def export_report_csv(self, report_data: Dict[str, Any], report_type: str) -> BytesIO:
        """
        Export report data to CSV format.
        
        Args:
            report_data: Report data dictionary
            report_type: Type of report (usage, access, storage)
            
        Returns:
            BytesIO object containing CSV data
        """
        output = BytesIO()
        output.write('\ufeff'.encode('utf-8'))  # UTF-8 BOM
        
        writer = csv.writer(output, delimiter=';')
        
        if report_type == 'usage':
            writer.writerow(['Relatório de Uso do Sistema'])
            writer.writerow(['Período', f"{report_data['period']['start']} a {report_data['period']['end']}"])
            writer.writerow([])
            writer.writerow(['Resumo'])
            writer.writerow(['Total de Uploads', report_data['summary']['total_uploads']])
            writer.writerow(['Total de Logins', report_data['summary']['total_logins']])
            writer.writerow(['Total de Downloads', report_data['summary']['total_downloads']])
            writer.writerow(['Usuários Ativos', report_data['summary']['active_users']])
            writer.writerow([])
            writer.writerow(['Top Usuários por Atividade'])
            writer.writerow(['Nome', 'Email', 'Atividades'])
            for user in report_data['top_users']:
                writer.writerow([user['name'], user['email'], user['activity_count']])
        
        elif report_type == 'access':
            writer.writerow(['Relatório de Acessos'])
            writer.writerow(['Período', f"{report_data['period']['start']} a {report_data['period']['end']}"])
            writer.writerow([])
            writer.writerow(['Resumo por Ação'])
            for action, count in report_data['summary'].items():
                writer.writerow([action, count])
            writer.writerow([])
            writer.writerow(['Logs de Acesso'])
            writer.writerow(['Usuário', 'Ação', 'ID Documento', 'Data/Hora', 'IP'])
            for log in report_data['access_logs']:
                writer.writerow([
                    log['user_name'],
                    log['action'],
                    log['document_id'],
                    log['timestamp'],
                    log['ip_address']
                ])
        
        elif report_type == 'storage':
            writer.writerow(['Relatório de Armazenamento'])
            writer.writerow(['Total', report_data['total_storage_formatted']])
            writer.writerow([])
            writer.writerow(['Armazenamento por Usuário'])
            writer.writerow(['Nome', 'Email', 'Perfil', 'Documentos', 'Armazenamento'])
            for user in report_data['by_user']:
                writer.writerow([
                    user['name'],
                    user['email'],
                    user['profile'],
                    user['document_count'],
                    user['total_formatted']
                ])
            writer.writerow([])
            writer.writerow(['Armazenamento por Tipo de Arquivo'])
            writer.writerow(['Tipo MIME', 'Documentos', 'Armazenamento'])
            for file_type in report_data['by_type']:
                writer.writerow([
                    file_type['mime_type'],
                    file_type['document_count'],
                    file_type['total_formatted']
                ])
        
        output.seek(0)
        return output
    
    def _format_bytes(self, bytes_value: int) -> str:
        """Format bytes to human-readable string."""
        if bytes_value == 0:
            return "0 B"
        
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        unit_index = 0
        value = float(bytes_value)
        
        while value >= 1024 and unit_index < len(units) - 1:
            value /= 1024
            unit_index += 1
        
        return f"{value:.2f} {units[unit_index]}"
