# Design Document - Sistema GED

## Overview

Sistema GED is a web-based Electronic Document Management System built with Flask (Python), SQL Server, and Bootstrap. The system follows a layered architecture pattern with clear separation of concerns, implementing MVC, Repository, and Service Layer patterns.

### Key Design Principles

- **Layered Architecture**: Separation into Presentation, Application, Domain, Infrastructure, and Data layers
- **Clean Architecture**: Business logic independent of frameworks and external dependencies
- **SOLID Principles**: Single responsibility, dependency injection, interface segregation
- **Security First**: Authentication, authorization, encryption, and audit logging at every layer
- **Scalability**: Support for 1000 concurrent users and 500,000 documents

## Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────┐
│      PRESENTATION LAYER                 │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │Templates │ │Bootstrap │ │JavaScript│ │
│  │ (Jinja2) │ │ CSS/HTML │ │Libraries│ │
│  └──────────┘ └──────────┘ └─────────┘ │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│    APPLICATION LAYER (Flask)            │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │Controllers│ │ Services │ │Middleware│ │
│  │ (Routes) │ │(Business)│ │(Auth)   │ │
│  └──────────┘ └──────────┘ └─────────┘ │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│       DOMAIN LAYER                      │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │  Models  │ │ Schemas  │ │Validators│ │
│  │(Entities)│ │  (DTO)   │ │         │ │
│  └──────────┘ └──────────┘ └─────────┘ │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│    INFRASTRUCTURE LAYER                 │
│  ┌──────────┐ ┌──────────┐ ┌─────────┐ │
│  │Repository│ │File System│ │External │ │
│  │(Database)│ │ Storage  │ │Services │ │
│  └──────────┘ └──────────┘ └─────────┘ │
└─────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────┐
│         DATA LAYER                      │
│  ┌──────────┐ ┌──────────┐             │
│  │SQL Server│ │File Store│             │
│  │ Database │ │ (Uploads)│             │
│  └──────────┘ └──────────┘             │
└─────────────────────────────────────────┘
```

### Request Flow

```
Browser → NGINX → Gunicorn → Flask App
                              ↓
                         Middleware (Auth, Rate Limit)
                              ↓
                         Controller (Route Handler)
                              ↓
                         Service (Business Logic)
                              ↓
                         Repository (Data Access)
                              ↓
                         Database / File Storage
```

## Components and Interfaces

### 1. Application Factory Pattern

The application uses Flask's application factory pattern for flexible configuration and testing.

**Key Components:**
- `create_app(config_class)`: Creates and configures Flask application
- Extension initialization: SQLAlchemy, Flask-Login, Flask-WTF
- Blueprint registration: auth, document, admin, search, workflow

**Configuration:**
- Development, Testing, Production configurations
- Environment variables for sensitive data
- Database connection pooling

### 2. Blueprints (Modules)

**auth_bp** - Authentication and Authorization
- Routes: `/login`, `/logout`, `/register`, `/reset-password`
- Handles user authentication, session management, password reset

**document_bp** - Document Management
- Routes: `/documents`, `/documents/upload`, `/documents/<id>`, `/documents/<id>/download`
- Handles CRUD operations, file upload/download, metadata management

**category_bp** - Categories and Organization
- Routes: `/categories`, `/categories/<id>`, `/folders`
- Manages document organization structure

**search_bp** - Search and Filters
- Routes: `/search`, `/search/advanced`, `/search/suggestions`
- Implements simple, advanced, and full-text search

**workflow_bp** - Approval Workflows
- Routes: `/workflows`, `/workflows/<id>/approve`, `/workflows/<id>/reject`
- Manages document approval processes

**admin_bp** - System Administration
- Routes: `/admin/dashboard`, `/admin/users`, `/admin/settings`, `/admin/reports`
- System configuration and user management

### 3. Data Models

**User Model**
```python
- id: Integer (PK)
- nome: String(100)
- email: String(120) UNIQUE
- senha_hash: String(255)
- perfil_id: Integer (FK → perfis)
- ativo: Boolean
- tentativas_login: Integer
- bloqueado_ate: DateTime
- ultimo_acesso: DateTime
- data_cadastro: DateTime

Methods:
- set_password(password)
- check_password(password)
- has_permission(permission_name)
```

**Document Model**
```python
- id: Integer (PK)
- nome: String(255)
- descricao: Text
- caminho_arquivo: String(500)
- nome_arquivo_original: String(255)
- tamanho_bytes: BigInteger
- tipo_mime: String(100)
- hash_arquivo: String(64) SHA256
- categoria_id: Integer (FK → categorias)
- pasta_id: Integer (FK → pastas)
- usuario_id: Integer (FK → usuarios)
- versao_atual: Integer
- status: String(20) [ativo, arquivado, excluido]
- criptografado: Boolean
- data_upload: DateTime
- data_modificacao: DateTime
- data_exclusao: DateTime

