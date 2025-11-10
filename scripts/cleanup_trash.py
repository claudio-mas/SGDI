"""
Cleanup script for permanently deleting old trash items
Removes documents that have been in trash for more than 30 days
"""
import os
import sys
from datetime import datetime, timedelta

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.document import Documento
from config import Config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TrashCleanup:
    """Handle cleanup of old trash items"""
    
    def __init__(self, app):
        self.app = app
        self.retention_days = Config.TRASH_RETENTION_DAYS
    
    def get_expired_documents(self):
        """Get documents that have been in trash longer than retention period"""
        cutoff_date = datetime.utcnow() - timedelta(days=self.retention_days)
        
        with self.app.app_context():
            expired_docs = Documento.query.filter(
                Documento.status == 'excluido',
                Documento.data_exclusao.isnot(None),
                Documento.data_exclusao < cutoff_date
            ).all()
            
            return expired_docs
    
    def delete_file(self, file_path):
        """Delete physical file from storage"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                return True
            else:
                print(f"    Warning: File not found: {file_path}")
                return False
        except Exception as e:
            print(f"    Error deleting file: {str(e)}")
            return False
    
    def permanently_delete_document(self, documento):
        """Permanently delete document and its files"""
        try:
            # Delete main document file
            if documento.caminho_arquivo:
                self.delete_file(documento.caminho_arquivo)
            
            # Delete version files
            for versao in documento.versoes:
                if versao.caminho_arquivo:
                    self.delete_file(versao.caminho_arquivo)
            
            # Delete database record (cascade will handle related records)
            db.session.delete(documento)
            db.session.commit()
            
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"    Error deleting document from database: {str(e)}")
            return False
    
    def cleanup(self, dry_run=False):
        """Execute cleanup process"""
        print(f"Searching for documents in trash older than {self.retention_days} days...")
        
        expired_docs = self.get_expired_documents()
        
        if not expired_docs:
            print("✓ No expired documents found in trash")
            return 0
        
        print(f"Found {len(expired_docs)} expired document(s) to delete\n")
        
        deleted_count = 0
        failed_count = 0
        
        for doc in expired_docs:
            days_in_trash = (datetime.utcnow() - doc.data_exclusao).days
            
            print(f"Document: {doc.nome}")
            print(f"  ID: {doc.id}")
            print(f"  Deleted on: {doc.data_exclusao.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Days in trash: {days_in_trash}")
            print(f"  Size: {doc.tamanho_formatado}")
            
            if dry_run:
                print(f"  [DRY RUN] Would permanently delete this document")
                deleted_count += 1
            else:
                if self.permanently_delete_document(doc):
                    print(f"  ✓ Permanently deleted")
                    deleted_count += 1
                else:
                    print(f"  ✗ Failed to delete")
                    failed_count += 1
            
            print()
        
        return deleted_count, failed_count


def main():
    """Main cleanup execution"""
    print("=" * 60)
    print("Sistema SGDI - Trash Cleanup")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check for dry-run flag
    dry_run = '--dry-run' in sys.argv
    if dry_run:
        print("*** DRY RUN MODE - No changes will be made ***\n")
    
    # Create Flask app context
    app = create_app(os.getenv('FLASK_ENV', 'production'))
    
    cleanup = TrashCleanup(app)
    result = cleanup.cleanup(dry_run=dry_run)
    
    if isinstance(result, tuple):
        deleted_count, failed_count = result
        print("=" * 60)
        print("Cleanup Summary")
        print("=" * 60)
        print(f"Successfully deleted: {deleted_count}")
        print(f"Failed to delete: {failed_count}")
        print("=" * 60)
        print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        return 0 if failed_count == 0 else 1
    else:
        print("=" * 60)
        print("Cleanup completed - no documents to delete")
        print("=" * 60)
        return 0


if __name__ == '__main__':
    sys.exit(main())
