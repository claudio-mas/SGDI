"""
Document-related models
"""
from datetime import datetime
from app import db


# Association table for many-to-many relationship between documents and tags
class DocumentoTag(db.Model):
    """Association table for Document-Tag relationship"""
    __tablename__ = 'documento_tags'
    
    id = db.Column(db.Integer, primary_key=True)
    documento_id = db.Column(db.Integer, db.ForeignKey('documentos.id'), nullable=False)
    tag_id = db.Column(db.Integer, db.ForeignKey('tags.id'), nullable=False)
    data_associacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    __table_args__ = (
        db.UniqueConstraint('documento_id', 'tag_id', name='uq_documento_tag'),
    )
    
    def __repr__(self):
        return f'<DocumentoTag doc:{self.documento_id} tag:{self.tag_id}>'


class Favorito(db.Model):
    """Favorito model for user's favorite documents"""
    __tablename__ = 'favoritos'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, 
        db.ForeignKey('usuarios.id'), 
        nullable=False, 
        index=True
    )
    documento_id = db.Column(
        db.Integer, 
        db.ForeignKey('documentos.id'), 
        nullable=False, 
        index=True
    )
    data_favoritado = db.Column(
        db.DateTime, 
        default=datetime.utcnow, 
        nullable=False
    )
    
    __table_args__ = (
        db.UniqueConstraint(
            'usuario_id', 
            'documento_id', 
            name='uq_usuario_documento_favorito'
        ),
    )
    
    def __repr__(self):
        return f'<Favorito user:{self.usuario_id} doc:{self.documento_id}>'


class Categoria(db.Model):
    """Category model with hierarchical structure"""
    __tablename__ = 'categorias'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    descricao = db.Column(db.Text)
    categoria_pai_id = db.Column(db.Integer, db.ForeignKey('categorias.id'))
    icone = db.Column(db.String(50))
    cor = db.Column(db.String(7))  # Hex color code
    ordem = db.Column(db.Integer, default=0)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    
    # Self-referential relationship for hierarchy
    subcategorias = db.relationship('Categoria', backref=db.backref('categoria_pai', remote_side=[id]), lazy='dynamic')
    
    # Relationship with documents
    documentos = db.relationship('Documento', backref='categoria', lazy='dynamic')
    
    @property
    def caminho_completo(self):
        """Get full hierarchical path of category"""
        if self.categoria_pai:
            return f"{self.categoria_pai.caminho_completo} > {self.nome}"
        return self.nome
    
    def __repr__(self):
        return f'<Categoria {self.nome}>'


class Pasta(db.Model):
    """Folder model with hierarchical structure"""
    __tablename__ = 'pastas'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text)
    pasta_pai_id = db.Column(db.Integer, db.ForeignKey('pastas.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    cor = db.Column(db.String(7))  # Hex color code
    ordem = db.Column(db.Integer, default=0)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Self-referential relationship for hierarchy
    subpastas = db.relationship('Pasta', backref=db.backref('pasta_pai', remote_side=[id]), lazy='dynamic')
    
    # Relationship with documents
    documentos = db.relationship('Documento', backref='pasta', lazy='dynamic')
    
    @property
    def caminho_completo(self):
        """Get full hierarchical path of folder"""
        if self.pasta_pai:
            return f"{self.pasta_pai.caminho_completo}/{self.nome}"
        return self.nome
    
    @property
    def nivel(self):
        """Get depth level in hierarchy"""
        if self.pasta_pai:
            return self.pasta_pai.nivel + 1
        return 0
    
    def __repr__(self):
        return f'<Pasta {self.nome}>'


class Tag(db.Model):
    """Tag model for document labeling"""
    __tablename__ = 'tags'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    
    # Many-to-many relationship with documents through association table
    documentos = db.relationship('Documento', secondary='documento_tags', backref=db.backref('tags', lazy='dynamic'))
    
    def __repr__(self):
        return f'<Tag {self.nome}>'


class Documento(db.Model):
    """Document model with metadata and relationships"""
    __tablename__ = 'documentos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text)
    caminho_arquivo = db.Column(db.String(500), nullable=False)
    nome_arquivo_original = db.Column(db.String(255), nullable=False)
    tamanho_bytes = db.Column(db.BigInteger, nullable=False)
    tipo_mime = db.Column(db.String(100), nullable=False)
    hash_arquivo = db.Column(db.String(64), nullable=False, index=True)  # SHA256
    
    # Foreign keys
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id'))
    pasta_id = db.Column(db.Integer, db.ForeignKey('pastas.id'))
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False, index=True)
    
    # Document state
    versao_atual = db.Column(db.Integer, default=1, nullable=False)
    status = db.Column(db.String(20), default='ativo', nullable=False, index=True)  # ativo, arquivado, excluido
    criptografado = db.Column(db.Boolean, default=False, nullable=False)
    
    # Timestamps
    data_upload = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    data_modificacao = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    data_exclusao = db.Column(db.DateTime)
    
    # Relationships
    versoes = db.relationship('Versao', backref='documento', lazy='dynamic', cascade='all, delete-orphan')
    permissoes = db.relationship('Permissao', backref='documento', lazy='dynamic', cascade='all, delete-orphan')
    aprovacoes = db.relationship('AprovacaoDocumento', backref='documento', lazy='dynamic', cascade='all, delete-orphan')
    favoritos = db.relationship('Favorito', backref='documento', lazy='dynamic', cascade='all, delete-orphan')
    
    def is_favorito_by(self, user_id):
        """Check if document is favorited by user"""
        return self.favoritos.filter_by(usuario_id=user_id).count() > 0
    
    @property
    def extensao(self):
        """Get file extension"""
        import os
        return os.path.splitext(self.nome_arquivo_original)[1].lower()
    
    @property
    def tamanho_formatado(self):
        """Get human-readable file size"""
        size = self.tamanho_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"
    
    def soft_delete(self):
        """Perform logical deletion"""
        self.status = 'excluido'
        self.data_exclusao = datetime.utcnow()
        db.session.commit()
    
    def restore(self):
        """Restore from trash"""
        self.status = 'ativo'
        self.data_exclusao = None
        db.session.commit()
    
    def __repr__(self):
        return f'<Documento {self.nome}>'
