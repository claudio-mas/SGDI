# Search Functionality Documentation

## Overview

The Sistema GED search functionality provides comprehensive document search capabilities including:
- Simple text search
- Advanced search with multiple filters
- Full-text search in PDF content
- Autocomplete suggestions for tags and categories
- Quick filters for common searches

## Components

### SearchService (`app/services/search_service.py`)

The main service class that handles all search operations.

#### Key Methods

##### 1. Simple Search
```python
search_service = SearchService()
results, total_count = search_service.search(
    query="contract",
    user_id=current_user.id,
    page=1,
    per_page=20,
    include_shared=True
)
```

Searches in:
- Document names
- Document descriptions
- Tags

Features:
- Permission-based filtering (only returns documents user can access)
- Pagination support
- Includes both owned and shared documents

##### 2. Advanced Search
```python
results, total_count = search_service.advanced_search(
    user_id=current_user.id,
    nome="contract",
    categoria_id=5,
    tags=["legal", "2024"],
    data_inicio=datetime(2024, 1, 1),
    data_fim=datetime(2024, 12, 31),
    tipo_mime="application/pdf",
    page=1,
    per_page=20
)
```

Supported filters:
- `nome`: Document name
- `descricao`: Description
- `categoria_id`: Category ID
- `tags`: List of tag names (AND logic)
- `autor_id`: Document owner ID
- `tipo_mime`: MIME type
- `data_inicio`: Start date
- `data_fim`: End date
- `tamanho_min`: Minimum file size (bytes)
- `tamanho_max`: Maximum file size (bytes)
- `pasta_id`: Folder ID
- `extensao`: File extension

##### 3. Full-Text Search
```python
results, total_count = search_service.fulltext_search(
    query="confidential agreement",
    user_id=current_user.id,
    page=1,
    per_page=20
)
```

Searches within PDF document content using SQL Server Full-Text Search.

**Requirements:**
- SQL Server Full-Text Search feature must be installed
- Full-text catalog and index must be configured
- PDF text must be extracted and indexed

##### 4. Quick Filters
```python
results, total_count = search_service.get_quick_filter_results(
    user_id=current_user.id,
    filter_type='recent',  # or 'my_documents', 'favorites', 'pending_approval'
    page=1,
    per_page=20
)
```

Available filter types:
- `my_documents`: Documents owned by user
- `recent`: Documents uploaded in last 7 days
- `favorites`: Favorite documents (requires favorites table)
- `pending_approval`: Documents pending approval

##### 5. Autocomplete Suggestions
```python
# General suggestions
suggestions = search_service.get_suggestions(
    partial_query="cont",
    user_id=current_user.id,
    limit=10
)
# Returns: {'documents': [...], 'tags': [...], 'categories': [...]}

# Tag autocomplete
tags = search_service.get_tag_autocomplete(
    partial_tag="leg",
    limit=10
)
# Returns: ['legal', 'legislation', ...]

# Category autocomplete
categories = search_service.get_category_autocomplete(
    partial_category="cont",
    limit=10
)
# Returns: [{'id': 1, 'nome': 'Contracts', 'caminho': 'Legal > Contracts'}, ...]
```

## API Endpoints

### Search Routes (`app/search/routes.py`)

#### 1. Simple Search
```
GET /search?q=contract&page=1&per_page=20
```

#### 2. Advanced Search
```
GET /search/advanced?nome=contract&categoria_id=5&tags=legal,2024&data_inicio=2024-01-01
```

#### 3. Full-Text Search
```
GET /search/fulltext?q=confidential+agreement&page=1
```

#### 4. Quick Filters
```
GET /search/quick/recent?page=1
GET /search/quick/my_documents?page=1
GET /search/quick/pending_approval?page=1
```

#### 5. Autocomplete APIs (JSON)
```
GET /search/api/suggestions?q=cont&limit=10
GET /search/api/tags/autocomplete?q=leg&limit=10
GET /search/api/categories/autocomplete?q=cont&limit=10
```

## Full-Text Search Setup

### Prerequisites
1. SQL Server Full-Text Search feature must be installed
2. Database must support full-text indexing

### Setup Steps

#### 1. Run Migration
```bash
alembic upgrade head
```

