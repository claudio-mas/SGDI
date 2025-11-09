"""
Permission model
"""
from datetime import datetime
from app import db


class Permissao(db.Model):
    """Document permission model"""
    __tablename__ = 'permissoes'
    
    id = db.Column(db.Integer, primary_key=True)
    documento_id = db.Column(db.Integer, db.ForeignKey('documentos.id', ondelete='CASCADE'), nullable=False, index=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    tipo_permissao = db.Column(db.String(20), nullable=False)  # visualizar, editar, excluir, compartilhar
    data_concessao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    concedido_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    data_expiracao = db.Column(db.DateTime)  # Optional expiration date for shared access
    
    # Relationships
    concedente = db.relationship('User', foreign_keys=[concedido_por], backref='permissoes_concedidas')
    
    __table_args__ = (
        db.UniqueConstraint('documento_id', 'usuario_id', 'tipo_permissao', name='uq_documento_usuario_permissao'),
        db.Index('idx_permissao_documento_usuario', 'documento_id', 'usuario_id'),
    )
    
    def is_expired(self):
        """Check if permission has expired"""
        if self.data_expiracao:
            return self.data_expiracao < datetime.utcnow()
        return False
    
    def __repr__(self):
        return f'<Permissao doc:{self.documento_id} user:{self.usuario_id} tipo:{self.tipo_permissao}>'
