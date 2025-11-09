"""
Authentication service for user authentication, session management, and password operations.
Implements brute-force protection, account lockout, and secure password reset functionality.
"""
from typing import Optional, Tuple, Dict, Any
from datetime import datetime, timedelta
from flask import current_app, session
from flask_login import login_user, logout_user
import re

from app import db
from app.models.user import User, PasswordReset
from app.repositories.user_repository import UserRepository, PasswordResetRepository, PerfilRepository


class AuthService:
    """
    Service for authentication and authorization operations.
    Handles login, logout, password management, and user registration.
    """
    
    def __init__(self):
        """Initialize AuthService with required repositories."""
        self.user_repo = UserRepository()
        self.password_reset_repo = PasswordResetRepository()
        self.perfil_repo = PerfilRepository()
    
    def login(self, email: str, password: str, ip_address: str = None, remember: bool = False) -> Tuple[bool, str, Optional[User]]:
        """
        Authenticate user with brute-force protection and account lockout.
        
        Args:
            email: User's email address
            password: Plain text password
            ip_address: IP address of login attempt (for audit logging)
            remember: Whether to remember the user session
            
        Returns:
            Tuple of (success: bool, message: str, user: Optional[User])
            
        Requirements: 1.1, 1.2, 1.4
        """
        # Find user by email
        user = self.user_repo.get_by_email(email)
        
        if not user:
            # Log failed login attempt for non-existent user
            try:
                from app.services.audit_service import AuditService
                audit_service = AuditService()
                audit_service.log_login(
                    usuario_id=None,
                    success=False,
                    email=email,
                    reason='User not found'
                )
            except Exception as e:
                print(f"Warning: Failed to log failed login audit entry: {e}")
            
            return False, "Invalid email or password", None
        
        # Check if account is locked
        if user.is_account_locked():
            remaining_time = (user.bloqueado_ate - datetime.utcnow()).total_seconds()
            minutes = int(remaining_time / 60)
            return False, f"Account is locked. Try again in {minutes} minutes.", None
        
        # Check if account is active
        if not user.ativo:
            return False, "Account is inactive. Please contact administrator.", None
        
        # Verify password
        if not user.check_password(password):
            # Increment failed login attempts
            user.increment_login_attempts()
            
            # Log failed login attempt
            try:
                from app.services.audit_service import AuditService
                audit_service = AuditService()
                audit_service.log_login(
                    usuario_id=user.id,
                    success=False,
                    email=email,
                    reason='Invalid password'
                )
            except Exception as e:
                print(f"Warning: Failed to log failed login audit entry: {e}")
            
            # Lock account if max attempts reached
            max_attempts = current_app.config.get('MAX_LOGIN_ATTEMPTS', 5)
            if user.tentativas_login >= max_attempts:
                lockout_duration = current_app.config.get('ACCOUNT_LOCKOUT_DURATION', 900)
                user.lock_account(lockout_duration)
                return False, f"Account locked due to too many failed attempts. Try again in 15 minutes.", None
            
            remaining_attempts = max_attempts - user.tentativas_login
            return False, f"Invalid email or password. {remaining_attempts} attempts remaining.", None
        
        # Successful login - reset attempts and update last access
        user.reset_login_attempts()
        user.ultimo_acesso = datetime.utcnow()
        db.session.commit()
        
        # Log user in with Flask-Login
        login_user(user, remember=remember)
        
        # Store additional session data
        session['user_id'] = user.id
        session['user_email'] = user.email
        session['login_time'] = datetime.utcnow().isoformat()
        if ip_address:
            session['ip_address'] = ip_address
        
        # Log successful login
        try:
            from app.services.audit_service import AuditService
            audit_service = AuditService()
            audit_service.log_login(usuario_id=user.id, success=True, email=email)
        except Exception as e:
            print(f"Warning: Failed to log login audit entry: {e}")
        
        return True, "Login successful", user
    
    def logout(self, user_id: Optional[int] = None) -> Tuple[bool, str]:
        """
        Log out user and clear session.
        
        Args:
            user_id: Optional user ID for logging purposes
            
        Returns:
            Tuple of (success: bool, message: str)
            
        Requirements: 1.1
        """
        # Log logout before clearing session
        if user_id:
            try:
                from app.services.audit_service import AuditService
                audit_service = AuditService()
                audit_service.log_logout(usuario_id=user_id)
            except Exception as e:
                print(f"Warning: Failed to log logout audit entry: {e}")
        
        # Clear Flask-Login session
        logout_user()
        
        # Clear custom session data
        session.clear()
        
        return True, "Logout successful"
    
    def is_session_valid(self, user_id: int) -> bool:
        """
        Validate if user session is still valid.
        Checks session timeout and user active status.
        
        Args:
            user_id: User ID to validate
            
        Returns:
            True if session is valid, False otherwise
            
        Requirements: 1.4
        """
        # Check if user exists and is active
        user = self.user_repo.get_by_id(user_id)
        if not user or not user.ativo:
            return False
        
        # Check if account is locked
        if user.is_account_locked():
            return False
        
        # Check session timeout
        login_time_str = session.get('login_time')
        if login_time_str:
            login_time = datetime.fromisoformat(login_time_str)
            session_lifetime = current_app.config.get('PERMANENT_SESSION_LIFETIME', timedelta(hours=1))
            if isinstance(session_lifetime, int):
                session_lifetime = timedelta(seconds=session_lifetime)
            
            if datetime.utcnow() - login_time > session_lifetime:
                return False
        
        return True
    
    def request_password_reset(self, email: str) -> Tuple[bool, str, Optional[str]]:
        """
        Generate password reset token and prepare for email sending.
        
        Args:
            email: User's email address
            
        Returns:
            Tuple of (success: bool, message: str, token: Optional[str])
            
        Requirements: 1.3
        """
        # Find user by email
        user = self.user_repo.get_by_email(email)
        
        if not user:
            # Don't reveal if email exists for security
            return True, "If the email exists, a reset link has been sent.", None
        
        if not user.ativo:
            return False, "Account is inactive. Please contact administrator.", None
        
        # Invalidate any existing tokens for this user
        self.password_reset_repo.invalidate_user_tokens(user.id)
        
        # Create new reset token
        expiration_hours = current_app.config.get('PASSWORD_RESET_TOKEN_EXPIRATION', 3600) / 3600
        reset = self.password_reset_repo.create_reset_token(user.id, int(expiration_hours))
        
        return True, "Password reset token generated", reset.token
    
    def validate_reset_token(self, token: str) -> Tuple[bool, str, Optional[User]]:
        """
        Validate password reset token.
        
        Args:
            token: Reset token to validate
            
        Returns:
            Tuple of (valid: bool, message: str, user: Optional[User])
            
        Requirements: 1.3
        """
        reset = self.password_reset_repo.get_valid_token(token)
        
        if not reset:
            return False, "Invalid or expired reset token", None
        
        user = self.user_repo.get_by_id(reset.usuario_id)
        
        if not user or not user.ativo:
            return False, "User account not found or inactive", None
        
        return True, "Token is valid", user
    
    def reset_password(self, token: str, new_password: str) -> Tuple[bool, str]:
        """
        Reset user password using valid token.
        
        Args:
            token: Password reset token
            new_password: New password (plain text)
            
        Returns:
            Tuple of (success: bool, message: str)
            
        Requirements: 1.3
        """
        # Validate password strength
        is_valid, validation_message = self.validate_password_strength(new_password)
        if not is_valid:
            return False, validation_message
        
        # Validate token
        valid, message, user = self.validate_reset_token(token)
        if not valid:
            return False, message
        
        # Get reset record
        reset = self.password_reset_repo.get_valid_token(token)
        
        # Update password
        user.set_password(new_password)
        user.tentativas_login = 0
        user.bloqueado_ate = None
        db.session.commit()
        
        # Mark token as used
        reset.mark_as_used()
        
        return True, "Password reset successful"
    
    def change_password(self, user_id: int, current_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Change user password (requires current password verification).
        
        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            Tuple of (success: bool, message: str)
            
        Requirements: 1.3
        """
        user = self.user_repo.get_by_id(user_id)
        
        if not user:
            return False, "User not found"
        
        # Verify current password
        if not user.check_password(current_password):
            return False, "Current password is incorrect"
        
        # Validate new password strength
        is_valid, validation_message = self.validate_password_strength(new_password)
        if not is_valid:
            return False, validation_message
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        return True, "Password changed successfully"
    
    def validate_password_strength(self, password: str) -> Tuple[bool, str]:
        """
        Validate password meets strength requirements.
        
        Requirements:
        - Minimum 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        
        Args:
            password: Password to validate
            
        Returns:
            Tuple of (valid: bool, message: str)
            
        Requirements: 1.3
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
        
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
        
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
        
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            return False, "Password must contain at least one special character"
        
        return True, "Password is strong"
    
    def register_user(self, nome: str, email: str, password: str, perfil_nome: str = 'Standard User') -> Tuple[bool, str, Optional[User]]:
        """
        Register a new user with email validation and default profile assignment.
        
        Args:
            nome: User's full name
            email: User's email address
            password: Plain text password
            perfil_nome: Profile name (default: 'Standard User')
            
        Returns:
            Tuple of (success: bool, message: str, user: Optional[User])
            
        Requirements: 1.1, 1.5
        """
        # Validate email format
        if not self.validate_email(email):
            return False, "Invalid email format", None
        
        # Check if email is already taken
        if self.user_repo.is_email_taken(email):
            return False, "Email address is already registered", None
        
        # Validate password strength
        is_valid, validation_message = self.validate_password_strength(password)
        if not is_valid:
            return False, validation_message, None
        
        # Get profile
        perfil = self.perfil_repo.get_by_name(perfil_nome)
        if not perfil:
            # Fallback to default profile
            perfil = self.perfil_repo.get_default_profile()
            if not perfil:
                return False, "Default user profile not found. Please contact administrator.", None
        
        # Create user
        try:
            user = self.user_repo.create(
                nome=nome,
                email=email,
                perfil_id=perfil.id,
                ativo=True,
                tentativas_login=0
            )
            
            # Set password (hashed)
            user.set_password(password)
            db.session.commit()
            
            return True, "User registered successfully", user
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error registering user: {str(e)}")
            return False, "An error occurred during registration", None
    
    def validate_email(self, email: str) -> bool:
        """
        Validate email format using regex.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if valid, False otherwise
            
        Requirements: 1.1
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.
        
        Args:
            user_id: User ID
            
        Returns:
            User instance or None
        """
        return self.user_repo.get_by_id(user_id)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email.
        
        Args:
            email: User email
            
        Returns:
            User instance or None
        """
        return self.user_repo.get_by_email(email)
    
    def unlock_expired_accounts(self) -> int:
        """
        Unlock all accounts whose lock period has expired.
        This should be called periodically (e.g., via cron job).
        
        Returns:
            Number of accounts unlocked
            
        Requirements: 1.2
        """
        return self.user_repo.unlock_expired_accounts()
