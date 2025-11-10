"""
File storage backup script for Sistema SGDI
Performs automated backup of uploaded documents
"""
import os
import sys
import shutil
from datetime import datetime
from pathlib import Path
import zipfile

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from config import Config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class FileStorageBackup:
    """Handle file storage backup operations"""
    
    def __init__(self):
        self.upload_dir = Config.UPLOAD_FOLDER
        self.backup_dir = os.environ.get('BACKUP_DIR', os.path.join(os.path.dirname(__file__), '..', 'backups', 'files'))
        
        # Create backup directory if it doesn't exist
        Path(self.backup_dir).mkdir(parents=True, exist_ok=True)
    
    def get_directory_size(self, directory):
        """Calculate total size of directory in bytes"""
        total_size = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
        except Exception as e:
            print(f"  Warning: Error calculating directory size: {str(e)}")
        return total_size
    
    def count_files(self, directory):
        """Count total number of files in directory"""
        count = 0
        try:
            for dirpath, dirnames, filenames in os.walk(directory):
                count += len(filenames)
        except Exception as e:
            print(f"  Warning: Error counting files: {str(e)}")
        return count
    
    def create_backup(self, compression=True):
        """Create backup of file storage"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if not os.path.exists(self.upload_dir):
            print(f"✗ Upload directory not found: {self.upload_dir}")
            return False, None
        
        print(f"Starting file storage backup")
        print(f"Source directory: {self.upload_dir}")
        
        # Get statistics
        file_count = self.count_files(self.upload_dir)
        total_size = self.get_directory_size(self.upload_dir)
        size_mb = total_size / (1024 * 1024)
        
        print(f"Files to backup: {file_count}")
        print(f"Total size: {size_mb:.2f} MB")
        
        if compression:
            # Create compressed backup
            backup_filename = f"files_backup_{timestamp}.zip"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            try:
                print(f"\nCreating compressed backup...")
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(self.upload_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, self.upload_dir)
                            zipf.write(file_path, arcname)
                
                backup_size_mb = os.path.getsize(backup_path) / (1024 * 1024)
                compression_ratio = (1 - backup_size_mb / size_mb) * 100 if size_mb > 0 else 0
                
                print(f"✓ File storage backup completed successfully")
                print(f"  Backup file: {backup_filename}")
                print(f"  Backup size: {backup_size_mb:.2f} MB")
                print(f"  Compression ratio: {compression_ratio:.1f}%")
                
                return True, backup_path
                
            except Exception as e:
                print(f"✗ Backup failed: {str(e)}")
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                return False, None
        else:
            # Create uncompressed backup (copy directory)
            backup_dirname = f"files_backup_{timestamp}"
            backup_path = os.path.join(self.backup_dir, backup_dirname)
            
            try:
                print(f"\nCreating uncompressed backup...")
                shutil.copytree(self.upload_dir, backup_path)
                
                print(f"✓ File storage backup completed successfully")
                print(f"  Backup directory: {backup_dirname}")
                print(f"  Backup size: {size_mb:.2f} MB")
                
                return True, backup_path
                
            except Exception as e:
                print(f"✗ Backup failed: {str(e)}")
                if os.path.exists(backup_path):
                    shutil.rmtree(backup_path)
                return False, None
    
    def cleanup_old_backups(self, retention_days=90):
        """Remove backup files older than retention period"""
        print(f"\nCleaning up backups older than {retention_days} days...")
        
        current_time = datetime.now()
        deleted_count = 0
        
        try:
            for item in os.listdir(self.backup_dir):
                item_path = os.path.join(self.backup_dir, item)
                
                # Check both .zip files and directories
                if item.startswith('files_backup_'):
                    item_time = datetime.fromtimestamp(os.path.getmtime(item_path))
                    age_days = (current_time - item_time).days
                    
                    if age_days > retention_days:
                        if os.path.isfile(item_path):
                            os.remove(item_path)
                        elif os.path.isdir(item_path):
                            shutil.rmtree(item_path)
                        
                        deleted_count += 1
                        print(f"  Deleted old backup: {item} (age: {age_days} days)")
            
            if deleted_count > 0:
                print(f"✓ Cleaned up {deleted_count} old backup(s)")
            else:
                print(f"✓ No old backups to clean up")
                
        except Exception as e:
            print(f"✗ Error during cleanup: {str(e)}")
    
    def verify_backup(self, backup_path):
        """Verify backup integrity"""
        print(f"\nVerifying backup integrity...")
        
        try:
            if backup_path.endswith('.zip'):
                # Verify ZIP file
                with zipfile.ZipFile(backup_path, 'r') as zipf:
                    # Test ZIP file integrity
                    bad_file = zipf.testzip()
                    if bad_file:
                        print(f"✗ Backup verification failed: corrupted file {bad_file}")
                        return False
                    else:
                        print(f"✓ Backup verification successful")
                        return True
            else:
                # Verify directory exists and is readable
                if os.path.isdir(backup_path) and os.access(backup_path, os.R_OK):
                    print(f"✓ Backup verification successful")
                    return True
                else:
                    print(f"✗ Backup verification failed: directory not accessible")
                    return False
                    
        except Exception as e:
            print(f"✗ Backup verification failed: {str(e)}")
            return False


def main():
    """Main backup execution"""
    print("=" * 60)
    print("Sistema SGDI - File Storage Backup")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    backup = FileStorageBackup()
    
    # Create backup with compression
    success, backup_path = backup.create_backup(compression=True)
    
    if success and backup_path:
        # Verify backup
        backup.verify_backup(backup_path)
        
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