This adds the `conteudo_texto` column to the `documentos` table.

#### 2. Create Full-Text Catalog and Index
```python
from app import create_app, db
from app.services.search_service import SearchService

app = create_app()
with app.app_context():
    SearchService.setup_fulltext_catalog()
```

Or manually via SQL:
```sql
-- Create catalog
CREATE FULLTEXT CATALOG ged_fulltext_catalog AS DEFAULT;

-- Create index
CREATE FULLTEXT INDEX ON documentos(
    nome LANGUAGE 1046,
    descricao LANGUAGE 1046,
    conteudo_texto LANGUAGE 1046
)
KEY INDEX PK__document__3213E83F
ON ged_fulltext_catalog
WITH CHANGE_TRACKING AUTO;
```

#### 3. Index Existing Documents
```python
from app.services.search_service import SearchService
from app.services.storage_service import StorageService
from app.repositories.document_repository import DocumentRepository

search_service = SearchService()
storage_service = StorageService()
doc_repo = DocumentRepository()

# Get all PDF documents
pdfs = doc_repo.filter_by(tipo_mime='application/pdf', status='ativo')

for doc in pdfs:
    file_path = storage_service.get_file(doc.caminho_arquivo)
    if file_path:
        search_service.index_document_content(doc, str(file_path))
```

## Performance Considerations

### Indexing
- Document names, descriptions, and hashes are indexed
- Full-text search uses SQL Server's native indexing
- Tag searches use indexed associations

### Pagination
- Always use pagination for large result sets
- Default: 20 results per page
- Maximum: 100 results per page

### Permission Filtering
- Permission checks are done at query level (not post-processing)
- Uses SQL joins for efficient filtering
- Expired permissions are automatically excluded

## Requirements Mapping

- **Requirement 4.1**: Simple search by name, description, and tags ✓
- **Requirement 4.2**: Advanced search with multiple filters ✓
- **Requirement 4.3**: Full-text search in PDF content ✓
- **Requirement 4.4**: Search results within 3 seconds (depends on indexing) ✓
- **Requirement 4.5**: Quick filters (My Documents, Recent, Favorites, Pending Approval) ✓
- **Requirement 3.5**: Tag autocomplete ✓

## Usage Examples

### Frontend Integration (JavaScript)

```javascript
// Autocomplete for search input
$('#search-input').autocomplete({
    source: function(request, response) {
        $.getJSON('/search/api/suggestions', {
            q: request.term,
            limit: 10
        }, function(data) {
            // Combine all suggestions
            let suggestions = [
                ...data.documents,
                ...data.tags.map(t => `tag:${t}`),
                ...data.categories.map(c => `category:${c}`)
            ];
            response(suggestions);
        });
    },
    minLength: 2
});

// Tag autocomplete for document form
$('#tags-input').autocomplete({
    source: '/search/api/tags/autocomplete',
    minLength: 1
});

// Category autocomplete
$('#category-input').autocomplete({
    source: function(request, response) {
        $.getJSON('/search/api/categories/autocomplete', {
            q: request.term
        }, function(data) {
            response(data.map(c => ({
                label: c.caminho,
                value: c.nome,
                id: c.id
            })));
        });
    },
    minLength: 1
});
```

## Troubleshooting

### Full-Text Search Not Working
1. Check if SQL Server Full-Text Search is installed:
   ```sql
   SELECT SERVERPROPERTY('IsFullTextInstalled');
   ```
2. Verify catalog exists:
   ```sql
   SELECT * FROM sys.fulltext_catalogs;
   ```
3. Check index status:
   ```sql
   SELECT * FROM sys.fulltext_indexes WHERE object_id = OBJECT_ID('documentos');
   ```

### Slow Search Performance
1. Ensure indexes exist on frequently queried columns
2. Use pagination to limit result sets
3. Consider adding more specific filters
4. Check SQL Server query execution plans

### Permission Issues
1. Verify user has proper permissions in database
2. Check that permission records are not expired
3. Ensure document status is 'ativo'

## Future Enhancements

- Search history tracking
- Saved searches
- Search result ranking/relevance scoring
- Fuzzy search for typo tolerance
- Search filters persistence
- Export search results
- Search analytics and reporting
