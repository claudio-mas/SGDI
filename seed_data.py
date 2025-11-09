"""
Seed data script for Sistema GED
Creates default profiles, categories, and admin user

Requirements:
- 1.5: Support five user profiles (Administrator, Manager, Standard User, Auditor, Visitor)
- 3.2: Provide predefined categories (Contracts, Invoices, HR, Legal, Technical, Administrative)
"""
from app import create_app, db
from app.models import Perfil, Categoria, User
from datetime import datetime
import os
import sys


def seed_profiles():
    """
    Create default user profiles
    
    Requirement 1.5: Support five user profiles
    - Administrator: Full system access
    - Manager: Document management and workflow approval
    - Standard User: Basic document operations
    - Auditor: Read-only access for compliance
    - Visitor: View-only access to shared documents
    """
    profiles = [
        {
            'nome': 'Administrator',
            'descricao': 'Full system access with all permissions including user management and system configuration'
        },
        {
            'nome': 'Manager',
            'descricao': 'Can manage documents, approve workflows, and manage users within their department'
        },
        {
            'nome': 'Standard User',
            'descricao': 'Can upload, view, edit, and share documents'
        },
        {
            'nome': 'Auditor',
            'descricao': 'Read-only access to documents and audit logs for compliance purposes'
        },
        {
            'nome': 'Visitor',
            'descricao': 'View-only access to shared documents'
        }
    ]
    
    print("Creating user profiles...")
    created_count = 0
    existing_count = 0
    
    try:
        for profile_data in profiles:
            # Validate profile data
            if not profile_data.get('nome') or not profile_data.get('descricao'):
                print(f"  ✗ Invalid profile data: {profile_data}")
                continue
            
            existing = Perfil.query.filter_by(nome=profile_data['nome']).first()
            if not existing:
                profile = Perfil(**profile_data)
                db.session.add(profile)
                print(f"  ✓ Created profile: {profile_data['nome']}")
                created_count += 1
            else:
                print(f"  - Profile already exists: {profile_data['nome']}")
                existing_count += 1
        
        db.session.commit()
        print(f"  Summary: {created_count} created, {existing_count} already existed")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"  ✗ Error creating profiles: {e}")
        return False


def seed_categories():
    """
    Create default document categories
    
    Requirement 3.2: Provide predefined categories
    - Contracts, Invoices, HR, Legal, Technical, Administrative
    """
    categories = [
        {
            'nome': 'Contracts',
            'descricao': 'Legal contracts and agreements',
            'icone': 'file-contract',
            'cor': '#3498db',
            'ordem': 1,
            'ativo': True
        },
        {
            'nome': 'Invoices',
            'descricao': 'Financial invoices and billing documents',
            'icone': 'file-invoice',
            'cor': '#2ecc71',
            'ordem': 2,
            'ativo': True
        },
        {
            'nome': 'HR',
            'descricao': 'Human resources documents',
            'icone': 'users',
            'cor': '#e74c3c',
            'ordem': 3,
            'ativo': True
        },
        {
            'nome': 'Legal',
            'descricao': 'Legal documents and compliance',
            'icone': 'gavel',
            'cor': '#9b59b6',
            'ordem': 4,
            'ativo': True
        },
        {
            'nome': 'Technical',
            'descricao': 'Technical documentation and specifications',
            'icone': 'cogs',
            'cor': '#34495e',
            'ordem': 5,
            'ativo': True
        },
        {
            'nome': 'Administrative',
            'descricao': 'General administrative documents',
            'icone': 'folder',
            'cor': '#95a5a6',
            'ordem': 6,
            'ativo': True
        }
    ]
    
    print("\nCreating document categories...")
    created_count = 0
    existing_count = 0
    
    try:
        for category_data in categories:
            # Validate category data
            if not category_data.get('nome'):
                print(f"  ✗ Invalid category data: {category_data}")
                continue
            
            # Validate color format (hex color)
            if category_data.get('cor') and not category_data['cor'].startswith('#'):
                print(f"  ✗ Invalid color format for {category_data['nome']}: {category_data['cor']}")
                continue
            
            existing = Categoria.query.filter_by(nome=category_data['nome']).first()
            if not existing:
                category = Categoria(**category_data)
                db.session.add(category)
                print(f"  ✓ Created category: {category_data['nome']}")
                created_count += 1
            else:
                print(f"  - Category already exists: {category_data['nome']}")
                existing_count += 1
        
        db.session.commit()
        print(f"  Summary: {created_count} created, {existing_count} already existed")
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"  ✗ Error creating categories: {e}")
        return False