Properties:
- extensao: File extension
- tamanho_formatado: Human-readable size

Methods:
- soft_delete(): Logical deletion
```

**Category Model**
```python
- id: Integer (PK)
- nome: String(100) UNIQUE
- descricao: Text
- categoria_pai_id: Integer (FK → categorias, self-reference)
- icone: String(50)
- cor: String(7) Hex color
- ordem: Integer
- ativo: Boolean

Properties:
- caminho_completo: Full hierarchical path
```

**Tag Model**
```python
- id: Integer (PK)
- nome: String(50) UNIQUE
```

**Version Model**
```python
- id: Integer (PK)
- documento_id: Integer (FK → documentos)
- numero_versao: Integer
- caminho_arquivo: String(500)
- tamanho_bytes: BigInteger
- usuario_id: Integer (FK → usuarios)
- comentario: Text
- data_criacao: DateTime
```

**Permission Model**
```python
- id: Integer (PK)
- documento_id: Integer (FK → documentos)
- usuario_id: Integer (FK → usuarios)
- tipo_permissao: String(20) [visualizar, editar, excluir, compartilhar]
- data_concessao: DateTime
- concedido_por: Integer (FK → usuarios)
```

**AuditLog Model**
```python
- id: BigInteger (PK)
- usuario_id: Integer (FK → usuarios)
- acao: String(50)
- tabela: String(50)
- registro_id: Integer
- dados_json: Text (JSON)
- ip_address: String(45)
- data_hora: DateTime
```

### 4. Repository Layer

**BaseRepository**
- Generic CRUD operations
- Methods: `get_by_id()`, `get_all()`, `filter_by()`, `create()`, `update()`, `delete()`, `paginate()`

**DocumentRepository** (extends BaseRepository)
- `search(query, filters, user_id)`: Advanced document search
- `get_recent(user_id, days, limit)`: Recent documents
- `get_by_category(categoria_id, user_id)`: Documents by category
- `get_deleted(user_id)`: Trash/deleted documents
- `permanent_delete(id)`: Physical deletion

**UserRepository** (extends BaseRepository)
- `get_by_email(email)`: Find user by email
- `get_active_users()`: List active users

**CategoryRepository** (extends BaseRepository)
- `get_hierarchy()`: Get category tree structure
- `get_root_categories()`: Top-level categories

### 5. Service Layer

**AuthService**
- `authenticate(email, password, ip_address)`: User authentication with brute-force protection
- `register(user_data)`: New user registration
- `request_password_reset(email)`: Generate password reset token
- `reset_password(token, new_password)`: Reset password using token

**DocumentService**
- `upload_document(file, metadata, user_id)`: Process file upload with validation
- `download_document(document_id, user_id)`: Prepare file for download
- `update_document(document_id, metadata, user_id)`: Update document metadata
- `delete_document(document_id, user_id)`: Soft delete document
- `create_version(document_id, new_file, user_id, comment)`: Create new version
- `_calculate_hash(file)`: Calculate SHA256 hash
- `_has_permission(documento, user_id, permission_type)`: Check permissions
- `_log_access(documento, user_id, action)`: Log document access

**SearchService**
- `search(query, filters, user_id, page, per_page)`: Unified search with pagination
- `fulltext_search(query, user_id)`: Full-text search in PDF content
- `get_suggestions(partial_query, limit)`: Autocomplete suggestions

**StorageService**
- `save_file(file, filename, user_id)`: Save file to storage
- `get_file(file_path)`: Retrieve file from storage
- `delete_file(file_path)`: Remove file from storage
- Support for local filesystem and cloud storage (S3, Azure Blob)

**NotificationService**
- `notify_upload(documento, user_id)`: Send upload notification
- `notify_share(documento, from_user, to_user)`: Send share notification
- `notify_workflow(documento, approver)`: Send approval request
- `send_email(to, subject, body)`: Generic email sending

**WorkflowService**
- `create_workflow(workflow_data)`: Create approval workflow
- `submit_for_approval(document_id, workflow_id, user_id)`: Submit document
- `approve_document(approval_id, user_id, comment)`: Approve document
- `reject_document(approval_id, user_id, comment)`: Reject document

## Data Models

### Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────┐
│   PERFIS    │       │  USUARIOS   │
├─────────────┤       ├─────────────┤
│ id (PK)     │◄──┐   │ id (PK)     │
│ nome        │   └───│ perfil_id(FK)│
│ descricao   │       │ nome        │
└─────────────┘       │ email (UK)  │
                      │ senha_hash  │
                      │ ativo       │
                      └──────┬──────┘
                             │ 1:N
                             ↓
                      ┌─────────────┐
                      │ DOCUMENTOS  │
                      ├─────────────┤
                      │ id (PK)     │
                      │ nome        │
                      │ caminho     │
                      │ tamanho     │
                      │ tipo_mime   │
                      │ hash        │
                      │ categoria_id│
                      │ pasta_id    │
                      │ usuario_id  │
                      │ status      │
                      └──────┬──────┘
                             │
                    ┌────────┼────────┐
                    │        │        │
                    ↓        ↓        ↓
            ┌──────────┐ ┌──────┐ ┌──────────┐
            │ VERSOES  │ │ TAGS │ │PERMISSOES│
            └──────────┘ └──────┘ └──────────┘
```

