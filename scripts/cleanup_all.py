"""
Unified cleanup script for SGDI
Performs all maintenance cleanup tasks
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from cleanup_trash import TrashCleanup
from cleanup_tokens import TokenCleanup
from cleanup_audit_logs import AuditLogCleanup
from dotenv import load_dotenv

load_dotenv()


def main():
    """Execute complete cleanup process"""
    print("=" * 60)
    print("SGDI - Complete System Cleanup")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check for dry-run flag
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("*** DRY RUN MODE - No changes will be made ***\n")
    
    # Create Flask app context
    app = create_app(os.getenv('FLASK_ENV', 'production'))
    
    results = {
        'trash': 0,
        'tokens': 0,
        'audit_logs': 0
    }
    
    # Cleanup 1: Trash documents
    print("\n" + "-" * 60)
    print("PHASE 1: Trash Cleanup")
    print("-" * 60)
    try:
        trash_cleanup = TrashCleanup(app)
        result = trash_cleanup.cleanup(dry_run=dry_run)
        if isinstance(result, tuple):
            results['trash'] = result[0]
        else:
            results['trash'] = result
    except Exception as e:
        print(f"✗ Trash cleanup error: {str(e)}")
    
    # Cleanup 2: Password reset tokens
    print("\n" + "-" * 60)
    print("PHASE 2: Password Reset Token Cleanup")
    print("-" * 60)
    try:
        token_cleanup = TokenCleanup(app)
        results['tokens'] = token_cleanup.cleanup(dry_run=dry_run, include_used=True)
    except Exception as e:
        print(f"✗ Token cleanup error: {str(e)}")
    
    # Cleanup 3: Audit logs
    print("\n" + "-" * 60)
    print("PHASE 3: Audit Log Cleanup")
    print("-" * 60)
    try:
        audit_cleanup = AuditLogCleanup(app)
        results['audit_logs'] = audit_cleanup.cleanup(dry_run=dry_run, archive=True)
    except Exception as e:
        print(f"✗ Audit log cleanup error: {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Cleanup Summary")
    print("=" * 60)
    print(f"Trash documents deleted: {results['trash']}")
    print(f"Password reset tokens deleted: {results['tokens']}")
    print(f"Audit logs archived/deleted: {results['audit_logs']}")
    print(f"Total items processed: {sum(results.values())}")
    print("=" * 60)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
