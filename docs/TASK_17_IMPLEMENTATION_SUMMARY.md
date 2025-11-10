# Task 17: Security Middleware Implementation Summary

## Overview
Implemented comprehensive security middleware for the Sistema SGDI application, including authentication decorators, permission checking, security headers, CSRF protection, and rate limiting.

## Implementation Details

### 17.1 Authentication Middleware

**File:** `app/utils/decorators.py`

Implemented the following decorators:

1. **`@login_required`**
   - Validates user authentication
   - Checks account lock status
   - Validates account is active
   - Implements automatic session timeout
   - Updates last activity timestamp
   - Updates user's last access time periodically
   - Requirements: 1.1, 14.1

2. **`@admin_required`**
   - Requires Administrator role
   - Checks authentication first
   - Requirements: 5.1, 5.2, 5.3, 5.4, 5.5

3. **`@manager_or_admin_required`**
   - Requires Manager or Administrator role
   - Checks authentication first
   - Requirements: 5.1, 5.2, 5.3, 5.4, 5.5

**Key Features:**
- Session timeout validation using `PERMANENT_SESSION_LIFETIME` config
- Account lockout checking
- Active account validation
- Periodic last access time updates (every 5 minutes)
- User-friendly flash messages in Portuguese

### 17.2 Permission Checking Middleware

**Files:** 
- `app/utils/decorators.py` (decorators)
- `app/utils/middleware.py` (middleware and utilities)

#### Decorators

1. **`@permission_required(permission_type)`**
   - Checks role-based permissions at profile level
   - Validates user has specific permission
   - Requirements: 5.1, 5.2, 5.3, 5.4, 5.5

2. **`@document_permission_required(permission_type, document_id_param)`**
   - Validates resource-level permissions for documents
   - Checks if user is document owner
   - Checks explicit document permissions
   - Validates permission expiration
   - Handles deleted documents (only owner can access)
   - Requirements: 5.1, 5.2, 5.3, 5.4, 5.5

#### Middleware Class

**`PermissionMiddleware`**
- Runs before and after each request
- Stores request start time for performance monitoring
- Stores request IP address
- Stores current user info in Flask's `g` object
- Adds request duration header to responses

#### Utility Functions

1. **`check_document_permission(documento, user, permission_type)`**
   - Utility function for checking document permissions
   - Used by services and views
   - Checks owner, administrator, and explicit permissions

2. **`check_role_permission(user, permission_name)`**
   - Validates role-based access control (RBAC)
   - Defines permission mappings for each profile:
     - **Administrator**: All permissions
     - **Manager**: view, edit, delete, share, upload, approve, manage_workflows, view_reports
     - **Standard User**: view, edit, share, upload, create_folders
     - **Auditor**: view, audit, view_reports, view_logs
     - **Visitor**: view only

3. **`validate_resource_access(resource_type, resource_id, user, action)`**
   - Generic function for validating access to different resource types
   - Supports: document, workflow, user, category
   - Returns tuple: (has_access, error_message)

### 17.3 Security Headers and CSRF Protection

**File:** `app/utils/security.py`

#### Security Headers Middleware

**`SecurityHeaders`** class implements:
- **X-Frame-Options**: SAMEORIGIN (prevent clickjacking)
- **X-Content-Type-Options**: nosniff (prevent MIME sniffing)
- **X-XSS-Protection**: 1; mode=block (enable XSS filter)
- **Strict-Transport-Security**: Enforce HTTPS in production (31536000 seconds)
- **Content-Security-Policy**: Restrict resource loading
  - Allows self, CDN resources (Bootstrap, jQuery, DataTables)
  - Restricts script, style, image, font sources
  - Prevents frame embedding from other origins
- **Referrer-Policy**: strict-origin-when-cross-origin
- **Permissions-Policy**: Disable geolocation, microphone, camera

Requirements: 14.2, 14.3, 14.4, 14.5

#### Rate Limiting

**`RateLimiter`** class:
- Global rate limiting middleware
- Default: 100 requests per minute per IP
- Configurable via `RATE_LIMIT_PER_MINUTE` config
- In-memory storage (thread-safe with locks)
- Skips static files
- Returns 429 (Too Many Requests) when exceeded

