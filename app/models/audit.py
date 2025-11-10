"""
Audit log model
"""
from datetime import datetime
from app import db
import json


class LogAuditoria(db.Model):
    """Audit log model for tracking all system operations"""
    __tablename__ = 'log_auditoria'
    
    # Use Integer with autoincrement to ensure SQLite (and other DBs) will
    # automatically generate the primary key value on insert. Using
    # BigInteger here previously caused NOT NULL constraint failures in the
    # test DB where autoincrement wasn't applied.
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), index=True)
    acao = db.Column(db.String(50), nullable=False, index=True)  # login, upload, download, edit, delete, etc.
    tabela = db.Column(db.String(50), index=True)  # Table/entity affected
    registro_id = db.Column(db.Integer, index=True)  # ID of affected record
    dados_json = db.Column(db.Text)  # Additional context data as JSON
    ip_address = db.Column(db.String(45))  # IPv4 or IPv6
    user_agent = db.Column(db.String(255))  # Browser/client info
    data_hora = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationships
    usuario = db.relationship('User', backref='logs_auditoria')
    
    __table_args__ = (
        db.Index('idx_audit_usuario_data', 'usuario_id', 'data_hora'),
        db.Index('idx_audit_tabela_registro', 'tabela', 'registro_id'),
    )
    
    @property
    def dados(self):
        """Get additional data as dict"""
        return json.loads(self.dados_json) if self.dados_json else {}
    
    @dados.setter
    def dados(self, data_dict):
        """Set additional data from dict"""
        self.dados_json = json.dumps(data_dict) if data_dict else None
    
    @staticmethod
    def log(usuario_id, acao, tabela=None, registro_id=None, dados=None, ip_address=None, user_agent=None):
        """Create audit log entry"""
        log_entry = LogAuditoria(
            usuario_id=usuario_id,
            acao=acao,
            tabela=tabela,
            registro_id=registro_id,
            ip_address=ip_address,
            user_agent=user_agent
        )
        if dados:
            log_entry.dados = dados
        db.session.add(log_entry)
        db.session.commit()
        return log_entry
    
    def __repr__(self):
        return f'<LogAuditoria {self.acao} by user:{self.usuario_id} at {self.data_hora}>'