### Database Schema

**Key Tables:**
1. `usuarios` - User accounts
2. `perfis` - User roles/profiles
3. `documentos` - Document metadata
4. `categorias` - Document categories (hierarchical)
5. `pastas` - Folder structure (hierarchical)
6. `tags` - Document tags
7. `documento_tags` - Many-to-many relationship
8. `versoes` - Document versions
9. `permissoes` - Document permissions
10. `log_auditoria` - Audit trail
11. `workflows` - Approval workflows
12. `aprovacao_documentos` - Workflow instances
13. `historico_aprovacoes` - Approval history

**Indexes:**
- `usuarios.email` (UNIQUE)
- `documentos.usuario_id`
- `documentos.categoria_id`
- `documentos.status`
- `documentos.hash_arquivo`
- `documentos.data_upload` (DESC)
- `log_auditoria.usuario_id, data_hora` (DESC)
- `log_auditoria.tabela, registro_id`

**Full-Text Search:**
- Full-text catalog on `documentos` table
- Indexed columns: `nome`, `descricao`, `conteudo_texto` (extracted from PDFs)

## Error Handling

### Exception Hierarchy

```python
GEDException (Base)
├── AuthenticationError
│   ├── InvalidCredentialsError
│   ├── AccountBlockedError
│   └── SessionExpiredError
├── AuthorizationError
│   ├── PermissionDeniedError
│   └── InsufficientPrivilegesError
├── ValidationError
│   ├── InvalidFileTypeError
│   ├── FileSizeExceededError
│   └── DuplicateDocumentError
├── NotFoundError
│   ├── DocumentNotFoundError
│   └── UserNotFoundError
└── StorageError
    ├── FileUploadError
    └── FileDownloadError
```

### Error Handling Strategy

1. **Controller Level**: Catch exceptions, log errors, display user-friendly messages
2. **Service Level**: Validate business rules, raise specific exceptions
3. **Repository Level**: Handle database errors, transaction rollback
4. **Global Error Handler**: Catch unhandled exceptions, log stack traces, return 500 errors

### Logging

- **Application Logs**: `logs/ged_system.log` (rotating, 10MB max, 10 backups)
- **Access Logs**: `logs/gunicorn_access.log`
- **Error Logs**: `logs/gunicorn_error.log`
- **Audit Logs**: Database table `log_auditoria`

## Testing Strategy

### Unit Tests

**Coverage Target**: 70% minimum

**Test Modules:**
- `tests/unit/test_models.py` - Model methods and properties
- `tests/unit/test_repositories.py` - Repository CRUD operations
- `tests/unit/test_services.py` - Business logic
- `tests/unit/test_utils.py` - Utility functions

**Mocking Strategy:**
- Mock database with SQLite in-memory
- Mock file system operations
- Mock external services (email, storage)

### Integration Tests

**Test Modules:**
- `tests/integration/test_auth_flow.py` - Login, logout, password reset
- `tests/integration/test_document_flow.py` - Upload, download, delete
- `tests/integration/test_search.py` - Search functionality
- `tests/integration/test_workflow.py` - Approval processes

### End-to-End Tests

**Test Scenarios:**
- Complete document lifecycle: upload → categorize → share → approve → download
- User management: create → assign role → login → perform operations
- Search and retrieval: upload documents → search → filter → view

**Tools:**
- Selenium WebDriver for browser automation
- pytest for test framework
- pytest-flask for Flask testing utilities

### Performance Tests

**Load Testing:**
- Simulate 1000 concurrent users
- Test 100 simultaneous uploads
- Test 1000 searches per minute

**Tools:**
- Locust for load testing
- Apache JMeter for stress testing

## Security Considerations

### Authentication Security

1. **Password Hashing**: bcrypt with cost factor 12
2. **Brute Force Protection**: Account lockout after 5 failed attempts (15 minutes)
3. **Session Management**: Secure, HTTP-only cookies with CSRF protection
4. **Password Reset**: Time-limited tokens (1 hour expiration)

### Authorization Security

