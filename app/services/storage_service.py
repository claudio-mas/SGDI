"""
Storage service for file operations
Handles file saving, retrieval, and deletion with support for local filesystem storage
"""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, BinaryIO
from werkzeug.utils import secure_filename


class StorageService:
    """Service for managing file storage operations"""
    
    def __init__(self, upload_folder: str):
        """
        Initialize storage service
        
        Args:
            upload_folder: Base directory for file uploads
        """
        self.upload_folder = Path(upload_folder)
        self._ensure_upload_folder_exists()
    
    def _ensure_upload_folder_exists(self) -> None:
        """Create upload folder if it doesn't exist"""
        if not self.upload_folder.exists():
            self.upload_folder.mkdir(parents=True, exist_ok=True)
    
    def _generate_unique_filename(self, original_filename: str) -> str:
        """
        Generate a unique filename to prevent collisions
        
        Args:
            original_filename: Original name of the uploaded file
            
        Returns:
            Unique filename with timestamp and UUID
        """
        # Secure the filename to prevent directory traversal
        safe_filename = secure_filename(original_filename)
        
        # Extract extension
        name, ext = os.path.splitext(safe_filename)
        
        # Generate unique identifier
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = uuid.uuid4().hex[:8]
        
        # Construct unique filename: timestamp_uuid_originalname.ext
        unique_filename = f"{timestamp}_{unique_id}_{name}{ext}"
        
        return unique_filename
    
    def _get_user_folder(self, user_id: int) -> Path:
        """
        Get or create user-specific folder
        
        Args:
            user_id: ID of the user
            
        Returns:
            Path to user's folder
        """
        user_folder = self.upload_folder / str(user_id)
        if not user_folder.exists():
            user_folder.mkdir(parents=True, exist_ok=True)
        return user_folder
    
    def save_file(self, file: BinaryIO, original_filename: str, user_id: int) -> dict:
        """
        Save file to storage with unique filename
        
        Args:
            file: File object to save
            original_filename: Original name of the file
            user_id: ID of the user uploading the file
            
        Returns:
            Dictionary containing file path and unique filename
            {
                'file_path': 'relative/path/to/file',
                'unique_filename': 'generated_unique_name.ext',
                'original_filename': 'original_name.ext'
            }
        """
        # Generate unique filename
        unique_filename = self._generate_unique_filename(original_filename)
        
        # Get user folder
        user_folder = self._get_user_folder(user_id)
        
        # Construct full file path
        file_path = user_folder / unique_filename
        
        # Save file
        file.seek(0)  # Ensure we're at the beginning of the file
        with open(file_path, 'wb') as f:
            f.write(file.read())
        
        # Return relative path from upload folder
        relative_path = str(file_path.relative_to(self.upload_folder))
        
        return {
            'file_path': relative_path,
            'unique_filename': unique_filename,
            'original_filename': original_filename
        }
    
    def get_file(self, file_path: str) -> Optional[Path]:
        """
        Retrieve file from storage
        
        Args:
            file_path: Relative path to the file
            
        Returns:
            Full path to the file if it exists, None otherwise
        """
        full_path = self.upload_folder / file_path
        
        if full_path.exists() and full_path.is_file():
            return full_path
        
        return None
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete file from storage
        
        Args:
            file_path: Relative path to the file
            
        Returns:
            True if file was deleted, False otherwise
        """
        full_path = self.upload_folder / file_path
        
        try:
            if full_path.exists() and full_path.is_file():
                full_path.unlink()
                
                # Try to remove empty parent directories
                try:
                    full_path.parent.rmdir()
                except OSError:
                    # Directory not empty or other error, ignore
                    pass
                
                return True
        except Exception as e:
            # Log error but don't raise
            print(f"Error deleting file {file_path}: {e}")
            return False
        
        return False
    
    def file_exists(self, file_path: str) -> bool:
        """
        Check if file exists in storage
        
        Args:
            file_path: Relative path to the file
            
        Returns:
            True if file exists, False otherwise
        """
        full_path = self.upload_folder / file_path
        return full_path.exists() and full_path.is_file()
    
    def get_file_size(self, file_path: str) -> Optional[int]:
        """
        Get size of file in bytes
        
        Args:
            file_path: Relative path to the file
            
        Returns:
            File size in bytes, or None if file doesn't exist
        """
        full_path = self.upload_folder / file_path
        
        if full_path.exists() and full_path.is_file():
            return full_path.stat().st_size
        
        return None
