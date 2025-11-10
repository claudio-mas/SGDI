# Permission System Developer Guide

## Overview

The Sistema SGDI permission system provides fine-grained access control for documents. This guide explains how to use the PermissionService in your code.

## Permission Types

The system supports four permission types:

| Permission Type | Description | Implies |
|----------------|-------------|---------|
| `visualizar` | View document | - |
| `editar` | Edit document metadata and create versions | `visualizar` |
| `excluir` | Delete document | `visualizar` |
| `compartilhar` | Share document with others | `visualizar` |

**Note:** Document owners automatically have all permissions without explicit grants.

## Quick Start

### Import the Service

```python
from app.services.permission_service import PermissionService

permission_service = PermissionService()
```

### Check if User Has Permission

```python
# Check if user can view a document
if permission_service.check_permission(documento, user_id, 'visualizar'):
    # Allow access
    pass
else:
    # Deny access
    raise PermissionDeniedError("You don't have permission to view this document")
```

### Grant Permission to User

```python
from datetime import datetime, timedelta

# Grant edit permission with 30-day expiration
permission = permission_service.grant_permission(
    documento=documento,
    target_user_id=recipient_user_id,
    permission_type='editar',
    granted_by_user_id=current_user_id,
    expiration_date=datetime.utcnow() + timedelta(days=30)
)
```

### Share Document (Multiple Permissions)

```python
# Share document with view and edit permissions
permissions = permission_service.share_document(
    documento=documento,
    target_user_id=recipient_user_id,
    permission_types=['visualizar', 'editar'],
    shared_by_user_id=current_user_id,
    expiration_days=30,  # Optional
    send_notification=True  # Send email notification
)
```

### Revoke Permission

```python
# Revoke specific permission
success = permission_service.revoke_permission(
    documento=documento,
    target_user_id=user_id,
    permission_type='editar',
    revoked_by_user_id=current_user_id
)

# Revoke all permissions (unshare)
count = permission_service.unshare_document(
    documento=documento,
    target_user_id=user_id,
    unshared_by_user_id=current_user_id
)
```

## Common Use Cases

### Controller Route Protection

```python
from flask import abort
from flask_login import current_user
from app.services.permission_service import PermissionService

@document_bp.route('/<int:document_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_document(document_id):
    documento = DocumentRepository().get_by_id(document_id)
    if not documento:
        abort(404)
    
    # Check permission
    permission_service = PermissionService()
    if not permission_service.check_permission(documento, current_user.id, 'editar'):
        abort(403)
    
    # Process edit...
```

### List Documents User Can Access

```python
# Get documents shared with user
shared_docs = permission_service.get_shared_with_me(
    user_id=current_user.id,
    permission_type='visualizar'  # Optional filter
)

# Get documents user has shared
shared_by_me = permission_service.get_shared_by_me(
    user_id=current_user.id
)
```

### View Document Permissions

```python
# Get all permissions for a document (owner or share permission required)
permissions = permission_service.get_document_permissions(
    documento=documento,
    user_id=current_user.id
)

for perm in permissions:
    print(f"{perm['user_name']} has {perm['permission_type']} permission")
    if perm['expiration_date']:
        print(f"  Expires: {perm['expiration_date']}")
```

### Cleanup Expired Permissions

```python
# Run periodically (e.g., daily cron job)
count = permission_service.cleanup_expired_permissions()
print(f"Removed {count} expired permissions")
```

## Permission Inheritance Rules

1. **Document Owner**: Has all permissions automatically
2. **Explicit Grants**: Permissions explicitly granted to users
3. **Permission Hierarchy**: Higher permissions imply lower ones
   - `editar`, `excluir`, or `compartilhar` → implies `visualizar`

## Authorization Rules

### Who Can Grant Permissions?
- Document owner can grant any permission
- Users with `compartilhar` permission can grant permissions to others

### Who Can Revoke Permissions?
- Document owner can revoke any permission
- Users with `compartilhar` permission can revoke permissions

### Who Can View Permissions?
- Document owner
- Users with `compartilhar` permission

## Error Handling

The service raises specific exceptions:

```python
from app.services.permission_service import (
    PermissionServiceError,
    PermissionDeniedError,
    InvalidPermissionTypeError
)

try:
    permission_service.grant_permission(...)
except PermissionDeniedError:
    # User doesn't have authority to grant permission
    flash("You don't have permission to share this document", "error")
except InvalidPermissionTypeError:
    # Invalid permission type provided
    flash("Invalid permission type", "error")
except PermissionServiceError as e:
    # Other permission-related errors
    flash(str(e), "error")
```

## Best Practices

### 1. Always Check Permissions

