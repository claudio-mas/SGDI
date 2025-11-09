# Logging and Error Handling - Sistema GED

## Overview

This document describes the logging and error handling implementation for Sistema GED, covering application logging, error handlers, and custom exceptions.

## Application Logging

### Configuration

The logging system is configured in `app/utils/logging_config.py` and automatically initialized when the Flask application starts.

### Log Files

All log files are stored in the `logs/` directory:

- **ged_system.log**: Main application log with all events (rotating, 10MB max, 10 backups)
- **ged_errors.log**: Error-only log for critical issues (rotating, 10MB max, 10 backups)

### Log Levels by Environment

- **Development**: DEBUG level (all messages logged, includes console output)
- **Testing**: WARNING level (only warnings and errors)
- **Production**: INFO level (informational messages and above)

### Log Format

```
[YYYY-MM-DD HH:MM:SS] LEVEL in module (function:line): message
```

Example:
```
[2024-11-08 14:30:45] INFO in auth (login:45): User 123 logged in successfully
```

### Usage in Code

```python
from flask import current_app

# Log informational message
current_app.logger.info('Document uploaded successfully')

# Log warning
current_app.logger.warning('File size approaching limit')

# Log error
current_app.logger.error('Failed to save document')

# Log with context
current_app.logger.info(f'User {user_id} accessed document {doc_id}')
```

### Request Logging

All HTTP requests are automatically logged with:
- Request method and path
- User ID (or 'anonymous')
- IP address
- Response status code

### Operation Logging with Context Manager

For timing and tracking operations:

```python
from app.utils.logging_config import RequestLogger
from flask import current_app

with RequestLogger(current_app.logger, 'upload_document', user_id=user.id, document_id=doc.id):
    # Your operation code here
    process_upload(file)
```

This logs:
- Operation start with context
- Operation completion with duration
- Operation failure with error details

## Error Handling

### Custom Exception Hierarchy

```
GEDException (Base)
├── AuthenticationError
│   ├── InvalidCredentialsError
│   ├── AccountBlockedError
│   └── SessionExpiredError
├── AuthorizationError
│   ├── PermissionDeniedError
│   └── InsufficientPrivilegesError
├── ValidationError
│   ├── InvalidFileTypeError
│   ├── FileSizeExceededError
│   └── DuplicateDocumentError
├── NotFoundError
│   ├── DocumentNotFoundError
│   └── UserNotFoundError
└── StorageError
    ├── FileUploadError
    └── FileDownloadError
```

### Using Custom Exceptions

```python
from app.errors import DocumentNotFoundError, PermissionDeniedError

# Raise specific exception
if not document:
    raise DocumentNotFoundError(f'Document {doc_id} not found')

# Raise with custom message
if not has_permission(user, document):
    raise PermissionDeniedError('You cannot edit this document')
```

### HTTP Error Handlers

The system handles the following HTTP errors with custom pages:

- **404 Not Found**: Resource doesn't exist
- **403 Forbidden**: Access denied
- **429 Too Many Requests**: Rate limit exceeded
- **500 Internal Server Error**: Unexpected error

### Error Pages

All error pages are located in `app/templates/errors/`:
- `404.html` - Not found page
- `403.html` - Forbidden page
- `429.html` - Rate limit page
- `500.html` - Internal error page

Each error page includes:
- Clear error message
- User-friendly explanation
- Action buttons (return home, retry, etc.)
- Contextual help based on authentication status

### Error Logging

All errors are automatically logged with:
- Error type and message
- Request details (method, path)
- User information
- IP address
- Full stack trace (for 500 errors)

### JSON API Error Responses

For API requests (JSON), errors return structured responses:

```json
{
  "error": "Error message in Portuguese"
}
```

Status codes match the error type:
- 400: Validation errors
- 401: Authentication errors
- 403: Authorization errors
- 404: Not found errors
- 409: Conflict errors (duplicates)
- 500: Server errors

## Best Practices

### Logging

1. **Use appropriate log levels**:
   - DEBUG: Detailed diagnostic information
   - INFO: General informational messages
   - WARNING: Warning messages for potentially harmful situations
   - ERROR: Error messages for serious problems
   - CRITICAL: Critical messages for very serious errors

