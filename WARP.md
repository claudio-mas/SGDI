# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

SGDI (Gestão Eletrônica de Documentos) is a Flask-based document management system with SQL Server backend. It provides document upload, versioning, permissions, workflow approvals, full-text search, and audit logging for corporate environments.

**Tech Stack:**
- Backend: Flask 3.0+, SQLAlchemy, PyODBC
- Frontend: Bootstrap 5, jQuery, DataTables, Dropzone.js
- Database: SQL Server 2019+
- Production: Gunicorn, NGINX, Supervisor

## Development Commands

### Environment Setup

```powershell
# Windows - Create and activate virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
copy .env.example .env
# Edit .env with your database credentials
```

### Database Operations

```bash
# Initialize database with seed data (profiles, categories, admin user)
python init_db.py

# Initialize without seed data
python init_db.py --no-seed

# Seed data only (if tables already exist)
python seed_data.py
```

### Running the Application

```bash
# Development server (defaults to localhost:5000)
python run.py

# Production with Gunicorn
gunicorn -c gunicorn_config.py wsgi:app
```

### Testing

```bash
# Run all tests with coverage
python run_tests.py

# Run specific test suites
python run_tests.py e2e          # End-to-end tests
python run_tests.py security     # Security tests
python run_tests.py performance  # Performance tests

# Direct pytest usage
pytest tests/ -v
pytest tests/test_security.py -v
pytest tests/ -v --cov=app --cov-report=html
```

### Maintenance Scripts

```bash
# Backup operations
python scripts/backup_database.py  # Database backup
python scripts/backup_files.py     # File storage backup
python scripts/backup_all.py       # Complete backup

# Cleanup operations
python scripts/cleanup_trash.py        # Clean documents older than 30 days
python scripts/cleanup_tokens.py       # Remove expired tokens
python scripts/cleanup_audit_logs.py   # Archive old audit logs
python scripts/cleanup_all.py          # Complete cleanup
python scripts/cleanup_all.py --dry-run  # Preview without changes
```

## Architecture Overview

### Layered Architecture

The codebase follows a clean layered architecture with clear separation of concerns:

**Models Layer** (`app/models/`)
- SQLAlchemy ORM models defining database schema
- Domain logic encapsulated in model methods
- Key models: `User`, `Perfil`, `Documento`, `Categoria`, `Workflow`, `Permissao`, `Versao`

**Repository Layer** (`app/repositories/`)
- Implements Repository pattern for data access abstraction
- All repositories inherit from `BaseRepository` (generic CRUD operations)
- Isolates SQLAlchemy queries from business logic
- Example: `DocumentRepository`, `UserRepository`, `WorkflowRepository`

**Service Layer** (`app/services/`)
- Contains business logic and orchestration
- Services compose multiple repositories and handle complex operations
- Key services:
  - `document_service.py`: Document upload, versioning, tagging
  - `auth_service.py`: Authentication, login attempts, account locking
  - `permission_service.py`: Fine-grained document permissions (visualizar, editar, excluir, compartilhar)
  - `workflow_service.py`: Multi-stage approval workflows
  - `search_service.py`: Full-text and metadata search
  - `audit_service.py`: Comprehensive audit logging
  - `storage_service.py`: File system operations

**Presentation Layer** (`app/*/routes.py`)
- Flask blueprints organize routes by feature domain
- Blueprints: `auth`, `documents`, `categories`, `search`, `workflows`, `admin`
- Routes are thin controllers delegating to services
- Form validation via Flask-WTF

### Application Factory Pattern

The app uses factory pattern (`app/__init__.py:create_app`):
- Supports multiple configurations (development, testing, production)
- Extensions initialized with app context
- Blueprints registered dynamically
- Security middleware applied automatically

### Configuration Management

Three configuration classes in `config.py`:
- `DevelopmentConfig`: DEBUG=True, SQLALCHEMY_ECHO=True
- `TestingConfig`: Uses SQLite (`test_sqlite.db`), disables CSRF for tests
- `ProductionConfig`: DEBUG=False, secure cookies, no SQL echo

Select via `FLASK_ENV` environment variable.

### Permission System

Fine-grained access control via `PermissionService`:
- **Permission Types**: `visualizar`, `editar`, `excluir`, `compartilhar`
- **Implicit Permissions**: Document owners have all permissions automatically
- **Permission Hierarchy**: Higher permissions (editar, excluir) imply `visualizar`
- **Expiration**: Permissions can have expiration dates
- **Profile-based**: 5 user profiles (Administrator, Manager, Standard User, Auditor, Visitor)

Always check permissions before document operations:
```python
from app.services.permission_service import PermissionService
permission_service = PermissionService()
if not permission_service.check_permission(documento, user_id, 'editar'):
    abort(403)
```

### Document Versioning

- Documents maintain version history via `Versao` model
- Maximum versions per document: 10 (configurable via `MAX_VERSIONS_PER_DOCUMENT`)
- Each version stores file path, size, uploader, and timestamp
- Old versions pruned automatically when limit exceeded

### Workflow System

Multi-stage approval workflows:
- Define workflows with sequential stages
- Assign approvers to each stage
- Documents submitted for approval progress through stages
- Approval/rejection recorded in `AprovacaoDocumento` and `HistoricoAprovacao`
- Email notifications via `NotificationService`

### Audit Logging

