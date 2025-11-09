# Database Setup Guide

This guide explains how to initialize and seed the Sistema GED database.

## Prerequisites

1. SQL Server 2019 or later installed and running
2. Python 3.8+ with all dependencies installed (`pip install -r requirements.txt`)
3. `.env` file configured with database connection settings

## Quick Start

### Option 1: Initialize with Seed Data (Recommended)

This will create all tables, indexes, and seed initial data (profiles, categories, admin user):

```bash
python init_db.py
```

### Option 2: Initialize Without Seed Data

This will only create tables and indexes without seeding data:

```bash
python init_db.py --no-seed
```

### Option 3: Seed Data Only

If tables already exist and you only want to seed data:

```bash
python seed_data.py
```

## What Gets Created

### Database Tables

The initialization script creates the following tables:

- **User Management**: `perfis`, `usuarios`, `password_resets`
- **Document Management**: `documentos`, `categorias`, `pastas`, `tags`, `documento_tags`
- **Versioning**: `versoes`
- **Permissions**: `permissoes`
- **Workflows**: `workflows`, `aprovacao_documentos`, `historico_aprovacoes`
- **Audit**: `log_auditoria`
- **Settings**: `system_settings`

### Indexes

Performance indexes are automatically created on:
- `usuarios.email` (unique)
- `documentos.usuario_id`
- `documentos.categoria_id`
- `documentos.status`
- `documentos.hash_arquivo`
- `documentos.data_upload`
- `log_auditoria.usuario_id, data_hora`
- `log_auditoria.tabela, registro_id`

### Seed Data

#### User Profiles (5 profiles)

1. **Administrator** - Full system access with all permissions
2. **Manager** - Document management and workflow approval
3. **Standard User** - Basic document operations (upload, view, edit, share)
4. **Auditor** - Read-only access for compliance
5. **Visitor** - View-only access to shared documents

#### Document Categories (6 categories)

1. **Contracts** - Legal contracts and agreements
2. **Invoices** - Financial invoices and billing documents
3. **HR** - Human resources documents
4. **Legal** - Legal documents and compliance
5. **Technical** - Technical documentation and specifications
6. **Administrative** - General administrative documents

#### Admin User

A default administrator account is created with credentials from environment variables:

- Email: `ADMIN_EMAIL` (default: admin@example.com)
- Password: `ADMIN_PASSWORD` (default: admin123)
- Name: `ADMIN_NAME` (default: System Administrator)

**⚠️ IMPORTANT**: Change the admin password immediately after first login!

## Configuration

### Environment Variables

Configure these in your `.env` file:

```env
# Database Configuration
DATABASE_SERVER=localhost
DATABASE_NAME=sistema_ged
DATABASE_USER=sa
DATABASE_PASSWORD=your-password-here
DATABASE_DRIVER=ODBC Driver 17 for SQL Server

# Admin User (for seeding)
ADMIN_EMAIL=admin@example.com
ADMIN_PASSWORD=admin123
ADMIN_NAME=System Administrator
```

## Validation

The initialization script automatically validates:

1. **Database Connection** - Verifies connection to SQL Server
2. **Table Creation** - Confirms all expected tables exist
3. **Schema Validation** - Checks foreign keys, indexes, and constraints
4. **Data Integrity** - Verifies seeded data is correct

## Troubleshooting

### Connection Failed

```
✗ Connection failed: [error message]
```

**Solutions:**
1. Verify SQL Server is running
2. Check database connection settings in `.env`
3. Ensure database exists: `CREATE DATABASE sistema_ged`
4. Verify user has appropriate permissions

### Missing Tables

```
⚠ Warning: Missing tables: [table names]
```

**Solutions:**
1. Drop and recreate the database
2. Run `python init_db.py` again
3. Check for errors in model definitions

### Seed Data Errors

```
✗ Error creating profiles: [error message]
```

**Solutions:**
1. Ensure tables exist (run `python init_db.py --no-seed` first)
2. Check for duplicate data (profiles/categories already exist)
3. Verify database user has INSERT permissions

### Profile Not Found

```
✗ Error: Administrator profile not found
```

**Solutions:**
1. Run seed_profiles first: `python seed_data.py`
2. Or run full initialization: `python init_db.py`

## Advanced Usage

### Re-seeding Data

If you need to re-seed data after making changes:

```bash
# Delete existing seed data (optional)
# Then re-run seed script
python seed_data.py
```

### Custom Admin Credentials

Set custom admin credentials before seeding:

```bash
export ADMIN_EMAIL=myemail@company.com
export ADMIN_PASSWORD=SecurePassword123
export ADMIN_NAME="John Doe"
python seed_data.py
```

### Using Alembic Migrations

For production environments, use Alembic migrations instead:

```bash
# Initialize Alembic (if not already done)
alembic init migrations

# Create migration
alembic revision --autogenerate -m "Initial schema"

# Apply migration
alembic upgrade head

# Then seed data
python seed_data.py
```

## Verification

After initialization, verify the setup:

```bash
# Check tables exist
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); print(db.engine.table_names())"

# Check profiles
python -c "from app import create_app, db; from app.models import Perfil; app = create_app(); app.app_context().push(); print([p.nome for p in Perfil.query.all()])"

# Check categories
python -c "from app import create_app, db; from app.models import Categoria; app = create_app(); app.app_context().push(); print([c.nome for c in Categoria.query.all()])"
```

## Next Steps

After successful initialization:

1. ✅ Start the application: `python run.py`
2. ✅ Login with admin credentials
3. ✅ Change admin password
4. ✅ Configure email settings
5. ✅ Create additional users
6. ✅ Start uploading documents

## Support

For issues or questions:
- Check the troubleshooting section above
- Review application logs
- Consult the main README.md
- Check deployment documentation in `deployment/` folder