**`@rate_limit(max_requests, window_seconds)`** decorator:
- Endpoint-specific rate limiting
- Customizable limits per endpoint
- Uses IP + endpoint as unique key

Requirements: 14.5

#### CSRF Protection

**`CSRFProtection`** class:
- Enhanced utilities for Flask-WTF CSRF
- `validate_csrf_token()`: Validates CSRF for AJAX requests
- `exempt_view()`: Decorator to exempt views from CSRF (use with caution)

Requirements: 14.4

#### Security Utilities

1. **`sanitize_input(text, allow_html=False)`**
   - Prevents XSS attacks
   - Escapes HTML by default
   - Optional: Allow safe HTML tags using bleach
   - Requirements: 14.3

2. **`validate_sql_input(text)`**
   - Secondary defense against SQL injection
   - Checks for dangerous SQL patterns
   - Primary defense: SQLAlchemy parameterized queries
   - Requirements: 14.2

3. **`secure_filename(filename)`**
   - Removes dangerous characters from filenames
   - Uses werkzeug's secure_filename
   - Additional sanitization with regex

4. **`generate_secure_token(length=32)`**
   - Generates cryptographically secure random tokens
   - Uses secrets module

5. **`validate_password_strength(password)`**
   - Validates password requirements:
     - At least 8 characters
     - Contains uppercase letter
     - Contains lowercase letter
     - Contains digit
     - Contains special character
   - Returns tuple: (is_valid, error_message)

## Configuration Changes

**File:** `config.py`

Added:
```python
# Rate Limiting
RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', 100))
```

## Application Integration

**File:** `app/__init__.py`

Integrated security middleware in `create_app()`:
```python
# Initialize security middleware
from app.utils.security import SecurityHeaders, RateLimiter
from app.utils.middleware import PermissionMiddleware

SecurityHeaders(app)
RateLimiter(app, requests_per_minute=app.config.get('RATE_LIMIT_PER_MINUTE', 100))
PermissionMiddleware(app)
```

## Error Handling

**File:** `app/errors/__init__.py`

Added 429 error handler:
```python
@app.errorhandler(429)
def too_many_requests_error(error):
    return render_template('errors/429.html'), 429
```

**File:** `app/templates/errors/429.html`

Created user-friendly error page for rate limit exceeded.

## Exports

**File:** `app/utils/__init__.py`

Exported all security components for easy import:
- Decorators: `login_required`, `permission_required`, `document_permission_required`, `admin_required`, `manager_or_admin_required`
- Security: `SecurityHeaders`, `RateLimiter`, `CSRFProtection`, `rate_limit`, `sanitize_input`, `validate_sql_input`, `secure_filename`, `generate_secure_token`, `validate_password_strength`
- Middleware: `PermissionMiddleware`, `check_document_permission`, `check_role_permission`, `validate_resource_access`

## Usage Examples

### Using Authentication Decorator

```python
from app.utils import login_required

@document_bp.route('/list')
@login_required
def list_documents():
    # Only authenticated users can access
    pass
```

### Using Permission Decorator

```python
from app.utils import permission_required

@admin_bp.route('/users')
@permission_required('manage_users')
def manage_users():
    # Only users with 'manage_users' permission can access
    pass
```

### Using Document Permission Decorator

```python
from app.utils import document_permission_required

@document_bp.route('/<int:document_id>/edit')
@document_permission_required('editar', document_id_param='document_id')
def edit_document(document_id):
    # Only users with 'editar' permission on this document can access
    pass
```

### Using Admin Decorator

```python
from app.utils import admin_required

@admin_bp.route('/settings')
@admin_required
def system_settings():
    # Only administrators can access
    pass
```

### Using Rate Limit Decorator

```python
from app.utils import rate_limit

@auth_bp.route('/login', methods=['POST'])
@rate_limit(max_requests=5, window_seconds=60)
def login():
    # Limited to 5 login attempts per minute
    pass
```

### Checking Permissions in Code

```python
from app.utils import check_document_permission, check_role_permission

# Check document permission
if check_document_permission(documento, current_user, 'visualizar'):
    # User can view document
    pass

# Check role permission
if check_role_permission(current_user, 'approve'):
    # User can approve documents
    pass
```

