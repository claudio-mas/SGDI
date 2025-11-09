"""
Authentication forms using Flask-WTF
"""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from app.models.user import User


class LoginForm(FlaskForm):
    """Login form with email and password"""
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido')
    ])
    password = PasswordField('Senha', validators=[
        DataRequired(message='Senha é obrigatória')
    ])
    remember_me = BooleanField('Lembrar-me')
    submit = SubmitField('Entrar')


class PasswordResetRequestForm(FlaskForm):
    """Form to request password reset"""
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido')
    ])
    submit = SubmitField('Enviar Link de Recuperação')


class PasswordResetForm(FlaskForm):
    """Form to reset password with token"""
    password = PasswordField('Nova Senha', validators=[
        DataRequired(message='Senha é obrigatória'),
        Length(min=8, message='Senha deve ter no mínimo 8 caracteres')
    ])
    password_confirm = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(message='Confirmação de senha é obrigatória'),
        EqualTo('password', message='As senhas devem ser iguais')
    ])
    submit = SubmitField('Redefinir Senha')


class ChangePasswordForm(FlaskForm):
    """Form to change password (requires current password)"""
    current_password = PasswordField('Senha Atual', validators=[
        DataRequired(message='Senha atual é obrigatória')
    ])
    new_password = PasswordField('Nova Senha', validators=[
        DataRequired(message='Nova senha é obrigatória'),
        Length(min=8, message='Senha deve ter no mínimo 8 caracteres')
    ])
    new_password_confirm = PasswordField('Confirmar Nova Senha', validators=[
        DataRequired(message='Confirmação de senha é obrigatória'),
        EqualTo('new_password', message='As senhas devem ser iguais')
    ])
    submit = SubmitField('Alterar Senha')


class ProfileEditForm(FlaskForm):
    """Form to edit user profile"""
    nome = StringField('Nome Completo', validators=[
        DataRequired(message='Nome é obrigatório'),
        Length(min=3, max=100, message='Nome deve ter entre 3 e 100 caracteres')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email é obrigatório'),
        Email(message='Email inválido')
    ])
    submit = SubmitField('Salvar Alterações')
    
    def __init__(self, original_email, *args, **kwargs):
        super(ProfileEditForm, self).__init__(*args, **kwargs)
        self.original_email = original_email
    
    def validate_email(self, field):
        """Check if email is already taken by another user"""
        if field.data != self.original_email:
            user = User.query.filter_by(email=field.data).first()
            if user:
                raise ValidationError('Este email já está em uso.')
