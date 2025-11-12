"""
Cleanup script for expired password reset tokens
Removes expired and used password reset tokens from database
"""
import os
import sys
from datetime import datetime

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.user import PasswordReset
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TokenCleanup:
    """Handle cleanup of expired password reset tokens"""
    
    def __init__(self, app):
        self.app = app
    
    def get_expired_tokens(self):
        """Get expired password reset tokens"""
        with self.app.app_context():
            expired_tokens = PasswordReset.query.filter(
                PasswordReset.expiracao < datetime.utcnow()
            ).all()
            
            return expired_tokens
    
    def get_used_tokens(self):
        """Get used password reset tokens"""
        with self.app.app_context():
            used_tokens = PasswordReset.query.filter(
                PasswordReset.usado == True
            ).all()
            
            return used_tokens
    
    def delete_tokens(self, tokens):
        """Delete tokens from database"""
        try:
            for token in tokens:
                db.session.delete(token)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting tokens: {str(e)}")
            return False
    
    def cleanup(self, dry_run=False, include_used=True):
        """Execute cleanup process"""
        print("Searching for expired password reset tokens...")
        
        expired_tokens = self.get_expired_tokens()
        used_tokens = self.get_used_tokens() if include_used else []
        
        # Combine and deduplicate
        all_tokens = list(set(expired_tokens + used_tokens))
        
        if not all_tokens:
            print("✓ No expired or used tokens found")
            return 0
        
        print(f"Found {len(all_tokens)} token(s) to delete")
        print(f"  - Expired: {len(expired_tokens)}")
        if include_used:
            print(f"  - Used: {len(used_tokens)}")
        print()
        
        # Group tokens by status for reporting
        expired_count = 0
        used_count = 0
        
        for token in all_tokens:
            is_expired = token.expiracao < datetime.utcnow()
            is_used = token.usado
            
            status_parts = []
            if is_expired:
                status_parts.append("expired")
                expired_count += 1
            if is_used:
                status_parts.append("used")
                used_count += 1
            
            status = " & ".join(status_parts)
            
            print(f"Token: {token.token[:20]}...")
            print(f"  User ID: {token.usuario_id}")
            print(f"  Created: {token.data_criacao.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Expires: {token.expiracao.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"  Status: {status}")
            
            if dry_run:
                print(f"  [DRY RUN] Would delete this token")
            else:
                print(f"  ✓ Marked for deletion")
            
            print()
        
        if not dry_run:
            if self.delete_tokens(all_tokens):
                print(f"✓ Successfully deleted {len(all_tokens)} token(s)")
                return len(all_tokens)
            else:
                print(f"✗ Failed to delete tokens")
                return 0
        else:
            print(f"[DRY RUN] Would delete {len(all_tokens)} token(s)")
            return len(all_tokens)


def main():
    """Main cleanup execution"""
    print("=" * 60)
    print("SGDI - Password Reset Token Cleanup")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Check for flags
    dry_run = '--dry-run' in sys.argv
    include_used = '--include-used' not in sys.argv or '--include-used' in sys.argv
    
    if dry_run:
        print("*** DRY RUN MODE - No changes will be made ***\n")
    
    # Create Flask app context
    app = create_app(os.getenv('FLASK_ENV', 'production'))
    
    cleanup = TokenCleanup(app)
    deleted_count = cleanup.cleanup(dry_run=dry_run, include_used=include_used)
    
    print("=" * 60)
    print("Cleanup Summary")
    print("=" * 60)
    print(f"Tokens deleted: {deleted_count}")
    print("=" * 60)
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
