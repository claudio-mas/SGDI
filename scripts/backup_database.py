"""
Database backup script for Sistema GED
Performs automated SQL Server database backups
"""
import os
import sys
import subprocess
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DatabaseBackup:
    """Handle database backup operations"""
    
    def __init__(self):
        self.server = Config.DATABASE_SERVER
        self.database = Config.DATABASE_NAME
        self.user = Config.DATABASE_USER
        self.password = Config.DATABASE_PASSWORD
        self.backup_dir = os.environ.get('BACKUP_DIR', os.path.join(os.path.dirname(__file__), '..', 'backups', 'database'))
        
        # Create backup directory if it doesn't exist
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
    
    def create_backup(self):
        """Create database backup using SQL Server BACKUP command"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_filename = f"{self.database}_backup_{timestamp}.bak"
        backup_path = os.path.join(self.backup_dir, backup_filename)
        
        print(f"Starting database backup: {self.database}")
        print(f"Backup location: {backup_path}")
        
        # SQL Server BACKUP command
        backup_sql = f"""
        BACKUP DATABASE [{self.database}]
        TO DISK = N'{backup_path}'
        WITH FORMAT, INIT, COMPRESSION,
        NAME = N'{self.database} Full Backup {timestamp}',
        SKIP, NOREWIND, NOUNLOAD, STATS = 10
        """
        
        try:
            # Use sqlcmd to execute backup command
            cmd = [
                'sqlcmd',
                '-S', self.server,
                '-U', self.user,
                '-P', self.password,
                '-Q', backup_sql
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
            
            if result.returncode == 0:
                print(f"✓ Database backup completed successfully")
                print(f"  Backup file: {backup_filename}")
                
                # Get backup file size
                if os.path.exists(backup_path):
                    size_mb = os.path.getsize(backup_path) / (1024 * 1024)
                    print(f"  Backup size: {size_mb:.2f} MB")
                
                return True, backup_path
            else:
                print(f"✗ Database backup failed")
                print(f"  Error: {result.stderr}")
                return False, None
                
        except subprocess.TimeoutExpired:
            print(f"✗ Database backup timed out after 1 hour")
            return False, None
        except FileNotFoundError:
            print(f"✗ sqlcmd not found. Please ensure SQL Server client tools are installed.")
            return False, None
        except Exception as e:
            print(f"✗ Database backup failed with error: {str(e)}")
            return False, None
    
    def cleanup_old_backups(self, retention_days=90):
        """Remove backup files older than retention period"""
        print(f"\nCleaning up backups older than {retention_days} days...")
        
        current_time = datetime.now()
        deleted_count = 0
        
        try:
            for filename in os.listdir(self.backup_dir):
                if filename.endswith('.bak'):
                    filepath = os.path.join(self.backup_dir, filename)
                    file_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                    age_days = (current_time - file_time).days
                    
                    if age_days > retention_days:
                        os.remove(filepath)
                        deleted_count += 1
                        print(f"  Deleted old backup: {filename} (age: {age_days} days)")
            
            if deleted_count > 0:
                print(f"✓ Cleaned up {deleted_count} old backup(s)")
            else:
                print(f"✓ No old backups to clean up")
                
        except Exception as e:
            print(f"✗ Error during cleanup: {str(e)}")


def main():
    """Main backup execution"""
    print("=" * 60)
    print("Sistema GED - Database Backup")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    backup = DatabaseBackup()
    
    # Create backup
    success, backup_path = backup.create_backup()
    
    if success:
        # Cleanup old backups
        backup.cleanup_old_backups()
        print("\n" + "=" * 60)
        print("Backup process completed successfully")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("Backup process failed")
        print("=" * 60)
        return 1


if __name__ == '__main__':
    sys.exit(main())
