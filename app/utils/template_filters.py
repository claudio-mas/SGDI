"""
Template filters for Jinja2 templates
"""


def get_file_icon(extension):
    """
    Get Font Awesome icon class for file extension
    
    Args:
        extension: File extension (e.g., '.pdf', '.docx')
        
    Returns:
        Font Awesome icon class string
    """
    if not extension:
        return 'fa-file'
    
    ext = extension.lower().lstrip('.')
    
    icon_map = {
        'pdf': 'fa-file-pdf text-danger',
        'doc': 'fa-file-word text-primary',
        'docx': 'fa-file-word text-primary',
        'xls': 'fa-file-excel text-success',
        'xlsx': 'fa-file-excel text-success',
        'jpg': 'fa-file-image text-info',
        'jpeg': 'fa-file-image text-info',
        'png': 'fa-file-image text-info',
        'tif': 'fa-file-image text-info',
        'tiff': 'fa-file-image text-info',
        'zip': 'fa-file-archive text-warning',
        'rar': 'fa-file-archive text-warning',
        'txt': 'fa-file-alt',
        'csv': 'fa-file-csv text-success',
    }
    
    return icon_map.get(ext, 'fa-file')


def format_file_size(bytes_size):
    """
    Format file size in human-readable format
    
    Args:
        bytes_size: Size in bytes
        
    Returns:
        Formatted string (e.g., '1.5 MB')
    """
    if not bytes_size:
        return '0 B'
    
    size = float(bytes_size)
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def register_filters(app):
    """
    Register custom template filters with Flask app
    
    Args:
        app: Flask application instance
    """
    app.jinja_env.filters['get_file_icon'] = get_file_icon
    app.jinja_env.filters['format_file_size'] = format_file_size