2. **Include context**: Always log relevant context (user ID, document ID, etc.)

3. **Don't log sensitive data**: Never log passwords, tokens, or personal information

4. **Use structured logging**: Include key-value pairs for easier parsing

### Error Handling

1. **Catch specific exceptions**: Use specific exception types rather than generic Exception

2. **Provide helpful messages**: Error messages should be clear and actionable

3. **Log before raising**: Log the error with context before raising it

4. **Clean up resources**: Use try-finally or context managers to ensure cleanup

5. **Don't expose internals**: Error messages to users should not reveal system internals

## Monitoring and Maintenance

### Log Rotation

Logs automatically rotate when they reach 10MB, keeping 10 backup files. This prevents disk space issues.

### Log Analysis

To analyze logs:

```bash
# View recent errors
tail -f logs/ged_errors.log

# Search for specific user activity
grep "User: 123" logs/ged_system.log

# Count errors by type
grep "ERROR" logs/ged_system.log | cut -d' ' -f4 | sort | uniq -c
```

### Cleanup

Old log backups can be manually deleted if needed:

```bash
# Remove logs older than 90 days
find logs/ -name "*.log.*" -mtime +90 -delete
```

## Troubleshooting

### Logs not being created

1. Check that the `logs/` directory exists and is writable
2. Verify file permissions
3. Check disk space

### Too many log files

1. Adjust `maxBytes` in `logging_config.py` to increase rotation size
2. Reduce `backupCount` to keep fewer backups
3. Implement automated cleanup

### Performance issues

1. Reduce log level in production (use INFO instead of DEBUG)
2. Disable request logging for static files (already implemented)
3. Consider async logging for high-traffic scenarios

## Examples

### Service Layer with Logging

```python
from flask import current_app
from app.errors import DocumentNotFoundError, PermissionDeniedError

class DocumentService:
    def delete_document(self, document_id, user_id):
        current_app.logger.info(f'Attempting to delete document {document_id} by user {user_id}')
        
        try:
            document = self.repository.get_by_id(document_id)
            if not document:
                raise DocumentNotFoundError(f'Document {document_id} not found')
            
            if not self._has_permission(document, user_id, 'delete'):
                raise PermissionDeniedError('User does not have delete permission')
            
            document.soft_delete()
            self.repository.save(document)
            
            current_app.logger.info(f'Document {document_id} deleted successfully by user {user_id}')
            
        except Exception as e:
            current_app.logger.error(f'Failed to delete document {document_id}: {str(e)}')
            raise
```

### Controller with Error Handling

```python
from flask import current_app, flash, redirect, url_for
from app.errors import DocumentNotFoundError, PermissionDeniedError

@document_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_document(id):
    try:
        document_service.delete_document(id, current_user.id)
        flash('Documento excluído com sucesso', 'success')
        return redirect(url_for('document.list_documents'))
        
    except DocumentNotFoundError:
        flash('Documento não encontrado', 'error')
        return redirect(url_for('document.list_documents'))
        
    except PermissionDeniedError:
        flash('Você não tem permissão para excluir este documento', 'error')
        return redirect(url_for('document.view_document', id=id))
        
    except Exception as e:
        current_app.logger.error(f'Unexpected error deleting document {id}: {str(e)}')
        flash('Erro ao excluir documento', 'error')
        return redirect(url_for('document.view_document', id=id))
```

## Configuration

### Environment Variables

No additional environment variables are required. Logging is configured based on the Flask environment:

- `FLASK_ENV=development` - Debug logging with console output
- `FLASK_ENV=production` - Info logging to files only
- `FLASK_ENV=testing` - Warning logging only

### Customization

To customize logging behavior, edit `app/utils/logging_config.py`:

- Change log file names
- Adjust rotation size and backup count
- Modify log format
- Add additional handlers (e.g., email alerts, Sentry)

## Integration with Audit System

The logging system complements the audit system (`log_auditoria` table):

- **Application logs**: Technical events, errors, performance
- **Audit logs**: Business events, user actions, compliance

Both systems work together to provide complete visibility into system operations.
