"""
Security utilities including headers, CSRF protection, and rate limiting
"""
from flask import request, abort, g
from datetime import datetime, timedelta
from functools import wraps
from collections import defaultdict
import threading


# Rate limiting storage (in-memory, for production use Redis)
rate_limit_storage = defaultdict(list)
rate_limit_lock = threading.Lock()


class SecurityHeaders:
    """
    Middleware to add security headers to all responses.
    
    Implements security best practices including:
    - X-Frame-Options: Prevent clickjacking
    - X-Content-Type-Options: Prevent MIME sniffing
    - X-XSS-Protection: Enable XSS filter
    - Strict-Transport-Security: Enforce HTTPS
    - Content-Security-Policy: Restrict resource loading
    
    Requirements: 14.2, 14.3, 14.4, 14.5
    """
    
    def __init__(self, app=None):
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize security headers middleware with Flask app"""
        app.after_request(self.add_security_headers)
    
    def add_security_headers(self, response):
        """
        Add security headers to response.
        
        Requirements: 14.2, 14.3, 14.4, 14.5
        """
        # Prevent clickjacking attacks
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        
        # Prevent MIME type sniffing
        response.headers['X-Content-Type-Options'] = 'nosniff'
        
        # Enable XSS protection
        response.headers['X-XSS-Protection'] = '1; mode=block'
        
        # Enforce HTTPS in production
        from flask import current_app
        if not current_app.config.get('DEBUG', False):
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        
        # Content Security Policy
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://code.jquery.com https://cdn.datatables.net https://cdnjs.cloudflare.com",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdn.datatables.net https://cdnjs.cloudflare.com",
            "img-src 'self' data: https:",
            "font-src 'self' data: https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
            "connect-src 'self'",
            "frame-ancestors 'self'",
            "base-uri 'self'",
            "form-action 'self'"
        ]
        response.headers['Content-Security-Policy'] = '; '.join(csp_directives)
        
        # Referrer Policy
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions Policy (formerly Feature Policy)
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        return response


class RateLimiter:
    """
    Rate limiting middleware to prevent abuse.
    
    Implements rate limiting based on IP address to prevent:
    - Brute force attacks
    - DDoS attacks
    - API abuse
    
    Requirements: 14.5
    """
    
    def __init__(self, app=None, requests_per_minute=100):
        self.app = app
        self.requests_per_minute = requests_per_minute
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize rate limiter with Flask app"""
        self.requests_per_minute = app.config.get('RATE_LIMIT_PER_MINUTE', 100)
        app.before_request(self.check_rate_limit)
    
    def check_rate_limit(self):
        """
        Check if request exceeds rate limit.
        
        Requirements: 14.5
        """
        # Skip rate limiting for static files
        if request.endpoint and request.endpoint.startswith('static'):
            return
        
        # Get client IP address
        ip_address = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', 'unknown')
        
        # Get current time
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)
        
        with rate_limit_lock:
            # Clean old entries
            rate_limit_storage[ip_address] = [
                timestamp for timestamp in rate_limit_storage[ip_address]
                if timestamp > minute_ago
            ]
            
            # Check rate limit
            if len(rate_limit_storage[ip_address]) >= self.requests_per_minute:
                # Store rate limit info in g for logging
                g.rate_limited = True
                abort(429)  # Too Many Requests
            
            # Add current request
            rate_limit_storage[ip_address].append(now)


