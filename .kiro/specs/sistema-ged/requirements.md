# Requirements Document - Sistema SGDI

## Introduction

Sistema de Gestão Eletrônica de Documentos (GED) é uma aplicação web corporativa desenvolvida com Flask, SQL Server e Bootstrap que permite digitalização, armazenamento centralizado, organização hierárquica e controle de acesso a documentos corporativos.

## Glossary

- **GED_System**: The Electronic Document Management System application
- **User**: Any authenticated person using the system
- **Document**: Any file uploaded and managed by the system
- **Category**: A classification group for organizing documents
- **Tag**: A keyword label attached to documents for search and organization
- **Permission**: Access control rule defining what actions a user can perform
- **Workflow**: An automated approval process for documents
- **Audit_Log**: System record of all operations performed
- **Repository**: Data access layer component
- **Service**: Business logic layer component

## Requirements

### Requirement 1: User Authentication and Authorization

**User Story:** As a user, I want to securely log in to the system, so that I can access my documents and perform authorized operations.

#### Acceptance Criteria

1. WHEN a user submits valid credentials, THE GED_System SHALL authenticate the user and create a session
2. WHEN a user enters incorrect credentials 5 times, THE GED_System SHALL block the account for 15 minutes
3. WHEN a user requests password reset, THE GED_System SHALL generate a secure token and send it via email
4. THE GED_System SHALL hash all passwords using bcrypt with cost factor 12
5. THE GED_System SHALL support five user profiles: Administrator, Manager, Standard User, Auditor, and Visitor

### Requirement 2: Document Upload and Storage

**User Story:** As a standard user, I want to upload documents to the system, so that I can store them centrally and access them from anywhere.

#### Acceptance Criteria

1. WHEN a user uploads a file, THE GED_System SHALL validate the file type against allowed formats (PDF, DOC, DOCX, XLS, XLSX, JPG, PNG, TIF)
2. WHEN a user uploads a file, THE GED_System SHALL reject files larger than 50MB
3. WHEN a file is uploaded, THE GED_System SHALL calculate a SHA256 hash and check for duplicates
4. WHEN a file is uploaded, THE GED_System SHALL generate a unique filename and store it securely
5. WHEN a file is uploaded, THE GED_System SHALL record metadata including name, description, category, tags, and upload timestamp
6. THE GED_System SHALL support uploading up to 10 files simultaneously

### Requirement 3: Document Organization

**User Story:** As a user, I want to organize documents using folders, categories, and tags, so that I can find them easily later.

#### Acceptance Criteria

1. THE GED_System SHALL allow users to create folder hierarchies up to 5 levels deep
2. THE GED_System SHALL provide predefined categories: Contracts, Invoices, HR, Legal, Technical, Administrative
3. WHEN a user assigns a category, THE GED_System SHALL allow hierarchical subcategories
4. THE GED_System SHALL allow users to add multiple tags to each document
5. THE GED_System SHALL provide tag autocomplete based on existing tags

### Requirement 4: Document Search and Retrieval

**User Story:** As a user, I want to search for documents using various criteria, so that I can quickly find what I need.

#### Acceptance Criteria

1. WHEN a user enters a search term, THE GED_System SHALL search document names, descriptions, and tags
2. THE GED_System SHALL provide advanced search with filters for date range, category, author, file type, and size
3. WHEN a user searches PDF content, THE GED_System SHALL use full-text search indexing
4. THE GED_System SHALL return search results within 3 seconds
5. THE GED_System SHALL provide quick filters for "My Documents", "Recent", "Favorites", and "Pending Approval"

### Requirement 5: Access Control and Permissions

**User Story:** As a document owner, I want to control who can access my documents, so that sensitive information remains secure.

#### Acceptance Criteria

1. WHEN a document is created, THE GED_System SHALL assign the creator as owner with full permissions
2. THE GED_System SHALL allow owners to grant permissions (view, edit, delete, share) to other users
3. WHEN a user attempts an operation, THE GED_System SHALL validate permissions before allowing the action
4. THE GED_System SHALL enforce role-based access control (RBAC) based on user profiles
5. WHEN a user lacks permission, THE GED_System SHALL display an appropriate error message

### Requirement 6: Document Versioning

**User Story:** As a user, I want to maintain version history of documents, so that I can track changes and restore previous versions if needed.

#### Acceptance Criteria

1. WHEN a user uploads a new version, THE GED_System SHALL increment the version number
2. THE GED_System SHALL store up to 10 versions per document
3. WHEN a new version is created, THE GED_System SHALL require a comment describing the changes
4. THE GED_System SHALL allow users to view version history with timestamps and authors
5. THE GED_System SHALL allow users to restore a previous version

### Requirement 7: Document Workflow and Approvals

**User Story:** As a manager, I want to create approval workflows for documents, so that important documents go through proper review before publication.

#### Acceptance Criteria