```python
# ✅ Good
if permission_service.check_permission(documento, user_id, 'visualizar'):
    return send_file(file_path)
else:
    abort(403)

# ❌ Bad - No permission check
return send_file(file_path)
```

### 2. Use Appropriate Permission Types

```python
# ✅ Good - Check specific permission needed
if permission_service.check_permission(documento, user_id, 'editar'):
    documento.nome = new_name
    db.session.commit()

# ❌ Bad - Checking wrong permission
if permission_service.check_permission(documento, user_id, 'visualizar'):
    documento.nome = new_name  # Should require 'editar'
```

### 3. Set Expiration for Temporary Access

```python
# ✅ Good - Temporary access with expiration
permission_service.share_document(
    documento=documento,
    target_user_id=contractor_id,
    permission_types=['visualizar'],
    shared_by_user_id=current_user.id,
    expiration_days=7  # Access expires in 7 days
)

# ⚠️ Acceptable - Permanent access (use with caution)
permission_service.share_document(
    documento=documento,
    target_user_id=team_member_id,
    permission_types=['visualizar', 'editar'],
    shared_by_user_id=current_user.id
    # No expiration
)
```

### 4. Send Notifications When Sharing

```python
# ✅ Good - User is notified
permission_service.share_document(
    documento=documento,
    target_user_id=user_id,
    permission_types=['visualizar'],
    shared_by_user_id=current_user.id,
    send_notification=True
)
```

### 5. Clean Up Expired Permissions Regularly

```python
# Add to scheduled tasks (e.g., daily cron job)
from app.services.permission_service import PermissionService

def cleanup_expired_permissions():
    """Daily cleanup task"""
    permission_service = PermissionService()
    count = permission_service.cleanup_expired_permissions()
    logger.info(f"Cleaned up {count} expired permissions")
```

## Integration with DocumentService

The DocumentService already uses permission checking internally:

```python
from app.services.document_service import DocumentService

document_service = DocumentService(storage_service, file_handler)

# These methods automatically check permissions:
documento = document_service.get_document(document_id, user_id)  # Checks 'visualizar'
document_service.update_document_metadata(document_id, user_id, ...)  # Checks 'editar'
document_service.delete_document(document_id, user_id)  # Checks 'excluir'
```

## Database Schema

The `permissoes` table structure:

```sql
CREATE TABLE permissoes (
    id INT PRIMARY KEY,
    documento_id INT NOT NULL,
    usuario_id INT NOT NULL,
    tipo_permissao VARCHAR(20) NOT NULL,  -- visualizar, editar, excluir, compartilhar
    data_concessao DATETIME NOT NULL,
    concedido_por INT NOT NULL,
    data_expiracao DATETIME NULL,  -- Optional expiration
    UNIQUE (documento_id, usuario_id, tipo_permissao)
);
```

## Performance Considerations

1. **Permission checks are fast**: Simple database queries with indexes
2. **Owner checks are instant**: No database query needed
3. **Expired permissions**: Automatically filtered in checks
4. **Batch operations**: Use `share_document()` for multiple permission types

## Testing

Example test cases:

```python
def test_owner_has_all_permissions():
    doc = create_test_document(owner_id=1)
    assert permission_service.check_permission(doc, 1, 'visualizar')
    assert permission_service.check_permission(doc, 1, 'editar')
    assert permission_service.check_permission(doc, 1, 'excluir')
    assert permission_service.check_permission(doc, 1, 'compartilhar')

def test_non_owner_without_permission():
    doc = create_test_document(owner_id=1)
    assert not permission_service.check_permission(doc, 2, 'visualizar')

def test_grant_and_check_permission():
    doc = create_test_document(owner_id=1)
    permission_service.grant_permission(doc, 2, 'visualizar', 1)
    assert permission_service.check_permission(doc, 2, 'visualizar')

def test_expired_permission():
    doc = create_test_document(owner_id=1)
    past_date = datetime.utcnow() - timedelta(days=1)
    permission_service.grant_permission(doc, 2, 'visualizar', 1, past_date)
    assert not permission_service.check_permission(doc, 2, 'visualizar')
```

## Troubleshooting

### Permission Check Returns False Unexpectedly

1. Verify user is not the owner
2. Check if permission was granted
3. Check if permission has expired
4. Verify permission type is correct

### Cannot Grant Permission

1. Verify granting user is owner or has 'compartilhar' permission
2. Check target user exists and is active
3. Verify permission type is valid

### Shared Document Not Visible

1. Check permission hasn't expired
2. Verify document status is 'ativo'
3. Check user has at least 'visualizar' permission

## Support

For questions or issues with the permission system:
- Review this guide
- Check `docs/TASK_8_IMPLEMENTATION_SUMMARY.md`
- Review the source code in `app/services/permission_service.py`
