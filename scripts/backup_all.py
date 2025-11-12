"""
Unified backup script for SGDI
Performs both database and file storage backups
"""
import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backup_database import DatabaseBackup
from backup_files import FileStorageBackup


def main():
    """Execute complete backup process"""
    print("=" * 60)
    print("SGDI - Complete System Backup")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    db_success = False
    files_success = False
    
    # Database backup
    print("\n" + "-" * 60)
    print("PHASE 1: Database Backup")
    print("-" * 60)
    try:
        db_backup = DatabaseBackup()
        db_success, _ = db_backup.create_backup()
        if db_success:
            db_backup.cleanup_old_backups()
    except Exception as e:
        print(f"✗ Database backup error: {str(e)}")
    
    # File storage backup
    print("\n" + "-" * 60)
    print("PHASE 2: File Storage Backup")
    print("-" * 60)
    try:
        files_backup = FileStorageBackup()
        files_success, backup_path = files_backup.create_backup(compression=True)
        if files_success and backup_path:
            files_backup.verify_backup(backup_path)
            files_backup.cleanup_old_backups()
    except Exception as e:
        print(f"✗ File storage backup error: {str(e)}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Backup Summary")
    print("=" * 60)
    print(f"Database backup: {'✓ SUCCESS' if db_success else '✗ FAILED'}")
    print(f"File storage backup: {'✓ SUCCESS' if files_success else '✗ FAILED'}")
    print("=" * 60)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Return success only if both backups succeeded
    return 0 if (db_success and files_success) else 1


if __name__ == '__main__':
    sys.exit(main())