def rate_limit(max_requests=100, window_seconds=60):
    """
    Decorator for rate limiting specific endpoints.
    
    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
    
    Requirements: 14.5
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Get client IP address
            ip_address = request.remote_addr or request.environ.get('HTTP_X_FORWARDED_FOR', 'unknown')
            
            # Create unique key for this endpoint
            endpoint_key = f"{ip_address}:{request.endpoint}"
            
            # Get current time
            now = datetime.utcnow()
            window_start = now - timedelta(seconds=window_seconds)
            
            with rate_limit_lock:
                # Clean old entries
                rate_limit_storage[endpoint_key] = [
                    timestamp for timestamp in rate_limit_storage[endpoint_key]
                    if timestamp > window_start
                ]
                
                # Check rate limit
                if len(rate_limit_storage[endpoint_key]) >= max_requests:
                    abort(429)  # Too Many Requests
                
                # Add current request
                rate_limit_storage[endpoint_key].append(now)
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator


class CSRFProtection:
    """
    Enhanced CSRF protection utilities.
    
    Flask-WTF already provides CSRF protection, but this class adds
    additional utilities and validation.
    
    Requirements: 14.4
    """
    
    @staticmethod
    def validate_csrf_token():
        """
        Validate CSRF token for AJAX requests.
        
        This is used for AJAX requests that don't use WTForms.
        """
        from flask_wtf.csrf import validate_csrf
        
        # Get token from header or form data
        token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
        
        if not token:
            abort(400, description='CSRF token missing')
        
        try:
            validate_csrf(token)
        except Exception as e:
            abort(400, description='CSRF token invalid')
    
    @staticmethod
    def exempt_view(view_func):
        """
        Decorator to exempt a view from CSRF protection.
        
        Use with caution - only for specific API endpoints.
        """
        view_func.csrf_exempt = True
        return view_func


def sanitize_input(text, allow_html=False):
    """
    Sanitize user input to prevent XSS attacks.
    
    Args:
        text: Input text to sanitize
        allow_html: If True, allow safe HTML tags
    
    Returns:
        Sanitized text
    
    Requirements: 14.3
    """
    if not text:
        return text
    
    if allow_html:
        # Allow only safe HTML tags
        import bleach
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'a', 'ul', 'ol', 'li']
        allowed_attributes = {'a': ['href', 'title']}
        return bleach.clean(text, tags=allowed_tags, attributes=allowed_attributes, strip=True)
    else:
        # Escape all HTML
        from markupsafe import escape
        return escape(text)


def validate_sql_input(text):
    """
    Validate input to prevent SQL injection.
    
    Note: This is a secondary defense. Primary defense is using
    parameterized queries with SQLAlchemy.
    
    Args:
        text: Input text to validate
    
    Returns:
        bool: True if input is safe
    
    Requirements: 14.2
    """
    if not text:
        return True
    
    # Check for common SQL injection patterns
    dangerous_patterns = [
        '--', ';--', '/*', '*/', 'xp_', 'sp_', 'exec', 'execute',
        'union', 'select', 'insert', 'update', 'delete', 'drop',
        'create', 'alter', 'truncate'
    ]
    
    text_lower = text.lower()
    for pattern in dangerous_patterns:
        if pattern in text_lower:
            return False
    
    return True


def secure_filename(filename):
    """
    Secure a filename by removing dangerous characters.
    
    Args:
        filename: Original filename
    
    Returns:
        Secured filename
    """
    from werkzeug.utils import secure_filename as werkzeug_secure_filename
    import re
    
    # Use werkzeug's secure_filename
    filename = werkzeug_secure_filename(filename)
    
    # Additional sanitization
    filename = re.sub(r'[^\w\s\-\.]', '', filename)
    filename = re.sub(r'[\s]+', '_', filename)
    
    return filename


def generate_secure_token(length=32):
    """
    Generate a cryptographically secure random token.
    
    Args:
        length: Length of the token
    
    Returns:
        Secure random token
    """
    import secrets
    return secrets.token_urlsafe(length)


def hash_password(password):
    """
    Hash a password using bcrypt.
    
    Args:
        password: Plain text password
    
    Returns:
        Hashed password
    """
    from werkzeug.security import generate_password_hash
    return generate_password_hash(password, method='pbkdf2:sha256')


def verify_password(password_hash, password):
    """
    Verify a password against its hash.
    
    Args:
        password_hash: Hashed password
        password: Plain text password to verify
    
    Returns:
        bool: True if password matches
    """
    from werkzeug.security import check_password_hash
    return check_password_hash(password_hash, password)


def validate_password_strength(password):
    """
    Validate password strength.
    
    Requirements:
    - At least 8 characters
    - Contains uppercase letter
    - Contains lowercase letter
    - Contains digit
    - Contains special character
    
    Args:
        password: Password to validate
    
    Returns:
        tuple: (bool, str) - (is_valid, error_message)
    """
    import re
    
    if len(password) < 8:
        return False, 'A senha deve ter pelo menos 8 caracteres'
    
    if not re.search(r'[A-Z]', password):
        return False, 'A senha deve conter pelo menos uma letra maiúscula'
    
    if not re.search(r'[a-z]', password):
        return False, 'A senha deve conter pelo menos uma letra minúscula'
    
    if not re.search(r'\d', password):
        return False, 'A senha deve conter pelo menos um número'
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, 'A senha deve conter pelo menos um caractere especial'
    
    return True, None
