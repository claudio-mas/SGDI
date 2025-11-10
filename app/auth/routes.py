"""
Authentication routes
"""
from flask import render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user, logout_user
from app.auth import auth_bp
from app.auth.forms import (
    LoginForm, PasswordResetRequestForm, PasswordResetForm,
    ChangePasswordForm, ProfileEditForm
)
from app.services.auth_service import AuthService
from app import db


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """
    Login page and handler
    Requirements: 1.1, 1.2
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('documents.list_documents'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        auth_service = AuthService()
        
        # Get IP address for audit logging
        ip_address = request.remote_addr
        
        # Attempt login
        success, message, user = auth_service.login(
            email=form.email.data,
            password=form.password.data,
            ip_address=ip_address,
            remember=form.remember_me.data
        )
        
        if success:
            # flash(message, 'success')
            
            # Redirect to next page or dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for('documents.list_documents'))
        else:
            flash(message, 'danger')
    
    return render_template('auth/login.html', form=form)


@auth_bp.route('/logout')
def logout():
    """
    Logout route
    Requirements: 1.1
    """
    auth_service = AuthService()
    
    # Get user ID before logout
    user_id = current_user.id if current_user.is_authenticated else None
    
    # Perform logout
    success, message = auth_service.logout(user_id)
    
    # flash('Você saiu do sistema com sucesso.', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/register')
def register():
    """Registration page"""
    return "Register page - To be implemented"


@auth_bp.route('/reset-password', methods=['GET', 'POST'])
@auth_bp.route('/reset-password-request', methods=['GET', 'POST'])
def reset_password_request():
    """
    Password reset request page
    Requirements: 1.3
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('documents.list_documents'))
    
    form = PasswordResetRequestForm()
    
    if form.validate_on_submit():
        auth_service = AuthService()
        
        # Request password reset
        success, message, token = auth_service.request_password_reset(form.email.data)
        
        if success and token:
            # Send password reset email
            user = auth_service.get_user_by_email(form.email.data)
            if user:
                from app.services.notification_service import NotificationService
                notification_service = NotificationService()
                notification_service.send_password_reset_email(user, token)
            
            flash('Um link de recuperação foi enviado para o seu email.', 'info')
        else:
            # Always show success message for security (don't reveal if email exists)
            flash('Se o email existir, um link de recuperação será enviado.', 'info')
        
        return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', form=form)


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    """
    Password reset confirmation page
    Requirements: 1.3
    """
    # Redirect if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('documents.list_documents'))
    
    auth_service = AuthService()
    
    # Validate token
    valid, message, user = auth_service.validate_reset_token(token)
    
    if not valid:
        flash(message, 'danger')
        return redirect(url_for('auth.reset_password_request'))
    
    form = PasswordResetForm()
    
    if form.validate_on_submit():
        # Reset password
        success, message = auth_service.reset_password(token, form.password.data)
        
        if success:
            flash('Senha redefinida com sucesso. Você já pode fazer login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash(message, 'danger')
    
    return render_template('auth/reset_password.html', form=form, token=token)


@auth_bp.route('/profile')
@login_required
def profile():
    """
    User profile view page
    Requirements: 1.1
    """
    return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """
    User profile edit page
    Requirements: 1.1
    """
    form = ProfileEditForm(original_email=current_user.email)
    
    if form.validate_on_submit():
        # Update user profile
        current_user.nome = form.nome.data
        current_user.email = form.email.data
        
        try:
            db.session.commit()
            flash('Perfil atualizado com sucesso.', 'success')
            return redirect(url_for('auth.profile'))
        except Exception as e:
            db.session.rollback()
            flash('Erro ao atualizar perfil. Tente novamente.', 'danger')
    
    # Pre-populate form with current data
    if request.method == 'GET':
        form.nome.data = current_user.nome
        form.email.data = current_user.email
    
    return render_template('auth/edit_profile.html', form=form)


@auth_bp.route('/profile/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """
    Password change page
    Requirements: 1.1
    """
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        auth_service = AuthService()
        
        # Change password
        success, message = auth_service.change_password(
            user_id=current_user.id,
            current_password=form.current_password.data,
            new_password=form.new_password.data
        )
        
        if success:
            flash('Senha alterada com sucesso.', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash(message, 'danger')
    
    return render_template('auth/change_password.html', form=form)
