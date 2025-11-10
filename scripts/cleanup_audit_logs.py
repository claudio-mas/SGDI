"""
Cleanup script for old audit logs
Archives or deletes audit logs older than retention period
"""
import os
import sys
import json
from datetime import datetime, timedelta

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.audit import LogAuditoria
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class AuditLogCleanup:
    """Handle cleanup and archival of old audit logs"""
    
    def __init__(self, app):
        self.app = app
        self.retention_days = int(os.environ.get('AUDIT_LOG_RETENTION_DAYS', 365))  # Default 1 year
        self.archive_dir = os.path.join(
            os.path.dirname(__file__), 
            '..', 
            'backups', 
            'audit_logs'
        )
        
        # Create archive directory if it doesn't exist
        os.makedirs(self.archive_dir, exist_ok=True)
    
    def get_old_logs(self):
        """Get audit logs older than retention period"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        with self.app.app_context():
            old_logs = LogAuditoria.query.filter(
                LogAuditoria.data_hora < cutoff_date
            ).all()
            
            return old_logs
    
    def archive_logs_to_json(self, logs):
        """Archive logs to JSON file"""
        if not logs:
            return None
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        archive_filename = f"audit_logs_archive_{timestamp}.json"
        archive_path = os.path.join(self.archive_dir, archive_filename)
        
        try:
            # Convert logs to dictionaries
            logs_data = []
            for log in logs:
                log_dict = {
                    'id': log.id,
                    'usuario_id': log.usuario_id,
                    'acao': log.acao,
                    'tabela': log.tabela,
                    'registro_id': log.registro_id,
                    'dados_json': log.dados_json,
                    'ip_address': log.ip_address,
                    'user_agent': log.user_agent,
                    'data_hora': log.data_hora.isoformat() if log.data_hora else None
                }
                logs_data.append(log_dict)
            
            # Write to JSON file
            with open(archive_path, 'w', encoding='utf-8') as f:
                json.dump(logs_data, f, indent=2, ensure_ascii=False)
            
            print(f"✓ Archived {len(logs)} log(s) to: {archive_filename}")
            
            # Get file size
            size_mb = os.path.getsize(archive_path) / (1024 * 1024)
            print(f"  Archive size: {size_mb:.2f} MB")
            
            return archive_path
            
        except Exception as e:
            print(f"✗ Error archiving logs: {str(e)}")
            return None
    
    def delete_logs(self, logs):
        """Delete logs from database"""
        try:
            for log in logs:
                db.session.delete(log)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"✗ Error deleting logs: {str(e)}")
            return False
    
    def get_log_statistics(self, logs):
        """Get statistics about logs to be archived"""
        if not logs:
            return {}
        
        stats = {
            'total_count': len(logs),
            'date_range': {
                'oldest': min(log.data_hora for log in logs),
                'newest': max(log.data_hora for log in logs)
            },
            'by_action': {},
            'by_user': {}
        }
        
        # Count by action
        for log in logs:
            action = log.acao or 'unknown'
            stats['by_action'][action] = stats['by_action'].get(action, 0) + 1
        
        # Count by user
        for log in logs:
            user_id = log.usuario_id or 0
            stats['by_user'][user_id] = stats['by_user'].get(user_id, 0) + 1
        
        return stats
    
    def cleanup(self, dry_run=False, archive=True):
        """Execute cleanup process"""
        print(f"Searching for audit logs older than {self.retention_days} days...")
        
        old_logs = self.get_old_logs()
        
        if not old_logs:
            print("✓ No old audit logs found")
            return 0
        
        print(f"Found {len(old_logs)} old log(s)\n")
        
        # Display statistics
        stats = self.get_log_statistics(old_logs)
        print("Log Statistics:")
        print(f"  Total logs: {stats['total_count']}")
        print(f"  Date range: {stats['date_range']['oldest'].strftime('%Y-%m-%d')} to {stats['date_range']['newest'].strftime('%Y-%m-%d')}")
        print(f"  Actions breakdown:")
        for action, count in sorted(stats['by_action'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"    - {action}: {count}")
        print()
        
        if dry_run:
            print(f"[DRY RUN] Would archive and delete {len(old_logs)} log(s)")
            return len(old_logs)
        
        # Archive logs if requested
        if archive:
            print("Archiving logs to JSON...")
            archive_path = self.archive_logs_to_json(old_logs)
            if not archive_path:
                print("✗ Archival failed - aborting cleanup")
                return 0
            print()
        
        # Delete logs from database
        print("Deleting logs from database...")
        if self.delete_logs(old_logs):
            print(f"✓ Successfully deleted {len(old_logs)} log(s)")
            return len(old_logs)
        else:
            print(f"✗ Failed to delete logs")
            return 0


def main():
    """Main cleanup execution"""
    print("=" * 60)
    print("Sistema SGDI - Audit Log Cleanup")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check for flags
    dry_run = '--dry-run' in sys.argv
    no_archive = '--no-archive' in sys.argv
    
    if dry_run:
        print("*** DRY RUN MODE - No changes will be made ***\n")
    
    if no_archive:
        print("*** Archive disabled - logs will be deleted without archiving ***\n")
    
    # Create Flask app context
    app = create_app(os.getenv('FLASK_ENV', 'production'))
    
    cleanup = AuditLogCleanup(app)
    deleted_count = cleanup.cleanup(dry_run=dry_run, archive=not no_archive)
    
    print("\n" + "=" * 60)
    print("Cleanup Summary")
    print("=" * 60)
    print(f"Logs processed: {deleted_count}")
    print("=" * 60)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