def seed_admin_user():
    """
    Create default admin user
    
    Creates a sample administrator account for initial system access.
    Credentials can be configured via environment variables.
    """
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    admin_password = os.getenv('ADMIN_PASSWORD', 'admin123')
    admin_name = os.getenv('ADMIN_NAME', 'System Administrator')
    
    print("\nCreating admin user...")
    
    try:
        # Validate email format
        if '@' not in admin_email or '.' not in admin_email:
            print(f"  ✗ Invalid email format: {admin_email}")
            return False
        
        # Validate password strength (minimum 6 characters for initial setup)
        if len(admin_password) < 6:
            print(f"  ✗ Password too weak (minimum 6 characters required)")
            return False
        
        existing_admin = User.query.filter_by(email=admin_email).first()
        
        if not existing_admin:
            admin_profile = Perfil.query.filter_by(nome='Administrator').first()
            if not admin_profile:
                print("  ✗ Error: Administrator profile not found. Run seed_profiles first.")
                return False
            
            admin_user = User(
                nome=admin_name,
                email=admin_email,
                perfil_id=admin_profile.id,
                ativo=True,
                tentativas_login=0,
                data_cadastro=datetime.utcnow()
            )
            admin_user.set_password(admin_password)
            
            db.session.add(admin_user)
            db.session.commit()
            
            print(f"  ✓ Created admin user: {admin_email}")
            print(f"    Name: {admin_name}")
            print(f"    Password: {admin_password}")
            print(f"    ⚠ IMPORTANT: Change this password after first login!")
            return True
        else:
            print(f"  - Admin user already exists: {admin_email}")
            return True
            
    except Exception as e:
        db.session.rollback()
        print(f"  ✗ Error creating admin user: {e}")
        return False


def verify_seed_data():
    """
    Verify that seed data was created successfully
    """
    print("\nVerifying seed data...")
    
    try:
        # Verify profiles
        profile_count = Perfil.query.count()
        expected_profiles = ['Administrator', 'Manager', 'Standard User', 'Auditor', 'Visitor']
        actual_profiles = [p.nome for p in Perfil.query.all()]
        
        print(f"  Profiles: {profile_count} found")
        for profile_name in expected_profiles:
            if profile_name in actual_profiles:
                print(f"    ✓ {profile_name}")
            else:
                print(f"    ✗ {profile_name} - MISSING")
        
        # Verify categories
        category_count = Categoria.query.count()
        expected_categories = ['Contracts', 'Invoices', 'HR', 'Legal', 'Technical', 'Administrative']
        actual_categories = [c.nome for c in Categoria.query.all()]
        
        print(f"  Categories: {category_count} found")
        for category_name in expected_categories:
            if category_name in actual_categories:
                print(f"    ✓ {category_name}")
            else:
                print(f"    ✗ {category_name} - MISSING")
        
        # Verify admin user
        admin_count = User.query.join(Perfil).filter(Perfil.nome == 'Administrator').count()
        print(f"  Admin users: {admin_count} found")
        
        # Check if all expected data exists
        all_profiles_exist = all(p in actual_profiles for p in expected_profiles)
        all_categories_exist = all(c in actual_categories for c in expected_categories)
        admin_exists = admin_count > 0
        
        if all_profiles_exist and all_categories_exist and admin_exists:
            print("\n  ✓ All seed data verified successfully")
            return True
        else:
            print("\n  ✗ Some seed data is missing")
            return False
            
    except Exception as e:
        print(f"  ✗ Error verifying seed data: {e}")
        return False


def main():
    """
    Main seed function
    
    Executes all seeding operations in the correct order:
    1. User profiles (required for users)
    2. Document categories (required for document organization)
    3. Admin user (requires profiles to exist)
    4. Verification of seeded data
    """
    print("=" * 60)
    print("Sistema GED - Database Seed Script")
    print("=" * 60)
    
    app = create_app(os.getenv('FLASK_ENV', 'development'))
    
    with app.app_context():
        # Check if database tables exist
        try:
            print("\nChecking database connection...")
            db.engine.connect()
            print("  ✓ Database connection successful")
        except Exception as e:
            print(f"\n✗ Error connecting to database: {e}")
            print("\nTroubleshooting:")
            print("  1. Make sure the database exists")
            print("  2. Verify connection settings in .env file")
            print("  3. Run migrations: alembic upgrade head")
            print("  4. Or run: python init_db.py")
            sys.exit(1)
        
        # Seed data in order
        success = True
        
        if not seed_profiles():
            success = False
        
        if not seed_categories():
            success = False
        
        if not seed_admin_user():
            success = False
        
        # Verify seeded data
        if success:
            verify_seed_data()
        
        print("\n" + "=" * 60)
        if success:
            print("✓ Seed data created successfully!")
        else:
            print("⚠ Seed data created with some errors")
        print("=" * 60)
        
        if not success:
            sys.exit(1)


if __name__ == '__main__':
    main()