1. **Role-Based Access Control (RBAC)**: Five user profiles with distinct permissions
2. **Permission Validation**: Check permissions on every operation
3. **Principle of Least Privilege**: Users have minimum necessary permissions

### Data Security

1. **Encryption in Transit**: TLS 1.2+ for all HTTPS connections
2. **Encryption at Rest**: Optional AES-256 encryption for sensitive documents
3. **File Validation**: MIME type verification, file size limits, virus scanning (future)

### Application Security

1. **SQL Injection Prevention**: Parameterized queries, ORM usage
2. **XSS Prevention**: Input sanitization, output encoding, Content Security Policy
3. **CSRF Protection**: Synchronizer tokens on all state-changing operations
4. **Rate Limiting**: 100 requests/minute per IP address
5. **Security Headers**: X-Frame-Options, X-Content-Type-Options, Strict-Transport-Security

### Audit and Compliance

1. **Comprehensive Logging**: All operations logged with user, timestamp, IP
2. **LGPD Compliance**: Data anonymization, export, deletion on request
3. **Immutable Audit Trail**: Audit logs cannot be modified or deleted
4. **Data Retention**: Logs retained for 1 year, backups for 90 days

## Performance Optimization

### Database Optimization

1. **Indexing**: Strategic indexes on frequently queried columns
2. **Query Optimization**: Use of joins, eager loading to prevent N+1 queries
3. **Connection Pooling**: Reuse database connections
4. **Stored Procedures**: Complex operations executed in database

### Application Optimization

1. **Caching**: Flask-Caching for frequently accessed data (categories, user profiles)
2. **Response Compression**: gzip compression for HTML, JSON responses
3. **Static Asset Optimization**: Minified CSS/JS, CDN for libraries
4. **Lazy Loading**: Load images and large content on demand

### File Storage Optimization

1. **Chunked Upload**: Large files uploaded in chunks
2. **Streaming Download**: Files streamed to avoid memory issues
3. **Storage Backends**: Support for local, S3, Azure Blob Storage
4. **File Deduplication**: SHA256 hash prevents duplicate storage

## Deployment Architecture

### Production Environment

```
Internet
    ↓
[Load Balancer]
    ↓
[NGINX Reverse Proxy] (SSL Termination)
    ↓
[Gunicorn WSGI Server] (4 workers)
    ↓
[Flask Application]
    ↓
[SQL Server Database]
[File Storage]
```

### Infrastructure Requirements

**Application Server:**
- OS: Linux (Ubuntu 20.04+) or Windows Server 2019+
- CPU: 4 cores minimum
- RAM: 8GB minimum
- Disk: 100GB for application, 2TB+ for file storage

**Database Server:**
- SQL Server 2019 or later
- CPU: 4 cores minimum
- RAM: 16GB minimum
- Disk: 500GB minimum with RAID configuration

**Network:**
- Bandwidth: 100 Mbps minimum
- SSL Certificate: Valid TLS certificate for HTTPS

### Deployment Process

1. **Environment Setup**: Create virtual environment, install dependencies
2. **Database Migration**: Run Alembic migrations to create schema
3. **Configuration**: Set environment variables, configure storage
4. **Static Files**: Collect and serve static assets
5. **Process Management**: Use Supervisor to manage Gunicorn processes
6. **Reverse Proxy**: Configure NGINX for SSL and load balancing
7. **Monitoring**: Set up logging, monitoring, and alerting

### Backup Strategy

1. **Database Backup**: Daily automated backups, 90-day retention
2. **File Backup**: Weekly full backups, 90-day retention
3. **Backup Verification**: Monthly restore tests
4. **Offsite Storage**: Backups replicated to secondary location

## Technology Stack

### Backend
- **Framework**: Flask 3.0+
- **ORM**: Flask-SQLAlchemy
- **Authentication**: Flask-Login
- **Forms**: Flask-WTF
- **Database Driver**: PyODBC
- **Security**: Werkzeug
- **PDF Processing**: PyPDF2
- **File Validation**: python-magic

### Frontend
- **CSS Framework**: Bootstrap 5.3+
- **JavaScript**: jQuery 3.7+
- **Tables**: DataTables
- **Select Fields**: Select2
- **File Upload**: Dropzone.js
- **Charts**: Chart.js

### Database
- **RDBMS**: SQL Server 2019+
- **Full-Text Search**: SQL Server Full-Text Search

### Infrastructure
- **WSGI Server**: Gunicorn
- **Reverse Proxy**: NGINX
- **Process Manager**: Supervisor
- **Caching**: Flask-Caching (Simple/Redis)
- **Task Queue**: Celery (future enhancement)

### Development Tools
- **Version Control**: Git
- **Testing**: pytest, pytest-flask
- **Code Quality**: pylint, black, flake8
- **Documentation**: Sphinx
- **API Documentation**: Flask-RESTX (future)
