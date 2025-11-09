# Error Handling Quick Reference

## Quick Exception Guide

### When to Use Each Exception

| Exception | Use When | HTTP Status |
|-----------|----------|-------------|
| `InvalidCredentialsError` | Login fails due to wrong password | 401 |
| `AccountBlockedError` | Account locked after failed attempts | 403 |
| `SessionExpiredError` | User session has expired | 401 |
| `PermissionDeniedError` | User lacks permission for action | 403 |
| `InsufficientPrivilegesError` | User role insufficient | 403 |
| `InvalidFileTypeError` | File type not allowed | 400 |
| `FileSizeExceededError` | File too large | 400 |
| `DuplicateDocumentError` | Document already exists | 409 |
| `DocumentNotFoundError` | Document doesn't exist | 404 |
| `UserNotFoundError` | User doesn't exist | 404 |
| `FileUploadError` | Upload failed | 500 |
| `FileDownloadError` | Download failed | 500 |

## Common Patterns

### Pattern 1: Service Method with Validation

```python
from app.errors import ValidationError, NotFoundError

def update_document(self, doc_id, data, user_id):
    # Log start
    current_app.logger.info(f'Updating document {doc_id}')
    
    # Validate
    document = self.repository.get_by_id(doc_id)
    if not document:
        raise DocumentNotFoundError()
    
    if not self._has_permission(document, user_id, 'edit'):
        raise PermissionDeniedError()
    
    # Process
    document.update(data)
    self.repository.save(document)
    
    # Log success
    current_app.logger.info(f'Document {doc_id} updated successfully')
    
    return document
```

### Pattern 2: Controller with Error Handling

```python
@document_bp.route('/<int:id>/edit', methods=['POST'])
@login_required
def edit_document(id):
    try:
        data = request.form.to_dict()
        document = document_service.update_document(id, data, current_user.id)
        flash('Documento atualizado com sucesso', 'success')
        return redirect(url_for('document.view_document', id=id))
        
    except DocumentNotFoundError:
        flash('Documento não encontrado', 'error')
        return redirect(url_for('document.list_documents'))
        
    except PermissionDeniedError:
        flash('Sem permissão para editar', 'error')
        return redirect(url_for('document.view_document', id=id))
        
    except ValidationError as e:
        flash(str(e.message), 'error')
        return redirect(url_for('document.edit_form', id=id))
```

### Pattern 3: API Endpoint

```python
@api_bp.route('/documents/<int:id>', methods=['DELETE'])
@login_required
def delete_document_api(id):
    try:
        document_service.delete_document(id, current_user.id)
        return jsonify({'message': 'Documento excluído'}), 200
        
    except DocumentNotFoundError as e:
        return jsonify({'error': e.message}), 404
        
    except PermissionDeniedError as e:
        return jsonify({'error': e.message}), 403
        
    except Exception as e:
        current_app.logger.error(f'API error: {str(e)}')
        return jsonify({'error': 'Erro interno'}), 500
```

## Logging Quick Reference

### Log Levels

```python
# DEBUG - Detailed diagnostic info
current_app.logger.debug(f'Processing file: {filename}')

# INFO - General information
current_app.logger.info(f'User {user_id} logged in')

# WARNING - Something unexpected but not an error
current_app.logger.warning(f'Storage at 80% capacity')

# ERROR - Serious problem
current_app.logger.error(f'Failed to save document: {error}')

# CRITICAL - Very serious problem
current_app.logger.critical(f'Database connection lost')
```

### Logging with Context

```python
# Simple message
current_app.logger.info('Document uploaded')

# With context
current_app.logger.info(
    f'Document uploaded | '
    f'User: {user_id} | '
    f'Size: {file_size} | '
    f'Type: {mime_type}'
)

# With timing
from app.utils.logging_config import RequestLogger

with RequestLogger(current_app.logger, 'process_upload', user_id=user.id):
    process_file(file)
```

## Flash Message Categories

Use consistent categories for user feedback:

```python
flash('Operação bem-sucedida', 'success')  # Green
flash('Atenção necessária', 'warning')     # Yellow
flash('Erro ao processar', 'error')        # Red
flash('Informação importante', 'info')     # Blue
```

## Testing Error Handlers

```python
def test_document_not_found(client):
    response = client.get('/documents/99999')
    assert response.status_code == 404
    assert b'não encontrado' in response.data

def test_permission_denied(client, regular_user):
    client.login(regular_user)
    response = client.delete('/documents/1')
    assert response.status_code == 403
```

## Checklist for New Features

- [ ] Add appropriate logging at key points
- [ ] Use specific exceptions for error cases
- [ ] Handle exceptions in controllers
- [ ] Provide user-friendly error messages
- [ ] Log errors with context
- [ ] Test error scenarios
- [ ] Document error conditions