1. WHEN an administrator creates a workflow, THE GED_System SHALL allow defining multiple approval stages
2. WHEN a user submits a document for approval, THE GED_System SHALL send email notifications to approvers
3. WHEN an approver reviews a document, THE GED_System SHALL allow approval or rejection with mandatory comments
4. THE GED_System SHALL record all workflow steps including date, time, approver, decision, and comments
5. WHEN a document is rejected, THE GED_System SHALL notify the submitter with rejection reasons

### Requirement 8: Audit Logging

**User Story:** As an auditor, I want to view complete logs of all system operations, so that I can ensure compliance and investigate issues.

#### Acceptance Criteria

1. THE GED_System SHALL log all operations including login, upload, download, edit, delete, and access
2. WHEN an operation occurs, THE GED_System SHALL record user ID, timestamp, IP address, action, and affected document
3. THE GED_System SHALL retain audit logs for at least 1 year
4. THE GED_System SHALL allow auditors to filter logs by date, user, document, and operation type
5. THE GED_System SHALL protect audit logs from modification or deletion

### Requirement 9: Document Deletion and Recovery

**User Story:** As a user, I want deleted documents to be recoverable for 30 days, so that I can restore accidentally deleted files.

#### Acceptance Criteria

1. WHEN a user deletes a document, THE GED_System SHALL perform soft deletion by marking status as "deleted"
2. THE GED_System SHALL move deleted documents to a trash folder accessible to the owner
3. WHEN 30 days pass after deletion, THE GED_System SHALL permanently delete the document and its file
4. THE GED_System SHALL allow users to restore documents from trash within the 30-day period
5. THE GED_System SHALL allow administrators to permanently delete documents immediately if needed

### Requirement 10: System Administration

**User Story:** As an administrator, I want to manage users, configure system settings, and monitor storage, so that the system runs smoothly.

#### Acceptance Criteria

1. THE GED_System SHALL allow administrators to create, edit, activate, and deactivate user accounts
2. THE GED_System SHALL allow administrators to assign and change user profiles
3. THE GED_System SHALL provide a dashboard showing total documents, storage used, and recent activity
4. WHEN storage reaches 80% capacity, THE GED_System SHALL send alerts to administrators
5. THE GED_System SHALL allow administrators to configure system parameters including max file size and allowed formats

### Requirement 11: Responsive User Interface

**User Story:** As a user, I want to access the system from any device, so that I can work from desktop, tablet, or mobile.

#### Acceptance Criteria

1. THE GED_System SHALL provide a responsive interface that adapts to screen sizes from 320px to 1920px
2. THE GED_System SHALL use Bootstrap Grid System for layout responsiveness
3. THE GED_System SHALL provide touch-friendly controls on mobile devices
4. THE GED_System SHALL maintain usability on Chrome 90+, Firefox 88+, Edge 90+, and Safari 14+
5. THE GED_System SHALL load pages within 2 seconds on standard broadband connections

### Requirement 12: Document Sharing

**User Story:** As a user, I want to share documents with colleagues, so that we can collaborate effectively.

#### Acceptance Criteria

1. THE GED_System SHALL allow users to share documents with other internal users
2. WHEN sharing a document, THE GED_System SHALL allow specifying permissions (view or edit)
3. THE GED_System SHALL allow setting expiration dates for shared access
4. THE GED_System SHALL send email notifications when documents are shared
5. THE GED_System SHALL allow users to revoke shared access at any time

### Requirement 13: Performance and Scalability

**User Story:** As a system stakeholder, I want the system to perform well under load, so that users have a smooth experience.

#### Acceptance Criteria

1. THE GED_System SHALL support up to 1000 concurrent users
2. THE GED_System SHALL process up to 100 simultaneous file uploads
3. THE GED_System SHALL handle up to 1000 search queries per minute
4. THE GED_System SHALL store up to 500,000 documents
5. THE GED_System SHALL provide minimum 2TB storage capacity

### Requirement 14: Security and Data Protection

**User Story:** As a security officer, I want the system to protect data and prevent attacks, so that corporate information remains secure.

#### Acceptance Criteria

1. THE GED_System SHALL enforce HTTPS for all communications in production
2. THE GED_System SHALL protect against SQL injection using prepared statements
3. THE GED_System SHALL protect against XSS attacks by sanitizing all user inputs
4. THE GED_System SHALL protect against CSRF attacks using secure tokens
5. THE GED_System SHALL implement rate limiting of 100 requests per minute per IP address
6. THE GED_System SHALL optionally encrypt sensitive documents using AES-256

### Requirement 15: Backup and Recovery

**User Story:** As an administrator, I want automated backups, so that data can be recovered in case of failure.

#### Acceptance Criteria

1. THE GED_System SHALL perform automatic daily database backups
2. THE GED_System SHALL perform weekly full file backups
3. THE GED_System SHALL retain backups for 90 days
4. THE GED_System SHALL allow administrators to trigger manual backups
5. THE GED_System SHALL provide backup restoration functionality
