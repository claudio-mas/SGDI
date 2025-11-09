"""
Version model
"""
from datetime import datetime
from app import db


class Versao(db.Model):
    """Document version model"""
    __tablename__ = 'versoes'
    
    id = db.Column(db.Integer, primary_key=True)
    documento_id = db.Column(db.Integer, db.ForeignKey('documentos.id', ondelete='CASCADE'), nullable=False, index=True)
    numero_versao = db.Column(db.Integer, nullable=False)
    caminho_arquivo = db.Column(db.String(500), nullable=False)
    tamanho_bytes = db.Column(db.BigInteger, nullable=False)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    comentario = db.Column(db.Text, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Relationship
    usuario = db.relationship('User', backref='versoes_criadas', lazy='joined')
    
    __table_args__ = (
        db.UniqueConstraint('documento_id', 'numero_versao', name='uq_documento_versao'),
    )
    
    @property
    def tamanho_formatado(self):
        """Get human-readable file size"""
        size = self.tamanho_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def __repr__(self):
        return f'<Versao doc:{self.documento_id} v{self.numero_versao}>'
