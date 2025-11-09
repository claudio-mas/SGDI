"""
Backup configuration for Sistema GED
Centralized configuration for backup operations
"""
import os
from dotenv import load_dotenv

load_dotenv()


class BackupConfig:
    """Backup configuration settings"""
    
    # Backup directories
    BACKUP_BASE_DIR = os.environ.get('BACKUP_DIR', os.path.join(os.path.dirname(__file__), '..', 'backups'))
    DATABASE_BACKUP_DIR = os.path.join(BACKUP_BASE_DIR, 'database')
    FILES_BACKUP_DIR = os.path.join(BACKUP_BASE_DIR, 'files')
    
    # Retention settings (in days)
    DATABASE_RETENTION_DAYS = int(os.environ.get('DATABASE_RETENTION_DAYS', 90))
    FILES_RETENTION_DAYS = int(os.environ.get('FILES_RETENTION_DAYS', 90))
    
    # Backup options
    COMPRESS_FILE_BACKUPS = os.environ.get('COMPRESS_FILE_BACKUPS', 'True').lower() == 'true'
    VERIFY_BACKUPS = os.environ.get('VERIFY_BACKUPS', 'True').lower() == 'true'
    
    # Notification settings
    SEND_BACKUP_NOTIFICATIONS = os.environ.get('SEND_BACKUP_NOTIFICATIONS', 'False').lower() == 'true'
    BACKUP_NOTIFICATION_EMAIL = os.environ.get('BACKUP_NOTIFICATION_EMAIL', '')
    
    # Backup schedule (for documentation purposes)
    # Actual scheduling should be done via cron (Linux) or Task Scheduler (Windows)
    SCHEDULE = {
        'database': {
            'frequency': 'daily',
            'time': '02:00',  # 2 AM
            'description': 'Daily database backup at 2 AM'
        },
        'files': {
            'frequency': 'weekly',
            'day': 'Sunday',
            'time': '03:00',  # 3 AM
            'description': 'Weekly file storage backup on Sunday at 3 AM'
        },
        'full': {
            'frequency': 'weekly',
            'day': 'Sunday',
            'time': '02:00',  # 2 AM
            'description': 'Weekly complete backup on Sunday at 2 AM'
        }
    }
    
    @classmethod
    def get_cron_schedule(cls):
        """Get cron schedule examples"""
        return {
            'database_daily': '0 2 * * * cd /path/to/sistema-ged && python scripts/backup_database.py',
            'files_weekly': '0 3 * * 0 cd /path/to/sistema-ged && python scripts/backup_files.py',
            'full_weekly': '0 2 * * 0 cd /path/to/sistema-ged && python scripts/backup_all.py'
        }
    
    @classmethod
    def get_windows_task_schedule(cls):
        """Get Windows Task Scheduler examples"""
        return {
            'database_daily': {
                'trigger': 'Daily at 2:00 AM',
                'action': 'python C:\\path\\to\\sistema-ged\\scripts\\backup_database.py',
                'description': 'Daily database backup for Sistema GED'
            },
            'files_weekly': {
                'trigger': 'Weekly on Sunday at 3:00 AM',
                'action': 'python C:\\path\\to\\sistema-ged\\scripts\\backup_files.py',
                'description': 'Weekly file storage backup for Sistema GED'
            },
            'full_weekly': {
                'trigger': 'Weekly on Sunday at 2:00 AM',
                'action': 'python C:\\path\\to\\sistema-ged\\scripts\\backup_all.py',
                'description': 'Weekly complete backup for Sistema GED'
            }
        }
