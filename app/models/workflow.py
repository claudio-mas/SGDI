"""
Workflow-related models
"""
from datetime import datetime
from app import db
import json


class Workflow(db.Model):
    """Workflow template model with JSON configuration"""
    __tablename__ = 'workflows'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    descricao = db.Column(db.Text)
    configuracao_json = db.Column(db.Text, nullable=False)  # JSON with workflow stages and approvers
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    criado_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    
    # Relationships
    criador = db.relationship('User', backref='workflows_criados')
    aprovacoes = db.relationship('AprovacaoDocumento', backref='workflow', lazy='dynamic')
    
    @property
    def configuracao(self):
        """Get workflow configuration as dict"""
        return json.loads(self.configuracao_json) if self.configuracao_json else {}
    
    @configuracao.setter
    def configuracao(self, config_dict):
        """Set workflow configuration from dict"""
        self.configuracao_json = json.dumps(config_dict)
    
    def __repr__(self):
        return f'<Workflow {self.nome}>'


class AprovacaoDocumento(db.Model):
    """Document approval instance model"""
    __tablename__ = 'aprovacao_documentos'
    
    id = db.Column(db.Integer, primary_key=True)
    documento_id = db.Column(db.Integer, db.ForeignKey('documentos.id', ondelete='CASCADE'), nullable=False, index=True)
    workflow_id = db.Column(db.Integer, db.ForeignKey('workflows.id'), nullable=False)
    submetido_por = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    estagio_atual = db.Column(db.Integer, default=1, nullable=False)  # Current approval stage
    status = db.Column(db.String(20), default='pendente', nullable=False)  # pendente, aprovado, rejeitado
    data_submissao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    data_conclusao = db.Column(db.DateTime)
    
    # Relationships
    submissor = db.relationship('User', foreign_keys=[submetido_por], backref='aprovacoes_submetidas')
    historico = db.relationship('HistoricoAprovacao', backref='aprovacao', lazy='dynamic', cascade='all, delete-orphan', order_by='HistoricoAprovacao.data_acao')
    
    def __repr__(self):
        return f'<AprovacaoDocumento doc:{self.documento_id} status:{self.status}>'


class HistoricoAprovacao(db.Model):
    """Approval history model"""
    __tablename__ = 'historico_aprovacoes'
    
    id = db.Column(db.Integer, primary_key=True)
    aprovacao_id = db.Column(db.Integer, db.ForeignKey('aprovacao_documentos.id', ondelete='CASCADE'), nullable=False, index=True)
    estagio = db.Column(db.Integer, nullable=False)
    aprovador_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    acao = db.Column(db.String(20), nullable=False)  # aprovado, rejeitado
    comentario = db.Column(db.Text, nullable=False)
    data_acao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    aprovador = db.relationship('User', backref='acoes_aprovacao')
    
    def __repr__(self):
        return f'<HistoricoAprovacao aprovacao:{self.aprovacao_id} acao:{self.acao}>'
