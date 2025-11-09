"""
User-related models
"""
from datetime import datetime, timedelta
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import secrets


class Perfil(db.Model):
    """User profile/role model"""
    __tablename__ = 'perfis'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(50), unique=True, nullable=False)
    descricao = db.Column(db.Text)
    
    # Relationships
    usuarios = db.relationship('User', backref='perfil', lazy='dynamic')
    
    def __repr__(self):
        return f'<Perfil {self.nome}>'


class User(UserMixin, db.Model):
    """User model with authentication support"""
    __tablename__ = 'usuarios'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    senha_hash = db.Column(db.String(255), nullable=False)
    perfil_id = db.Column(db.Integer, db.ForeignKey('perfis.id'), nullable=False)
    ativo = db.Column(db.Boolean, default=True, nullable=False)
    tentativas_login = db.Column(db.Integer, default=0, nullable=False)
    bloqueado_ate = db.Column(db.DateTime)
    ultimo_acesso = db.Column(db.DateTime)
    data_cadastro = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    documentos = db.relationship('Documento', backref='usuario', lazy='dynamic', foreign_keys='Documento.usuario_id')
    permissoes = db.relationship('Permissao', backref='usuario', lazy='dynamic')
    password_resets = db.relationship('PasswordReset', backref='usuario', lazy='dynamic')
    
    def set_password(self, password):
        """Hash and set user password"""
        self.senha_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Verify password against hash"""
        return check_password_hash(self.senha_hash, password)
    
    def has_permission(self, permission_name):
        """Check if user has specific permission based on profile"""
        # This will be expanded based on profile permissions
        if not self.ativo:
            return False
        
        # Administrator has all permissions
        if self.perfil.nome == 'Administrator':
            return True
        
        # Define permission mappings for each profile
        profile_permissions = {
            'Manager': ['view', 'edit', 'delete', 'share', 'approve', 'manage_users'],
            'Standard User': ['view', 'edit', 'share', 'upload'],
            'Auditor': ['view', 'audit'],
            'Visitor': ['view']
        }
        
        return permission_name in profile_permissions.get(self.perfil.nome, [])
    
    def is_account_locked(self):
        """Check if account is currently locked"""
        if self.bloqueado_ate and self.bloqueado_ate > datetime.utcnow():
            return True
        return False
    
    def lock_account(self, duration_seconds=900):
        """Lock account for specified duration (default 15 minutes)"""
        self.bloqueado_ate = datetime.utcnow() + timedelta(seconds=duration_seconds)
        db.session.commit()
    
    def unlock_account(self):
        """Unlock account and reset login attempts"""
        self.bloqueado_ate = None
        self.tentativas_login = 0
        db.session.commit()
    
    def increment_login_attempts(self):
        """Increment failed login attempts"""
        self.tentativas_login += 1
        db.session.commit()
    
    def reset_login_attempts(self):
        """Reset login attempts counter"""
        self.tentativas_login = 0
        db.session.commit()
    
    def __repr__(self):
        return f'<User {self.email}>'


class PasswordReset(db.Model):
    """Password reset token model"""
    __tablename__ = 'password_resets'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id'), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False, index=True)
    expiracao = db.Column(db.DateTime, nullable=False)
    usado = db.Column(db.Boolean, default=False, nullable=False)
    data_criacao = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    @staticmethod
    def generate_token():
        """Generate secure random token"""
        return secrets.token_urlsafe(32)
    
    def is_valid(self):
        """Check if token is valid (not expired and not used)"""
        return not self.usado and self.expiracao > datetime.utcnow()
    
    def mark_as_used(self):
        """Mark token as used"""
        self.usado = True
        db.session.commit()
    
    def __repr__(self):
        return f'<PasswordReset {self.token[:10]}...>'


@login_manager.user_loader
def load_user(user_id):
    """Load user by ID for Flask-Login"""
    return User.query.get(int(user_id))