All significant operations logged via `AuditService`:
- User actions (login, logout, failed attempts)
- Document operations (upload, edit, delete, share, download)
- Permission changes
- Workflow actions
- Logs stored in `log_auditoria` table with user, timestamp, IP, action details

### File Storage

`StorageService` handles physical file storage:
- Files organized by user ID and year/month directories
- Filenames sanitized and made unique with UUIDs
- SHA256 hash computed for duplicate detection
- Supports encryption for sensitive documents (AES-256)

### Security Features

- **Password Security**: bcrypt hashing with cost factor 12
- **Brute Force Protection**: Account lockout after 5 failed attempts (15 minutes)
- **CSRF Protection**: Flask-WTF CSRF tokens on all forms
- **Rate Limiting**: 100 requests/minute per IP (disabled in tests)
- **Security Headers**: X-Frame-Options, CSP, HSTS via `SecurityHeaders` middleware
- **Session Management**: Secure cookies, 1-hour timeout

## Testing Notes

- Test configuration uses SQLite (`test_sqlite.db`) instead of SQL Server for speed
- `SQLALCHEMY_EXPIRE_ON_COMMIT = False` in tests to prevent detached instance errors
- `check_same_thread=False` for SQLite to support concurrent test threads
- Rate limiting disabled in test mode to avoid flakiness
- `strict_slashes=False` in tests to reduce 308 redirect issues

## Important Conventions

### Error Handling

Services raise specific exceptions (e.g., `PermissionDeniedError`, `DocumentNotFoundError`). Routes should catch and handle appropriately:
```python
from app.services.document_service import DocumentNotFoundError, PermissionDeniedError
try:
    service.operation()
except PermissionDeniedError:
    flash("Access denied", "error")
    abort(403)
except DocumentNotFoundError:
    abort(404)
```

### Database Sessions

- Repositories handle session commits internally for single operations
- Services may manage transactions for multi-step operations
- Use `db.session.rollback()` on exceptions to maintain consistency

### File Paths

- `UPLOAD_FOLDER` defined in config (default: `uploads/`)
- Documents stored as: `uploads/{user_id}/{year}/{month}/{uuid}_{filename}`
- Always use absolute paths in configuration

### Environment Variables

Critical settings in `.env`:
- `DATABASE_SERVER`, `DATABASE_NAME`, `DATABASE_USER`, `DATABASE_PASSWORD`
- `SECRET_KEY` (must be strong in production)
- `ADMIN_EMAIL`, `ADMIN_PASSWORD` (for initial setup)
- `MAX_CONTENT_LENGTH` (default: 50MB, increase for tests to 200MB)

### User Profiles and Permissions

Profile permissions defined in `Perfil` model with boolean flags:
- `pode_criar_documentos`, `pode_editar_proprios`, `pode_excluir_proprios`
- `pode_visualizar_todos`, `pode_editar_todos`, `pode_excluir_todos`
- `pode_gerenciar_usuarios`, `pode_gerenciar_categorias`, `pode_gerenciar_workflows`
- `pode_visualizar_auditoria`

Check profile permissions via `user.has_permission(permission_name)` or profile flags directly.

## Common Development Tasks

### Adding a New Model

1. Create model class in `app/models/` inheriting from `db.Model`
2. Add relationships to related models
3. Create repository in `app/repositories/` inheriting from `BaseRepository`
4. Add migration: `alembic revision --autogenerate -m "Add model"`
5. Run migration: `alembic upgrade head`

### Adding a New Service Method

1. Add method to appropriate service in `app/services/`
2. Use repositories for data access (don't query models directly)
3. Add audit logging for significant operations
4. Raise specific exceptions for error conditions
5. Write tests in `tests/`

### Adding a New Route

1. Add route function to appropriate blueprint in `app/*/routes.py`
2. Use `@login_required` decorator for authenticated routes
3. Check permissions via `PermissionService` for document operations
4. Delegate business logic to services (keep routes thin)
5. Return proper HTTP status codes (200, 201, 400, 403, 404, etc.)

### Debugging

- Development logs: `logs/ged_system.log`
- Gunicorn logs: `logs/gunicorn_access.log`, `logs/gunicorn_error.log`
- Enable SQL echo: Set `SQLALCHEMY_ECHO=True` in config

## Deployment

Production deployment documented in `deployment/DEPLOYMENT_GUIDE.md`. Key points:
- Use Gunicorn with 4+ workers (configured in `gunicorn_config.py`)
- NGINX as reverse proxy (config in `deployment/nginx_sistema_ged.conf`)
- Supervisor or systemd for process management
- Enable SSL/TLS with valid certificates
- Set `FLASK_ENV=production` and strong `SECRET_KEY`
- Schedule backups via cron/Task Scheduler (see `scripts/BACKUP_SCHEDULING.md`)

## Documentation

- **Database Setup**: `DATABASE_SETUP.md`
- **API Documentation**: `docs/API_DOCUMENTATION.md`
- **Permission System**: `docs/PERMISSION_SYSTEM_GUIDE.md`
- **Search Functionality**: `docs/SEARCH_FUNCTIONALITY.md`
- **Logging & Errors**: `docs/LOGGING_AND_ERROR_HANDLING.md`
- **Testing Guide**: `docs/TESTING_GUIDE.md`
- **Deployment**: `deployment/DEPLOYMENT_GUIDE.md`
- **Maintenance Scripts**: `scripts/README.md`
