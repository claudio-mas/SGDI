"""
Database initialization script for Sistema GED
Creates all tables, indexes, constraints, and optionally seeds initial data

This script:
1. Tests database connection
2. Creates all database tables
3. Creates indexes for performance optimization
4. Validates database schema
5. Optionally seeds initial data (profiles, categories, admin user)

Requirements: All database requirements
"""
from app import create_app, db
from app.models import (
    User, Perfil, PasswordReset,
    Documento, Categoria, Pasta, Tag, DocumentoTag,
    Versao, Permissao,
    Workflow, AprovacaoDocumento, HistoricoAprovacao,
    LogAuditoria, SystemSettings
)
from sqlalchemy import inspect, text
import os
import sys


def test_connection(app):
    """Test database connection"""
    print("\n1. Testing database connection...")
    try:
        with db.engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        print("   ✓ Database connection successful")
        
        # Display connection info
        db_uri = app.config['SQLALCHEMY_DATABASE_URI']
        # Mask password in URI for display
        if '@' in db_uri:
            parts = db_uri.split('@')
            if ':' in parts[0]:
                user_pass = parts[0].split(':')
                masked_uri = f"{user_pass[0]}:****@{parts[1]}"
                print(f"   Database: {masked_uri}")
        
        return True
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        return False


def create_tables():
    """Create all database tables"""
    print("\n2. Creating database tables...")
    try:
        db.create_all()
        
        # Verify tables were created
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        expected_tables = [
            'perfis', 'usuarios', 'password_resets',
            'categorias', 'pastas', 'tags', 'documentos', 'documento_tags',
            'versoes', 'permissoes',
            'workflows', 'aprovacao_documentos', 'historico_aprovacoes',
            'log_auditoria', 'system_settings'
        ]
        
        print(f"   ✓ Created {len(tables)} tables")
        
        # Check for missing tables
        missing_tables = [t for t in expected_tables if t not in tables]
        if missing_tables:
            print(f"   ⚠ Warning: Missing tables: {', '.join(missing_tables)}")
        
        return True
    except Exception as e:
        print(f"   ✗ Error creating tables: {e}")
        return False


def create_indexes():
    """Create additional indexes for performance optimization"""
    print("\n3. Creating performance indexes...")
    
    indexes_created = 0
    indexes_failed = 0
    
    # Note: Most indexes are already defined in the models
    # This function can be used to create additional custom indexes
    
    try:
        # Check if indexes exist
        inspector = inspect(db.engine)
        
        # Example: Check indexes on key tables
        tables_to_check = ['usuarios', 'documentos', 'log_auditoria']
        
        for table_name in tables_to_check:
            if table_name in inspector.get_table_names():
                indexes = inspector.get_indexes(table_name)
                print(f"   ✓ Table '{table_name}': {len(indexes)} indexes")
        
        print(f"   Summary: Indexes verified")
        return True
        
    except Exception as e:
        print(f"   ✗ Error checking indexes: {e}")
        return False


def validate_schema():
    """Validate database schema and constraints"""
    print("\n4. Validating database schema...")
    
    try:
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        validation_results = {
            'tables': len(tables),
            'foreign_keys': 0,
            'indexes': 0,
            'unique_constraints': 0
        }
        
        # Count foreign keys, indexes, and constraints
        for table_name in tables:
            fks = inspector.get_foreign_keys(table_name)
            indexes = inspector.get_indexes(table_name)
            unique_constraints = inspector.get_unique_constraints(table_name)
            
            validation_results['foreign_keys'] += len(fks)
            validation_results['indexes'] += len(indexes)
            validation_results['unique_constraints'] += len(unique_constraints)
        
        print(f"   ✓ Tables: {validation_results['tables']}")
        print(f"   ✓ Foreign Keys: {validation_results['foreign_keys']}")
        print(f"   ✓ Indexes: {validation_results['indexes']}")
        print(f"   ✓ Unique Constraints: {validation_results['unique_constraints']}")
        
        # Validate critical tables exist
        critical_tables = ['usuarios', 'perfis', 'documentos', 'categorias']
        missing_critical = [t for t in critical_tables if t not in tables]
        
        if missing_critical:
            print(f"   ✗ Missing critical tables: {', '.join(missing_critical)}")
            return False
        
        print("   ✓ Schema validation passed")
        return True
        
    except Exception as e:
        print(f"   ✗ Schema validation failed: {e}")
        return False


