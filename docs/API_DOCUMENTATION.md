# API Documentation - Sistema GED

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Common Patterns](#common-patterns)
- [Authentication Endpoints](#authentication-endpoints)
- [Document Endpoints](#document-endpoints)
- [Category Endpoints](#category-endpoints)
- [Search Endpoints](#search-endpoints)
- [Workflow Endpoints](#workflow-endpoints)
- [Admin Endpoints](#admin-endpoints)
- [Error Responses](#error-responses)

## Overview

Sistema GED provides a web-based API for electronic document management. All endpoints return HTML pages for browser consumption, with some API endpoints returning JSON for AJAX requests.

### Base URL

```
Development: http://localhost:5000
Production: https://your-domain.com
```

### Content Types

- **HTML Endpoints**: Return rendered HTML pages
- **API Endpoints**: Return JSON data (prefixed with `/api/`)

### Response Formats

**HTML Responses**: Standard web pages with navigation
**JSON Responses**: 
```json
{
  "success": true,
  "data": {},
  "message": "Operation successful"
}
```

## Authentication

### Authentication Method

Sistema GED uses **session-based authentication** with Flask-Login.

### Login Flow

1. User submits credentials to `/auth/login`
2. Server validates credentials and creates session
3. Session cookie is set in browser
4. Subsequent requests include session cookie
5. Server validates session on each request

### Session Management

- **Session Duration**: 24 hours (configurable)
- **Remember Me**: Optional 30-day session
- **Session Cookie**: HTTP-only, Secure (in production)
- **CSRF Protection**: Required for all POST/PUT/DELETE requests

### Required Headers

```http
Cookie: session=<session-cookie>
X-CSRFToken: <csrf-token>  # For state-changing operations
```


## Common Patterns

### Pagination

List endpoints support pagination with query parameters:

```
?page=1&per_page=20
```

**Parameters:**
- `page` (integer): Page number (default: 1)
- `per_page` (integer): Items per page (default: 20, max: 100)

**Response includes:**
- `items`: Array of results
- `total`: Total number of items
- `page`: Current page
- `per_page`: Items per page
- `pages`: Total number of pages

### Filtering

Many endpoints support filtering with query parameters:

```
?status=ativo&categoria_id=5&data_inicio=2024-01-01
```

### Sorting

List endpoints support sorting:

```
?sort=data_upload&order=desc
```

**Parameters:**
- `sort`: Field to sort by
- `order`: `asc` or `desc` (default: `asc`)

### Flash Messages

After operations, flash messages are displayed:
- **success**: Green notification
- **info**: Blue notification
- **warning**: Yellow notification
- **danger**: Red notification

### Permission Requirements

Endpoints are protected by decorators:
- `@login_required`: User must be authenticated
- `@admin_required`: User must have Administrator profile
- `@permission_required('action')`: User must have specific permission


---

## Authentication Endpoints

### POST /auth/login

Authenticate user and create session.

**Authentication**: None (public)

**Request Body** (form-data):
```
email: string (required)
password: string (required)
remember_me: boolean (optional)
```

**Success Response** (302 Redirect):
```
Location: /documents/
Set-Cookie: session=...
```

**Error Response** (200 with error message):
```html
<!-- Login page with error message -->
```

**Example**:
```bash
curl -X POST http://localhost:5000/auth/login \
  -d "email=user@example.com" \
  -d "password=password123" \
  -d "remember_me=true"
```

**Validation**:
- Email must be valid format
- Password required
- Account must be active
- Account must not be locked

**Brute Force Protection**:
- 5 failed attempts → Account locked for 15 minutes
- Lockout message displayed

---

### GET /auth/logout

Logout user and destroy session.

**Authentication**: Required

**Success Response** (302 Redirect):
```
Location: /auth/login
```

**Example**:
```bash
curl -X GET http://localhost:5000/auth/logout \
  -b "session=..."
```

---

### GET /auth/register

Display registration page.

**Authentication**: None (public)

**Response**: HTML registration form

---

### POST /auth/reset-password

Request password reset token.

**Authentication**: None (public)

**Request Body** (form-data):
```
email: string (required)
```

**Success Response** (302 Redirect):
```
Location: /auth/login
Flash: "Password reset email sent"
```

**Example**:
```bash
curl -X POST http://localhost:5000/auth/reset-password \
  -d "email=user@example.com"
```

**Process**:
1. Validates email exists
2. Generates secure token (1 hour expiration)
3. Sends email with reset link
4. Redirects to login

---

### GET /auth/reset-password/<token>

Display password reset form.

**Authentication**: None (public)

**URL Parameters**:
- `token` (string): Password reset token

**Response**: HTML password reset form

**Validation**:
- Token must be valid
- Token must not be expired
- Token must not be used

---

### POST /auth/reset-password/<token>

Complete password reset.

**Authentication**: None (public)

**URL Parameters**:
- `token` (string): Password reset token

**Request Body** (form-data):
```
password: string (required, min 8 chars)
password_confirm: string (required, must match)
```

**Success Response** (302 Redirect):
```
Location: /auth/login
Flash: "Password reset successful"
```

---

### GET /auth/profile

View user profile.

**Authentication**: Required

**Response**: HTML profile page with user information

**Data Displayed**:
- Name
- Email
- Profile/Role
- Last access
- Registration date

---

### GET /auth/profile/edit

Display profile edit form.

**Authentication**: Required

**Response**: HTML profile edit form

---

### POST /auth/profile/edit

Update user profile.

**Authentication**: Required

**Request Body** (form-data):
```
nome: string (required)
email: string (required, valid email)
```

**Success Response** (302 Redirect):
```
Location: /auth/profile
Flash: "Profile updated successfully"
```

---

### GET /auth/profile/change-password

Display password change form.

**Authentication**: Required

**Response**: HTML password change form

---

### POST /auth/profile/change-password

Change user password.

**Authentication**: Required

**Request Body** (form-data):
```
current_password: string (required)
new_password: string (required, min 8 chars)
new_password_confirm: string (required, must match)
```

**Success Response** (302 Redirect):
```
Location: /auth/profile
Flash: "Password changed successfully"
```

**Validation**:
- Current password must be correct
- New password must meet strength requirements
- New password must be different from current


---

## Document Endpoints

### GET /documents/

List all documents accessible to the user.

**Authentication**: Required

**Query Parameters**:
```
page: integer (default: 1)
per_page: integer (default: 20)
status: string (ativo, arquivado, excluido)
categoria_id: integer
sort: string (nome, data_upload, tamanho)
order: string (asc, desc)
```

**Response**: HTML page with document list

**Example**:
```bash
curl -X GET "http://localhost:5000/documents/?page=1&per_page=20&status=ativo" \
  -b "session=..."
```

---

### GET /documents/upload

Display document upload form.

**Authentication**: Required

**Response**: HTML upload form with Dropzone.js

---

### POST /documents/upload

Upload one or more documents.

**Authentication**: Required

**Request Body** (multipart/form-data):
```
files[]: file[] (required, max 10 files)
nome[]: string[] (required for each file)
descricao[]: string[] (optional)
categoria_id[]: integer[] (required)
tags[]: string[] (optional, comma-separated)
pasta_id[]: integer[] (optional)
```

**Success Response** (302 Redirect):
```
Location: /documents/
Flash: "X documents uploaded successfully"
```

**Example**:
```bash
curl -X POST http://localhost:5000/documents/upload \
  -b "session=..." \
  -F "files[]=@document.pdf" \
  -F "nome[]=Contract 2024" \
  -F "descricao[]=Annual contract" \
  -F "categoria_id[]=1" \
  -F "tags[]=contract,2024"
```

**Validation**:
- File type must be allowed (PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, TIF)
- File size must be ≤ 50MB
- Maximum 10 files per upload
- Duplicate detection via SHA256 hash

**Process**:
1. Validates each file
2. Calculates SHA256 hash
3. Checks for duplicates
4. Generates unique filename
5. Saves file to storage
6. Creates database record
7. Processes tags
8. Logs upload action

---

### GET /documents/<id>

View document details.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Document ID

**Response**: HTML document detail page

**Data Displayed**:
- Document metadata
- Version history
- Permissions
- Preview (for PDF/images)
- Download button
- Edit/Delete buttons (if permitted)

**Example**:
```bash
curl -X GET http://localhost:5000/documents/123 \
  -b "session=..."
```

**Permission Check**: User must have 'visualizar' permission

---

### GET /documents/<id>/download

Download document file.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Document ID

**Success Response** (200):
```
Content-Type: application/octet-stream
Content-Disposition: attachment; filename="document.pdf"
[Binary file data]
```

**Example**:
```bash
curl -X GET http://localhost:5000/documents/123/download \
  -b "session=..." \
  -o document.pdf
```

**Process**:
1. Validates permission
2. Logs download action
3. Streams file to client

---

### POST /documents/<id>/delete

Soft delete document (move to trash).

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Document ID

**Success Response** (302 Redirect):
```
Location: /documents/
Flash: "Document moved to trash"
```

**Example**:
```bash
curl -X POST http://localhost:5000/documents/123/delete \
  -b "session=..." \
  -H "X-CSRFToken: ..."
```

**Permission Check**: User must have 'excluir' permission

**Process**:
1. Sets status to 'excluido'
2. Sets data_exclusao to current timestamp
3. Keeps file for 30 days
4. Logs deletion action

---

### POST /documents/<id>/restore

Restore document from trash.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Document ID

**Success Response** (302 Redirect):
```
Location: /documents/
Flash: "Document restored successfully"
```

**Example**:
```bash
curl -X POST http://localhost:5000/documents/123/restore \
  -b "session=..." \
  -H "X-CSRFToken: ..."
```

**Permission Check**: User must be document owner or admin

---

### POST /documents/bulk-delete

Delete multiple documents.

**Authentication**: Required

**Request Body** (form-data):
```
document_ids[]: integer[] (required)
```

**Success Response** (302 Redirect):
```
Location: /documents/
Flash: "X documents deleted"
```

**Example**:
```bash
curl -X POST http://localhost:5000/documents/bulk-delete \
  -b "session=..." \
  -H "X-CSRFToken: ..." \
  -d "document_ids[]=123" \
  -d "document_ids[]=124"
```

---

### GET /documents/<id>/preview

Preview document (PDF/image).

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Document ID

**Response**: HTML preview page with embedded viewer

**Supported Formats**:
- PDF: Embedded PDF viewer
- Images (JPG, PNG): Image display
- Other formats: Download link only

---

### POST /documents/<id>/upload-version

Upload new version of document.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Document ID

**Request Body** (multipart/form-data):
```
file: file (required)
comentario: string (required)
```

**Success Response** (302 Redirect):
```
Location: /documents/<id>
Flash: "New version uploaded"
```

**Example**:
```bash
curl -X POST http://localhost:5000/documents/123/upload-version \
  -b "session=..." \
  -H "X-CSRFToken: ..." \
  -F "file=@document_v2.pdf" \
  -F "comentario=Updated contract terms"
```

**Validation**:
- File type must match original
- Maximum 10 versions per document
- Comment is required

---

### POST /documents/<id>/restore-version/<version_number>

Restore previous version.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Document ID
- `version_number` (integer): Version number to restore

**Success Response** (302 Redirect):
```
Location: /documents/<id>
Flash: "Version restored"
```

---

### GET /documents/<id>/edit

Display document edit form.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Document ID

**Response**: HTML edit form

**Permission Check**: User must have 'editar' permission

---

### POST /documents/<id>/edit

Update document metadata.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Document ID

**Request Body** (form-data):
```
nome: string (required)
descricao: string (optional)
categoria_id: integer (required)
tags: string (optional, comma-separated)
pasta_id: integer (optional)
```

**Success Response** (302 Redirect):
```
Location: /documents/<id>
Flash: "Document updated"
```

**Example**:
```bash
curl -X POST http://localhost:5000/documents/123/edit \
  -b "session=..." \
  -H "X-CSRFToken: ..." \
  -d "nome=Updated Contract" \
  -d "descricao=Updated description" \
  -d "categoria_id=1" \
  -d "tags=contract,2024,updated"
```


---

## Category Endpoints

### GET /categories/

List all categories.

**Authentication**: Required

**Response**: HTML page with category list (hierarchical tree)

**Example**:
```bash
curl -X GET http://localhost:5000/categories/ \
  -b "session=..."
```

---

### GET /categories/new

Display category creation form.

**Authentication**: Required

**Response**: HTML category form

---

### POST /categories/new

Create new category.

**Authentication**: Required

**Request Body** (form-data):
```
nome: string (required, unique)
descricao: string (optional)
categoria_pai_id: integer (optional)
icone: string (optional)
cor: string (optional, hex color)
```

**Success Response** (302 Redirect):
```
Location: /categories/
Flash: "Category created"
```

**Example**:
```bash
curl -X POST http://localhost:5000/categories/new \
  -b "session=..." \
  -H "X-CSRFToken: ..." \
  -d "nome=Financial" \
  -d "descricao=Financial documents" \
  -d "cor=#FF5733"
```

---

### GET /categories/<id>/edit

Display category edit form.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Category ID

**Response**: HTML edit form

---

### POST /categories/<id>/edit

Update category.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Category ID

**Request Body** (form-data):
```
nome: string (required)
descricao: string (optional)
categoria_pai_id: integer (optional)
icone: string (optional)
cor: string (optional)
```

**Success Response** (302 Redirect):
```
Location: /categories/
Flash: "Category updated"
```

---

### POST /categories/<id>/delete

Delete category.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Category ID

**Success Response** (302 Redirect):
```
Location: /categories/
Flash: "Category deleted"
```

**Validation**:
- Category must not have documents
- Category must not have subcategories

---

### GET /categories/<id>

View category details and documents.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Category ID

**Response**: HTML page with category info and document list

---

### GET /categories/folders

List all folders.

**Authentication**: Required

**Response**: HTML page with folder tree

---

### GET /categories/folders/new

Display folder creation form.

**Authentication**: Required

**Response**: HTML folder form

---

### POST /categories/folders/new

Create new folder.

**Authentication**: Required

**Request Body** (form-data):
```
nome: string (required)
descricao: string (optional)
pasta_pai_id: integer (optional)
```

**Success Response** (302 Redirect):
```
Location: /categories/folders
Flash: "Folder created"
```

---

### GET /categories/folders/<id>/edit

Display folder edit form.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Folder ID

**Response**: HTML edit form

---

### POST /categories/folders/<id>/edit

Update folder.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Folder ID

**Request Body** (form-data):
```
nome: string (required)
descricao: string (optional)
pasta_pai_id: integer (optional)
```

**Success Response** (302 Redirect):
```
Location: /categories/folders
Flash: "Folder updated"
```

---

### POST /categories/folders/<id>/delete

Delete folder.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Folder ID

**Success Response** (302 Redirect):
```
Location: /categories/folders
Flash: "Folder deleted"
```

**Validation**:
- Folder must be empty (no documents)
- Folder must not have subfolders

---

### GET /categories/folders/<id>

View folder contents.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Folder ID

**Response**: HTML page with folder documents

---

### GET /categories/api/categories/hierarchy

Get category hierarchy as JSON.

**Authentication**: Required

**Response** (200 JSON):
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "nome": "Contracts",
      "children": [
        {
          "id": 2,
          "nome": "Vendor Contracts",
          "children": []
        }
      ]
    }
  ]
}
```

---

### GET /categories/api/folders/hierarchy

Get folder hierarchy as JSON.

**Authentication**: Required

**Response** (200 JSON):
```json
{
  "success": true,
  "data": [
    {
      "id": 1,
      "nome": "Projects",
      "children": [
        {
          "id": 2,
          "nome": "Project A",
          "children": []
        }
      ]
    }
  ]
}
```


---

## Search Endpoints

### GET /search/

Simple search.

**Authentication**: Required

**Query Parameters**:
```
q: string (required, search query)
page: integer (default: 1)
per_page: integer (default: 20)
```

**Response**: HTML search results page

**Example**:
```bash
curl -X GET "http://localhost:5000/search/?q=contract&page=1" \
  -b "session=..."
```

**Search Scope**:
- Document name
- Document description
- Tags

---

### GET /search/advanced

Advanced search with filters.

**Authentication**: Required

**Query Parameters**:
```
q: string (optional)
categoria_id: integer (optional)
data_inicio: date (optional, YYYY-MM-DD)
data_fim: date (optional, YYYY-MM-DD)
usuario_id: integer (optional)
tipo_arquivo: string (optional)
tamanho_min: integer (optional, bytes)
tamanho_max: integer (optional, bytes)
tags: string (optional, comma-separated)
page: integer (default: 1)
per_page: integer (default: 20)
sort: string (optional)
order: string (optional, asc/desc)
```

**Response**: HTML advanced search results

**Example**:
```bash
curl -X GET "http://localhost:5000/search/advanced?q=contract&categoria_id=1&data_inicio=2024-01-01&data_fim=2024-12-31" \
  -b "session=..."
```

---

### GET /search/fulltext

Full-text search in document content.

**Authentication**: Required

**Query Parameters**:
```
q: string (required)
page: integer (default: 1)
per_page: integer (default: 20)
```

**Response**: HTML full-text search results

**Example**:
```bash
curl -X GET "http://localhost:5000/search/fulltext?q=confidential" \
  -b "session=..."
```

**Note**: Only searches PDF content that has been indexed

---

### GET /search/quick/<filter_type>

Quick filter presets.

**Authentication**: Required

**URL Parameters**:
- `filter_type` (string): Filter type
  - `my-documents`: Documents owned by user
  - `recent`: Recently uploaded (last 7 days)
  - `favorites`: Favorited documents
  - `pending-approval`: Documents pending approval

**Query Parameters**:
```
page: integer (default: 1)
per_page: integer (default: 20)
```

**Response**: HTML filtered results

**Example**:
```bash
curl -X GET http://localhost:5000/search/quick/my-documents \
  -b "session=..."
```

---

### GET /search/api/suggestions

Get search suggestions (autocomplete).

**Authentication**: Required

**Query Parameters**:
```
q: string (required, partial query)
limit: integer (default: 10)
```

**Response** (200 JSON):
```json
{
  "success": true,
  "suggestions": [
    {
      "type": "document",
      "id": 123,
      "text": "Annual Contract 2024",
      "category": "Contracts"
    },
    {
      "type": "tag",
      "text": "contract"
    }
  ]
}
```

**Example**:
```bash
curl -X GET "http://localhost:5000/search/api/suggestions?q=cont&limit=5" \
  -b "session=..."
```

---

### GET /search/api/tags/autocomplete

Get tag suggestions.

**Authentication**: Required

**Query Parameters**:
```
q: string (required, partial tag)
limit: integer (default: 10)
```

**Response** (200 JSON):
```json
{
  "success": true,
  "tags": [
    "contract",
    "contractor",
    "contractual"
  ]
}
```

**Example**:
```bash
curl -X GET "http://localhost:5000/search/api/tags/autocomplete?q=cont" \
  -b "session=..."
```

---

### GET /search/api/categories/autocomplete

Get category suggestions.

**Authentication**: Required

**Query Parameters**:
```
q: string (required, partial category name)
limit: integer (default: 10)
```

**Response** (200 JSON):
```json
{
  "success": true,
  "categories": [
    {
      "id": 1,
      "nome": "Contracts",
      "caminho_completo": "Legal > Contracts"
    }
  ]
}
```


---

## Workflow Endpoints

### GET /workflows/

List all workflows.

**Authentication**: Required

**Response**: HTML page with workflow list

**Example**:
```bash
curl -X GET http://localhost:5000/workflows/ \
  -b "session=..."
```

---

### GET /workflows/new

Display workflow creation form.

**Authentication**: Required

**Response**: HTML workflow form

---

### POST /workflows/new

Create new workflow.

**Authentication**: Required

**Request Body** (form-data):
```
nome: string (required)
descricao: string (optional)
configuracao_json: string (required, JSON)
ativo: boolean (default: true)
```

**Configuration JSON Format**:
```json
{
  "stages": [
    {
      "name": "Manager Approval",
      "approvers": [5, 6],
      "required_approvals": 1
    },
    {
      "name": "Director Approval",
      "approvers": [2],
      "required_approvals": 1
    }
  ]
}
```

**Success Response** (302 Redirect):
```
Location: /workflows/
Flash: "Workflow created"
```

**Example**:
```bash
curl -X POST http://localhost:5000/workflows/new \
  -b "session=..." \
  -H "X-CSRFToken: ..." \
  -d "nome=Contract Approval" \
  -d "descricao=Two-stage approval" \
  -d 'configuracao_json={"stages":[...]}'
```

---

### GET /workflows/<id>/edit

Display workflow edit form.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Workflow ID

**Response**: HTML edit form

---

### POST /workflows/<id>/edit

Update workflow.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Workflow ID

**Request Body** (form-data):
```
nome: string (required)
descricao: string (optional)
configuracao_json: string (required, JSON)
ativo: boolean
```

**Success Response** (302 Redirect):
```
Location: /workflows/
Flash: "Workflow updated"
```

---

### POST /workflows/<id>/toggle

Activate/deactivate workflow.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Workflow ID

**Success Response** (302 Redirect):
```
Location: /workflows/
Flash: "Workflow activated/deactivated"
```

---

### GET /workflows/approvals

List pending approvals for current user.

**Authentication**: Required

**Response**: HTML page with pending approvals

**Example**:
```bash
curl -X GET http://localhost:5000/workflows/approvals \
  -b "session=..."
```

---

### GET /workflows/approval/<id>

View approval details.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Approval ID

**Response**: HTML approval detail page

**Data Displayed**:
- Document information
- Workflow stages
- Current stage
- Approval history
- Approve/Reject buttons

---

### POST /workflows/approval/<id>/approve

Approve document.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Approval ID

**Request Body** (form-data):
```
comentario: string (required)
```

**Success Response** (302 Redirect):
```
Location: /workflows/approvals
Flash: "Document approved"
```

**Example**:
```bash
curl -X POST http://localhost:5000/workflows/approval/123/approve \
  -b "session=..." \
  -H "X-CSRFToken: ..." \
  -d "comentario=Approved - all terms acceptable"
```

**Process**:
1. Validates user is approver
2. Records approval with comment
3. Checks if stage is complete
4. Advances to next stage or completes workflow
5. Sends notifications
6. Logs action

---

### POST /workflows/approval/<id>/reject

Reject document.

**Authentication**: Required

**URL Parameters**:
- `id` (integer): Approval ID

**Request Body** (form-data):
```
comentario: string (required)
```

**Success Response** (302 Redirect):
```
Location: /workflows/approvals
Flash: "Document rejected"
```

**Example**:
```bash
curl -X POST http://localhost:5000/workflows/approval/123/reject \
  -b "session=..." \
  -H "X-CSRFToken: ..." \
  -d "comentario=Rejected - terms need revision"
```

**Process**:
1. Validates user is approver
2. Records rejection with comment
3. Marks workflow as rejected
4. Notifies submitter
5. Logs action


---

## Admin Endpoints

### GET /admin/dashboard

View admin dashboard.

**Authentication**: Required (Administrator only)

**Response**: HTML dashboard with statistics

**Data Displayed**:
- Total documents
- Total users
- Storage used
- Recent uploads
- System activity chart

**Example**:
```bash
curl -X GET http://localhost:5000/admin/dashboard \
  -b "session=..."
```

---

### GET /admin/users

List all users.

**Authentication**: Required (Administrator only)

**Query Parameters**:
```
page: integer (default: 1)
per_page: integer (default: 20)
search: string (optional)
perfil_id: integer (optional)
ativo: boolean (optional)
```

**Response**: HTML user list page

**Example**:
```bash
curl -X GET "http://localhost:5000/admin/users?search=john&ativo=true" \
  -b "session=..."
```

---

### GET /admin/users/create

Display user creation form.

**Authentication**: Required (Administrator only)

**Response**: HTML user form

---

### POST /admin/users/create

Create new user.

**Authentication**: Required (Administrator only)

**Request Body** (form-data):
```
nome: string (required)
email: string (required, unique, valid email)
senha: string (required, min 8 chars)
perfil_id: integer (required)
ativo: boolean (default: true)
```

**Success Response** (302 Redirect):
```
Location: /admin/users
Flash: "User created successfully"
```

**Example**:
```bash
curl -X POST http://localhost:5000/admin/users/create \
  -b "session=..." \
  -H "X-CSRFToken: ..." \
  -d "nome=John Doe" \
  -d "email=john@example.com" \
  -d "senha=SecurePass123" \
  -d "perfil_id=3"
```

---

### GET /admin/users/<user_id>/edit

Display user edit form.

**Authentication**: Required (Administrator only)

**URL Parameters**:
- `user_id` (integer): User ID

**Response**: HTML edit form

---

### POST /admin/users/<user_id>/edit

Update user.

**Authentication**: Required (Administrator only)

**URL Parameters**:
- `user_id` (integer): User ID

**Request Body** (form-data):
```
nome: string (required)
email: string (required, valid email)
perfil_id: integer (required)
ativo: boolean
```

**Success Response** (302 Redirect):
```
Location: /admin/users
Flash: "User updated successfully"
```

---

### POST /admin/users/<user_id>/toggle-status

Activate/deactivate user.

**Authentication**: Required (Administrator only)

**URL Parameters**:
- `user_id` (integer): User ID

**Success Response** (302 Redirect):
```
Location: /admin/users
Flash: "User activated/deactivated"
```

**Example**:
```bash
curl -X POST http://localhost:5000/admin/users/5/toggle-status \
  -b "session=..." \
  -H "X-CSRFToken: ..."
```

---

### GET /admin/users/<user_id>/reset-password

Display password reset form.

**Authentication**: Required (Administrator only)

**URL Parameters**:
- `user_id` (integer): User ID

**Response**: HTML password reset form

---

### POST /admin/users/<user_id>/reset-password

Reset user password.

**Authentication**: Required (Administrator only)

**URL Parameters**:
- `user_id` (integer): User ID

**Request Body** (form-data):
```
nova_senha: string (required, min 8 chars)
nova_senha_confirm: string (required, must match)
```

**Success Response** (302 Redirect):
```
Location: /admin/users
Flash: "Password reset successfully"
```

---

### GET /admin/settings

Display system settings.

**Authentication**: Required (Administrator only)

**Response**: HTML settings form

---

### POST /admin/settings

Update system settings.

**Authentication**: Required (Administrator only)

**Request Body** (form-data):
```
max_file_size: integer (bytes)
allowed_extensions: string (comma-separated)
session_timeout: integer (minutes)
enable_email_notifications: boolean
smtp_server: string
smtp_port: integer
smtp_username: string
smtp_password: string
```

**Success Response** (302 Redirect):
```
Location: /admin/settings
Flash: "Settings updated"
```

---

### GET /admin/reports

View reports dashboard.

**Authentication**: Required (Administrator only)

**Response**: HTML reports page with links to different reports

---

### GET /admin/reports/usage

Usage report.

**Authentication**: Required (Administrator only)

**Query Parameters**:
```
data_inicio: date (optional, YYYY-MM-DD)
data_fim: date (optional, YYYY-MM-DD)
format: string (optional, html/pdf/excel)
```

**Response**: HTML report or file download

**Example**:
```bash
curl -X GET "http://localhost:5000/admin/reports/usage?data_inicio=2024-01-01&data_fim=2024-12-31&format=pdf" \
  -b "session=..." \
  -o usage_report.pdf
```

**Report Data**:
- Total uploads per day/week/month
- Most active users
- Most accessed documents
- Storage growth

---

### GET /admin/reports/access

Access report.

**Authentication**: Required (Administrator only)

**Query Parameters**:
```
data_inicio: date (optional)
data_fim: date (optional)
usuario_id: integer (optional)
documento_id: integer (optional)
format: string (optional)
```

**Response**: HTML report or file download

**Report Data**:
- Document access logs
- Download statistics
- User activity
- Peak usage times

---

### GET /admin/reports/storage

Storage report.

**Authentication**: Required (Administrator only)

**Query Parameters**:
```
format: string (optional, html/pdf/excel)
```

**Response**: HTML report or file download

**Report Data**:
- Storage by user
- Storage by category
- Storage by file type
- Total storage used
- Storage trends

---

### GET /admin/audit/logs

View audit logs.

**Authentication**: Required (Administrator only)

**Query Parameters**:
```
page: integer (default: 1)
per_page: integer (default: 50)
data_inicio: date (optional)
data_fim: date (optional)
usuario_id: integer (optional)
acao: string (optional)
tabela: string (optional)
```

**Response**: HTML audit log list

**Example**:
```bash
curl -X GET "http://localhost:5000/admin/audit/logs?acao=upload&data_inicio=2024-01-01" \
  -b "session=..."
```

---

### GET /admin/audit/logs/<log_id>

View audit log details.

**Authentication**: Required (Administrator only)

**URL Parameters**:
- `log_id` (integer): Log ID

**Response**: HTML log detail page

---

### GET /admin/audit/document/<documento_id>

View document audit trail.

**Authentication**: Required (Administrator only)

**URL Parameters**:
- `documento_id` (integer): Document ID

**Response**: HTML audit trail for specific document

**Data Displayed**:
- All operations on document
- User who performed each action
- Timestamps
- IP addresses
- Changes made

---

### GET /admin/audit/user/<usuario_id>

View user activity.

**Authentication**: Required (Administrator only)

**URL Parameters**:
- `usuario_id` (integer): User ID

**Response**: HTML user activity page

**Data Displayed**:
- All actions by user
- Login history
- Documents accessed
- Operations performed

---

### GET /admin/audit/recent

View recent activity.

**Authentication**: Required (Administrator only)

**Query Parameters**:
```
limit: integer (default: 100)
```

**Response**: HTML recent activity page

---

### GET /admin/audit/statistics

View audit statistics.

**Authentication**: Required (Administrator only)

**Response**: HTML statistics page with charts

**Data Displayed**:
- Operations by type
- Activity by user
- Activity by time
- Most accessed documents

---

### GET /admin/audit/export

Export audit logs.

**Authentication**: Required (Administrator only)

**Query Parameters**:
```
data_inicio: date (required)
data_fim: date (required)
format: string (required, csv/excel)
usuario_id: integer (optional)
acao: string (optional)
```

**Response**: File download

**Example**:
```bash
curl -X GET "http://localhost:5000/admin/audit/export?data_inicio=2024-01-01&data_fim=2024-12-31&format=excel" \
  -b "session=..." \
  -o audit_logs.xlsx
```

---

### GET /admin/audit/reports/<report_type>

Generate specific audit report.

**Authentication**: Required (Administrator only)

**URL Parameters**:
- `report_type` (string): Report type
  - `login-failures`: Failed login attempts
  - `permission-changes`: Permission modifications
  - `deletions`: Deleted documents
  - `downloads`: Document downloads

**Query Parameters**:
```
data_inicio: date (optional)
data_fim: date (optional)
format: string (optional)
```

**Response**: HTML report or file download

---

### GET /admin/audit/login-history

View login history.

**Authentication**: Required (Administrator only)

**Query Parameters**:
```
page: integer (default: 1)
per_page: integer (default: 50)
usuario_id: integer (optional)
data_inicio: date (optional)
data_fim: date (optional)
```

**Response**: HTML login history page

**Data Displayed**:
- Login timestamps
- IP addresses
- Success/failure status
- User agents
- Lockout events


---

## Error Responses

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 302 | Found | Redirect (common after POST operations) |
| 400 | Bad Request | Invalid request parameters |
| 401 | Unauthorized | Authentication required |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 413 | Payload Too Large | File size exceeds limit |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server error |

### Error Page Format

**HTML Error Pages**:

Sistema GED provides custom error pages for common errors:

- **403 Forbidden**: Access denied page
- **404 Not Found**: Page not found
- **500 Internal Server Error**: Server error page

Each error page includes:
- Error code and message
- Helpful description
- Link to return to home
- Contact information

### Flash Message Format

Flash messages are displayed at the top of pages after operations:

**Success** (green):
```html
<div class="alert alert-success">
  Operation completed successfully
</div>
```

**Error** (red):
```html
<div class="alert alert-danger">
  Error: Operation failed
</div>
```

**Warning** (yellow):
```html
<div class="alert alert-warning">
  Warning: Please review
</div>
```

**Info** (blue):
```html
<div class="alert alert-info">
  Information message
</div>
```

### Common Error Messages

**Authentication Errors**:
- "Invalid email or password"
- "Account is locked. Try again in X minutes"
- "Account is inactive. Contact administrator"
- "Session expired. Please login again"

**Permission Errors**:
- "You don't have permission to perform this action"
- "Access denied"
- "Administrator privileges required"

**Validation Errors**:
- "File type not allowed"
- "File size exceeds maximum (50MB)"
- "Invalid file format"
- "Duplicate document detected"
- "Required field missing"
- "Invalid email format"
- "Password must be at least 8 characters"

**Resource Errors**:
- "Document not found"
- "User not found"
- "Category not found"
- "Workflow not found"

**Operation Errors**:
- "Cannot delete category with documents"
- "Cannot delete folder with contents"
- "Maximum versions (10) reached"
- "Document is locked for editing"
- "Workflow already completed"

### API Error Response Format

For JSON API endpoints (prefixed with `/api/`):

**Error Response**:
```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input parameters",
    "details": {
      "field": "email",
      "reason": "Invalid email format"
    }
  }
}
```

**Error Codes**:
- `AUTHENTICATION_ERROR`: Authentication failed
- `AUTHORIZATION_ERROR`: Insufficient permissions
- `VALIDATION_ERROR`: Input validation failed
- `NOT_FOUND`: Resource not found
- `DUPLICATE_ERROR`: Duplicate resource
- `STORAGE_ERROR`: File storage error
- `DATABASE_ERROR`: Database operation failed
- `RATE_LIMIT_ERROR`: Too many requests

---

## Rate Limiting

### Limits

- **General Requests**: 100 requests per minute per IP
- **Login Attempts**: 5 attempts per 15 minutes per IP
- **Upload Requests**: 20 uploads per hour per user
- **Search Requests**: 60 searches per minute per user

### Rate Limit Headers

Responses include rate limit information:

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640000000
```

### Rate Limit Exceeded Response

**Status**: 429 Too Many Requests

**HTML Response**: Error page with retry information

**JSON Response**:
```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_ERROR",
    "message": "Too many requests",
    "retry_after": 60
  }
}
```

---

## Security Considerations

### CSRF Protection

All state-changing operations (POST, PUT, DELETE) require CSRF token:

**In Forms**:
```html
<form method="POST">
  {{ form.csrf_token }}
  <!-- form fields -->
</form>
```

**In AJAX**:
```javascript
$.ajax({
  url: '/documents/123/delete',
  method: 'POST',
  headers: {
    'X-CSRFToken': getCsrfToken()
  }
});
```

### HTTPS

**Production**: HTTPS is enforced
- All HTTP requests redirect to HTTPS
- Secure cookies enabled
- HSTS header set

**Development**: HTTP allowed for local testing

### Session Security

- **HTTP-Only Cookies**: Prevents XSS attacks
- **Secure Flag**: HTTPS only (production)
- **SameSite**: Lax (CSRF protection)
- **Session Timeout**: 24 hours (configurable)

### File Upload Security

- **Type Validation**: MIME type verification
- **Size Limit**: 50MB maximum
- **Virus Scanning**: Recommended (not implemented)
- **Unique Filenames**: Prevents overwrites
- **Hash Verification**: SHA256 for duplicates

### SQL Injection Prevention

- **Parameterized Queries**: All database queries
- **ORM Usage**: SQLAlchemy prevents injection
- **Input Validation**: All user inputs validated

### XSS Prevention

- **Output Encoding**: Jinja2 auto-escaping
- **Input Sanitization**: HTML tags stripped
- **CSP Headers**: Content Security Policy

---

## Best Practices

### Authentication

1. Always check session validity
2. Implement proper logout
3. Use strong passwords
4. Enable "Remember Me" carefully
5. Monitor failed login attempts

### File Operations

1. Validate file types before upload
2. Check file size limits
3. Use unique filenames
4. Implement proper error handling
5. Log all file operations

### Search

1. Use pagination for large results
2. Implement proper filtering
3. Cache frequent searches
4. Use full-text search for content
5. Provide autocomplete for better UX

### Performance

1. Use pagination on all lists
2. Implement caching where appropriate
3. Optimize database queries
4. Use CDN for static assets
5. Enable compression

### Error Handling

1. Log all errors
2. Display user-friendly messages
3. Don't expose sensitive information
4. Provide helpful error pages
5. Monitor error rates

---

## Changelog

### Version 1.0.0 (Current)

**Features**:
- Complete document management system
- User authentication and authorization
- Category and folder organization
- Advanced search functionality
- Workflow and approval system
- Audit logging
- Admin dashboard and reports

**API Endpoints**: All endpoints documented above

---

## Support

For API support or questions:

- **Documentation**: Check this document and related docs in `/docs`
- **Issues**: Contact system administrator
- **Email**: suporte@example.com

---

**Last Updated**: 2024
**API Version**: 1.0.0
