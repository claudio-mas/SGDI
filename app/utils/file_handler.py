"""
File validation utilities
Handles file validation including MIME type verification, size checks, and hash generation
"""
import hashlib
import os
from typing import Optional, BinaryIO, Set
from werkzeug.datastructures import FileStorage


class FileValidationError(Exception):
    """Base exception for file validation errors"""
    pass


class InvalidFileTypeError(FileValidationError):
    """Raised when file type is not allowed"""
    pass


class FileSizeExceededError(FileValidationError):
    """Raised when file size exceeds limit"""
    pass


class FileHandler:
    """Handler for file validation operations"""
    
    def __init__(self, allowed_extensions: Set[str], max_file_size: int):
        """
        Initialize file handler
        
        Args:
            allowed_extensions: Set of allowed file extensions (without dot)
            max_file_size: Maximum file size in bytes
        """
        self.allowed_extensions = {ext.lower() for ext in allowed_extensions}
        self.max_file_size = max_file_size
    
    def _get_file_extension(self, filename: str) -> str:
        """
        Extract file extension from filename
        
        Args:
            filename: Name of the file
            
        Returns:
            File extension without dot (lowercase)
        """
        if '.' not in filename:
            return ''
        return filename.rsplit('.', 1)[1].lower()
    
    def validate_extension(self, filename: str) -> bool:
        """
        Check if file extension is allowed
        
        Args:
            filename: Name of the file
            
        Returns:
            True if extension is allowed
            
        Raises:
            InvalidFileTypeError: If extension is not allowed
        """
        extension = self._get_file_extension(filename)
        
        if not extension:
            raise InvalidFileTypeError("File has no extension")
        
        if extension not in self.allowed_extensions:
            raise InvalidFileTypeError(
                f"File type '.{extension}' is not allowed. "
                f"Allowed types: {', '.join(sorted(self.allowed_extensions))}"
            )
        
        return True
    
    def validate_file_size(self, file: BinaryIO) -> bool:
        """
        Check if file size is within limit
        
        Args:
            file: File object to validate
            
        Returns:
            True if size is valid
            
        Raises:
            FileSizeExceededError: If file size exceeds limit
        """
        # Get current position
        current_pos = file.tell()
        
        # Seek to end to get size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        
        # Return to original position
        file.seek(current_pos)
        
        if file_size > self.max_file_size:
            max_size_mb = self.max_file_size / (1024 * 1024)
            actual_size_mb = file_size / (1024 * 1024)
            raise FileSizeExceededError(
                f"File size ({actual_size_mb:.2f}MB) exceeds maximum allowed size ({max_size_mb:.2f}MB)"
            )
        
        return True
    
    def verify_mime_type(self, file: BinaryIO, filename: str) -> str:
        """
        Verify MIME type of file using python-magic
        Falls back to extension-based detection if python-magic is not available
        
        Args:
            file: File object to verify
            filename: Name of the file
            
        Returns:
            MIME type string
        """
        try:
            import magic
            
            # Get current position
            current_pos = file.tell()
            
            # Read first 2048 bytes for magic detection
            file.seek(0)
            file_header = file.read(2048)
            
            # Return to original position
            file.seek(current_pos)
            
            # Detect MIME type
            mime = magic.from_buffer(file_header, mime=True)
            return mime
            
        except ImportError:
            # python-magic not available, fall back to extension-based detection
            return self._get_mime_from_extension(filename)
    
    def _get_mime_from_extension(self, filename: str) -> str:
        """
        Get MIME type based on file extension
        
        Args:
            filename: Name of the file
            
        Returns:
            MIME type string
        """
        extension = self._get_file_extension(filename)
        
        # Common MIME types mapping
        mime_types = {
            'pdf': 'application/pdf',
            'doc': 'application/msword',
            'docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            'xls': 'application/vnd.ms-excel',
            'xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'tif': 'image/tiff',
            'tiff': 'image/tiff',
        }
        
        return mime_types.get(extension, 'application/octet-stream')
    
    def calculate_hash(self, file: BinaryIO) -> str:
        """
        Calculate SHA256 hash of file for duplicate detection
        
        Args:
            file: File object to hash
            
        Returns:
            SHA256 hash as hexadecimal string
        """
        # Get current position
        current_pos = file.tell()
        
        # Calculate hash
        file.seek(0)
        sha256_hash = hashlib.sha256()
        
        # Read file in chunks to handle large files
        chunk_size = 8192
        while True:
            chunk = file.read(chunk_size)
            if not chunk:
                break
            sha256_hash.update(chunk)
        
        # Return to original position
        file.seek(current_pos)
        
        return sha256_hash.hexdigest()
    
    def validate_file(self, file: BinaryIO, filename: str) -> dict:
        """
        Perform complete file validation
        
        Args:
            file: File object to validate
            filename: Name of the file
            
        Returns:
            Dictionary with validation results:
            {
                'valid': True,
                'mime_type': 'application/pdf',
                'file_hash': 'abc123...',
                'file_size': 1024000
            }
            
        Raises:
            FileValidationError: If validation fails
        """
        # Validate extension
        self.validate_extension(filename)
        
        # Validate file size
        self.validate_file_size(file)
        
        # Get MIME type
        mime_type = self.verify_mime_type(file, filename)
        
        # Calculate hash
        file_hash = self.calculate_hash(file)
        
        # Get file size
        current_pos = file.tell()
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(current_pos)
        
        return {
            'valid': True,
            'mime_type': mime_type,
            'file_hash': file_hash,
            'file_size': file_size
        }
    
    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format
        
        Args:
            size_bytes: Size in bytes
            
        Returns:
            Formatted string (e.g., "1.5 MB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
