"""
Admin forms for user management and system settings
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Email, Length, Optional, NumberRange, ValidationError
from app.models import User
from app.repositories.user_repository import UserRepository


class UserCreateForm(FlaskForm):
    """Form for creating a new user"""
    nome = StringField('Nome', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=3, max=100, message='Nome deve ter entre 3 e 100 caracteres')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido'),
        Length(max=120)
    ])
    senha = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória'),
        Length(min=8, message='Senha deve ter no mínimo 8 caracteres')
    ])
    perfil_id = SelectField('Perfil', coerce=int, validators=[
        DataRequired(message='Perfil é obrigatório')
    ])
    ativo = BooleanField('Usuário Ativo', default=True)
    
    def validate_email(self, field):
        """Check if email is already in use"""
        user_repo = UserRepository()
        if user_repo.is_email_taken(field.data):
            raise ValidationError('Este email já está em uso.')


class UserEditForm(FlaskForm):
    """Form for editing an existing user"""
    nome = StringField('Nome', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=3, max=100, message='Nome deve ter entre 3 e 100 caracteres')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido'),
        Length(max=120)
    ])
    perfil_id = SelectField('Perfil', coerce=int, validators=[
        DataRequired(message='Perfil é obrigatório')
    ])
    ativo = BooleanField('Usuário Ativo')
    
    def __init__(self, user_id, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        self.user_id = user_id
    
    def validate_email(self, field):
        """Check if email is already in use by another user"""
        user_repo = UserRepository()
        if user_repo.is_email_taken(field.data, exclude_user_id=self.user_id):
            raise ValidationError('Este email já está em uso.')


class UserPasswordResetForm(FlaskForm):
    """Form for admin to reset user password"""
    nova_senha = PasswordField('Nova Senha', validators=[
        DataRequired(message='Nova senha é obrigatória'),
        Length(min=8, message='Senha deve ter no mínimo 8 caracteres')
    ])


class SystemSettingsForm(FlaskForm):
    """Form for system settings configuration"""
    max_file_size = IntegerField('Tamanho Máximo de Arquivo (MB)', validators=[
        DataRequired(message='Tamanho máximo é obrigatório'),
        NumberRange(min=1, max=500, message='Tamanho deve estar entre 1 e 500 MB')
    ])
    allowed_extensions = StringField('Extensões Permitidas', validators=[
        DataRequired(message='Extensões permitidas são obrigatórias'),
        Length(max=200)
    ], description='Separadas por vírgula (ex: pdf,doc,docx)')
    trash_retention_days = IntegerField('Dias de Retenção na Lixeira', validators=[
        DataRequired(message='Dias de retenção são obrigatórios'),
        NumberRange(min=1, max=365, message='Deve estar entre 1 e 365 dias')
    ])
    max_versions = IntegerField('Máximo de Versões por Documento', validators=[
        DataRequired(message='Máximo de versões é obrigatório'),
        NumberRange(min=1, max=50, message='Deve estar entre 1 e 50 versões')
    ])
    session_timeout = IntegerField('Timeout de Sessão (minutos)', validators=[
        DataRequired(message='Timeout de sessão é obrigatório'),
        NumberRange(min=5, max=1440, message='Deve estar entre 5 e 1440 minutos')
    ])
    logo = FileField('Logo do Sistema', validators=[
        FileAllowed(['jpg', 'jpeg', 'png'], 'Apenas imagens JPG e PNG são permitidas')
    ])
