"""
User repository with authentication and user management queries
"""
from typing import Optional, List
from datetime import datetime, timedelta
from app.repositories.base_repository import BaseRepository
from app.models.user import User, Perfil, PasswordReset


class UserRepository(BaseRepository[User]):
    """
    Repository for User model with specialized authentication queries.
    Handles user lookup, authentication, and account management operations.
    """
    
    def __init__(self):
        """Initialize UserRepository with User model."""
        super().__init__(User)
    
    def get_by_email(self, email: str) -> Optional[User]:
        """
        Find user by email address.
        
        Args:
            email: User's email address
            
        Returns:
            User instance or None if not found
        """
        return self.get_one_by(email=email)
    
    def get_active_users(self) -> List[User]:
        """
        Get all active users.
        
        Returns:
            List of active User instances
        """
        return self.filter_by(ativo=True)
    
    def get_by_profile(self, perfil_id: int) -> List[User]:
        """
        Get all users with a specific profile/role.
        
        Args:
            perfil_id: Profile ID
            
        Returns:
            List of User instances
        """
        return self.filter_by(perfil_id=perfil_id)
    
    def authenticate(self, email: str, password: str) -> Optional[User]:
        """
        Authenticate user by email and password.
        Does not check account lock status - use is_account_locked() separately.
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            User instance if credentials are valid, None otherwise
        """
        user = self.get_by_email(email)
        if user and user.check_password(password):
            return user
        return None
    
    def is_email_taken(self, email: str, exclude_user_id: Optional[int] = None) -> bool:
        """
        Check if email is already in use.
        
        Args:
            email: Email address to check
            exclude_user_id: Optional user ID to exclude from check (for updates)
            
        Returns:
            True if email is taken, False otherwise
        """
        query = self.get_query().filter(User.email == email)
        if exclude_user_id:
            query = query.filter(User.id != exclude_user_id)
        return query.count() > 0
    
    def get_locked_accounts(self) -> List[User]:
        """
        Get all currently locked accounts.
        
        Returns:
            List of User instances with active locks
        """
        now = datetime.utcnow()
        return self.get_query().filter(
            User.bloqueado_ate.isnot(None),
            User.bloqueado_ate > now
        ).all()
    
    def unlock_expired_accounts(self) -> int:
        """
        Unlock all accounts whose lock period has expired.
        
        Returns:
            Number of accounts unlocked
        """
        now = datetime.utcnow()
        count = self.get_query().filter(
            User.bloqueado_ate.isnot(None),
            User.bloqueado_ate <= now
        ).update({
            'bloqueado_ate': None,
            'tentativas_login': 0
        }, synchronize_session=False)
        self.session.commit()
        return count
    
    def update_last_access(self, user_id: int) -> bool:
        """
        Update user's last access timestamp.
        
        Args:
            user_id: User ID
            
        Returns:
            True if updated, False if user not found
        """
        user = self.get_by_id(user_id)
        if user:
            user.ultimo_acesso = datetime.utcnow()
            self.session.commit()
            return True
        return False
    
    def search_users(self, query: str, active_only: bool = True) -> List[User]:
        """
        Search users by name or email.
        
        Args:
            query: Search term
            active_only: If True, only return active users
            
        Returns:
            List of matching User instances
        """
        search_filter = self.get_query().filter(
            (User.nome.ilike(f'%{query}%')) | (User.email.ilike(f'%{query}%'))
        )
        if active_only:
            search_filter = search_filter.filter(User.ativo == True)
        return search_filter.all()


class PerfilRepository(BaseRepository[Perfil]):
    """
    Repository for Perfil (Profile/Role) model.
    """
    
    def __init__(self):
        """Initialize PerfilRepository with Perfil model."""
        super().__init__(Perfil)
    
    def get_by_name(self, nome: str) -> Optional[Perfil]:
        """
        Get profile by name.
        
        Args:
            nome: Profile name
            
        Returns:
            Perfil instance or None
        """
        return self.get_one_by(nome=nome)
    
    def get_default_profile(self) -> Optional[Perfil]:
        """
        Get the default profile for new users (Standard User).
        
        Returns:
            Perfil instance or None
        """
        return self.get_by_name('Standard User')


class PasswordResetRepository(BaseRepository[PasswordReset]):
    """
    Repository for PasswordReset model.
    Handles password reset token management.
    """
    
    def __init__(self):
        """Initialize PasswordResetRepository with PasswordReset model."""
        super().__init__(PasswordReset)
    
    def get_by_token(self, token: str) -> Optional[PasswordReset]:
        """
        Find password reset by token.
        
        Args:
            token: Reset token
            
        Returns:
            PasswordReset instance or None
        """
        return self.get_one_by(token=token)
    
    def get_valid_token(self, token: str) -> Optional[PasswordReset]:
        """
        Get valid (not expired, not used) password reset token.
        
        Args:
            token: Reset token
            
        Returns:
            PasswordReset instance if valid, None otherwise
        """
        reset = self.get_by_token(token)
        if reset and reset.is_valid():
            return reset
        return None
    
    def create_reset_token(self, usuario_id: int, expiration_hours: int = 1) -> PasswordReset:
        """
        Create a new password reset token for a user.
        
        Args:
            usuario_id: User ID
            expiration_hours: Hours until token expires (default 1)
            
        Returns:
            Created PasswordReset instance
        """
        token = PasswordReset.generate_token()
        expiracao = datetime.utcnow() + timedelta(hours=expiration_hours)
        
        return self.create(
            usuario_id=usuario_id,
            token=token,
            expiracao=expiracao,
            usado=False
        )
    
    def invalidate_user_tokens(self, usuario_id: int) -> int:
        """
        Invalidate all unused tokens for a user.
        
        Args:
            usuario_id: User ID
            
        Returns:
            Number of tokens invalidated
        """
        count = self.get_query().filter(
            PasswordReset.usuario_id == usuario_id,
            PasswordReset.usado == False
        ).update({'usado': True}, synchronize_session=False)
        self.session.commit()
        return count
    
    def cleanup_expired_tokens(self, days_old: int = 7) -> int:
        """
        Delete expired tokens older than specified days.
        
        Args:
            days_old: Delete tokens older than this many days
            
        Returns:
            Number of tokens deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        count = self.get_query().filter(
            PasswordReset.expiracao < cutoff_date
        ).delete(synchronize_session=False)
        self.session.commit()
        return count