def validate_data():
    """Validate seeded data integrity"""
    print("\n6. Validating data integrity...")
    
    try:
        # Check profiles
        profile_count = Perfil.query.count()
        if profile_count < 5:
            print(f"   ⚠ Warning: Expected 5 profiles, found {profile_count}")
        else:
            print(f"   ✓ Profiles: {profile_count}")
        
        # Check categories
        category_count = Categoria.query.count()
        if category_count < 6:
            print(f"   ⚠ Warning: Expected 6 categories, found {category_count}")
        else:
            print(f"   ✓ Categories: {category_count}")
        
        # Check admin user
        admin_profile = Perfil.query.filter_by(nome='Administrator').first()
        if admin_profile:
            admin_count = User.query.filter_by(perfil_id=admin_profile.id).count()
            if admin_count == 0:
                print(f"   ⚠ Warning: No admin user found")
            else:
                print(f"   ✓ Admin users: {admin_count}")
        
        # Check for orphaned records (basic integrity check)
        users_without_profile = User.query.filter(User.perfil_id.is_(None)).count()
        if users_without_profile > 0:
            print(f"   ⚠ Warning: {users_without_profile} users without profile")
        
        docs_without_user = Documento.query.filter(Documento.usuario_id.is_(None)).count()
        if docs_without_user > 0:
            print(f"   ⚠ Warning: {docs_without_user} documents without user")
        
        print("   ✓ Data validation complete")
        return True
        
    except Exception as e:
        print(f"   ✗ Data validation failed: {e}")
        return False


def init_database(seed=True):
    """
    Initialize database with all tables, indexes, and constraints
    
    Args:
        seed (bool): Whether to seed initial data (default: True)
    
    Returns:
        bool: True if initialization successful, False otherwise
    """
    print("=" * 60)
    print("Sistema GED - Database Initialization")
    print("=" * 60)
    
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    with app.app_context():
        success = True
        
        # Step 1: Test connection
        if not test_connection(app):
            print("\n✗ Cannot proceed without database connection")
            print("\nTroubleshooting:")
            print("  1. Check database connection settings in .env file")
            print("  2. Ensure SQL Server is running")
            print("  3. Verify database exists: CREATE DATABASE sistema_ged")
            print("  4. Verify user has permissions")
            sys.exit(1)
        
        # Step 2: Create tables
        if not create_tables():
            success = False
        
        # Step 3: Create indexes
        if not create_indexes():
            print("   ⚠ Warning: Some indexes may not have been created")
        
        # Step 4: Validate schema
        if not validate_schema():
            success = False
        
        # Step 5: Seed initial data if requested
        if seed and success:
            print("\n5. Seeding initial data...")
            try:
                from seed_data import seed_profiles, seed_categories, seed_admin_user
                
                if not seed_profiles():
                    success = False
                
                if not seed_categories():
                    success = False
                
                if not seed_admin_user():
                    success = False
                
                if success:
                    print("   ✓ Initial data seeded successfully")
                else:
                    print("   ⚠ Initial data seeded with some errors")
                
            except Exception as e:
                print(f"   ✗ Error seeding data: {e}")
                success = False
        elif seed:
            print("\n5. Skipping data seeding due to previous errors")
        else:
            print("\n5. Skipping data seeding (--no-seed flag)")
        
        # Step 6: Validate data (only if seeded)
        if seed and success:
            if not validate_data():
                print("   ⚠ Warning: Data validation found issues")
        
        # Final summary
        print("\n" + "=" * 60)
        if success:
            print("✓ Database initialization complete!")
            print("=" * 60)
            print("\nNext steps:")
            print("  1. Review the admin credentials above")
            print("  2. Update admin password after first login")
            print("  3. Configure email settings in .env file")
            print("  4. Start the application: python run.py")
        else:
            print("⚠ Database initialization completed with errors")
            print("=" * 60)
            print("\nPlease review the errors above and try again")
        print("=" * 60)
        
        if not success:
            sys.exit(1)
        
        return success


if __name__ == '__main__':
    # Check for --no-seed flag
    seed = '--no-seed' not in sys.argv
    init_database(seed=seed)
