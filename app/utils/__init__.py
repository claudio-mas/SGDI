"""
Utility functions and helpers
"""
from app.utils.file_handler import (
    FileHandler,
    FileValidationError,
    InvalidFileTypeError,
    FileSizeExceededError
)
from app.utils.decorators import (
    login_required,
    permission_required,
    document_permission_required,
    admin_required,
    manager_or_admin_required
)
from app.utils.security import (
    SecurityHeaders,
    RateLimiter,
    CSRFProtection,
    rate_limit,
    sanitize_input,
    validate_sql_input,
    secure_filename,
    generate_secure_token,
    validate_password_strength
)
from app.utils.middleware import (
    PermissionMiddleware,
    check_document_permission,
    check_role_permission,
    validate_resource_access
)

__all__ = [
    'FileHandler',
    'FileValidationError',
    'InvalidFileTypeError',
    'FileSizeExceededError',
    'login_required',
    'permission_required',
    'document_permission_required',
    'admin_required',
    'manager_or_admin_required',
    'SecurityHeaders',
    'RateLimiter',
    'CSRFProtection',
    'rate_limit',
    'sanitize_input',
    'validate_sql_input',
    'secure_filename',
    'generate_secure_token',
    'validate_password_strength',
    'PermissionMiddleware',
    'check_document_permission',
    'check_role_permission',
    'validate_resource_access'
]
