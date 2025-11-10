# Database Migrations

This directory contains Alembic database migrations for Sistema SGDI.

## Setup

Alembic is already configured. The migration environment is set up to work with Flask-SQLAlchemy.

## Common Commands

### Apply all migrations
```bash
alembic upgrade head
```

### Revert last migration
```bash
alembic downgrade -1
```

### Revert all migrations
```bash
alembic downgrade base
```

### Create a new migration (auto-generate)
```bash
alembic revision --autogenerate -m "Description of changes"
```

### Create a new migration (manual)
```bash
alembic revision -m "Description of changes"
```

### View migration history
```bash
alembic history
```

### View current migration version
```bash
alembic current
```

## Initial Setup

For a fresh database, run:

```bash
# Apply migrations
alembic upgrade head

# Seed initial data
python seed_data.py
```

Or use the initialization script:

```bash
# Initialize database and seed data
python init_db.py

# Initialize database without seeding
python init_db.py --no-seed
```

## Migration Files

- `env.py` - Alembic environment configuration
- `script.py.mako` - Template for new migration files
- `versions/` - Directory containing migration scripts

## Notes

- Always review auto-generated migrations before applying
- Test migrations on a development database first
- Keep migrations in version control
- Never modify applied migrations; create new ones instead