### Validating Resource Access

```python
from app.utils import validate_resource_access

has_access, error_msg = validate_resource_access(
    'document', 
    document_id, 
    current_user, 
    'edit'
)

if not has_access:
    flash(error_msg, 'danger')
    abort(403)
```

## Security Features Summary

### Authentication Security
✅ Session validation and timeout  
✅ Account lockout checking  
✅ Active account validation  
✅ Last access tracking  

### Authorization Security
✅ Role-based access control (RBAC)  
✅ Resource-level permissions  
✅ Document ownership validation  
✅ Permission expiration checking  

### Application Security
✅ Security headers (X-Frame-Options, CSP, HSTS, etc.)  
✅ CSRF protection  
✅ Rate limiting (global and per-endpoint)  
✅ XSS prevention (input sanitization)  
✅ SQL injection prevention (input validation)  

### Password Security
✅ Password strength validation  
✅ Secure password hashing (bcrypt)  
✅ Secure token generation  

## Requirements Fulfilled

- ✅ **1.1**: User authentication with session management
- ✅ **5.1**: Owner-based permission inheritance
- ✅ **5.2**: Permission granting functionality
- ✅ **5.3**: Permission validation before operations
- ✅ **5.4**: Role-based access control (RBAC)
- ✅ **5.5**: Appropriate error messages for permission denial
- ✅ **14.1**: HTTPS enforcement (Strict-Transport-Security header)
- ✅ **14.2**: SQL injection prevention
- ✅ **14.3**: XSS attack prevention
- ✅ **14.4**: CSRF attack prevention
- ✅ **14.5**: Rate limiting (100 requests/minute per IP)

## Testing Recommendations

1. **Authentication Tests**
   - Test session timeout
   - Test account lockout
   - Test inactive account blocking

2. **Permission Tests**
   - Test role-based permissions
   - Test document-level permissions
   - Test permission expiration
   - Test owner vs non-owner access

3. **Security Tests**
   - Test rate limiting (exceed limits)
   - Test CSRF protection
   - Test XSS prevention (inject scripts)
   - Test SQL injection prevention
   - Verify security headers in responses

4. **Integration Tests**
   - Test decorator combinations
   - Test middleware execution order
   - Test error handling

## Notes

- Rate limiting uses in-memory storage. For production with multiple workers, consider using Redis.
- Security headers are configured for common CDNs (Bootstrap, jQuery, DataTables). Update CSP if adding new external resources.
- CSRF protection is enabled globally via Flask-WTF. Use `@csrf.exempt` decorator for API endpoints if needed.
- Session timeout is configured via `PERMANENT_SESSION_LIFETIME` in config (default: 1 hour).
- All user-facing messages are in Portuguese (Brazilian).

## Next Steps

To use the security middleware in existing routes:

1. Replace Flask-Login's `@login_required` with our custom `@login_required` decorator
2. Add `@permission_required()` or `@document_permission_required()` decorators to protected routes
3. Use `@admin_required` or `@manager_or_admin_required` for admin routes
4. Add `@rate_limit()` decorator to sensitive endpoints (login, password reset, etc.)
5. Test all protected routes to ensure proper access control

## Files Created/Modified

### Created:
- `app/utils/decorators.py` - Authentication and permission decorators
- `app/utils/middleware.py` - Permission middleware and utilities
- `app/utils/security.py` - Security headers, rate limiting, CSRF utilities
- `app/templates/errors/429.html` - Rate limit error page
- `docs/TASK_17_IMPLEMENTATION_SUMMARY.md` - This documentation

### Modified:
- `app/__init__.py` - Integrated security middleware
- `app/utils/__init__.py` - Exported security components
- `app/errors/__init__.py` - Added 429 error handler
- `config.py` - Added rate limit configuration

## Conclusion

Task 17 has been successfully completed. The Sistema SGDI application now has comprehensive security middleware including:
- Robust authentication with session management
- Fine-grained permission checking (role-based and resource-level)
- Security headers to prevent common web attacks
- Rate limiting to prevent abuse
- CSRF protection for all forms
- Input sanitization and validation utilities

All requirements (1.1, 5.1-5.5, 14.1-14.5) have been fulfilled.
