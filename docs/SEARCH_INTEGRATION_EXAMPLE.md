# Search Service Integration Example

## Integrating Search with Document Upload

When a document is uploaded, you can automatically index its content for full-text search:

```python
from app.services.document_service import DocumentService
from app.services.search_service import SearchService
from app.services.storage_service import StorageService
from app.utils.file_handler import FileHandler

# Initialize services
storage_service = StorageService()
file_handler = FileHandler()
document_service = DocumentService(storage_service, file_handler)
search_service = SearchService()

# Upload document
documento = document_service.upload_document(
    file=uploaded_file,
    user_id=current_user.id,
    nome="Contract 2024",
    descricao="Annual service contract",
    categoria_id=5,
    tags=["contract", "2024", "legal"]
)

# Index PDF content for full-text search
if documento.tipo_mime == 'application/pdf':
    file_path = storage_service.get_file(documento.caminho_arquivo)
    if file_path:
        search_service.index_document_content(documento, str(file_path))
        print(f"Document {documento.id} indexed for full-text search")
```

## Complete Search Workflow Example

```python
from flask import request, render_template
from flask_login import current_user, login_required
from app.services.search_service import SearchService

@app.route('/documents/search')
@login_required
def search_documents():
    """Complete search workflow with all features"""
    
    search_service = SearchService()
    
    # Get search parameters
    query = request.args.get('q', '').strip()
    search_type = request.args.get('type', 'simple')  # simple, advanced, fulltext
    page = request.args.get('page', 1, type=int)
    
    if search_type == 'simple':
        # Simple search
        results, total = search_service.search(
            query=query,
            user_id=current_user.id,
            page=page,
            per_page=20
        )
        
    elif search_type == 'advanced':
        # Advanced search with filters
        results, total = search_service.advanced_search(
            user_id=current_user.id,
            nome=request.args.get('nome'),
            categoria_id=request.args.get('categoria_id', type=int),
            tags=request.args.getlist('tags'),
            data_inicio=request.args.get('data_inicio'),
            data_fim=request.args.get('data_fim'),
            page=page,
            per_page=20
        )
        
    elif search_type == 'fulltext':
        # Full-text search in PDF content
        results, total = search_service.fulltext_search(
            query=query,
            user_id=current_user.id,
            page=page,
            per_page=20
        )
    
    # Get search statistics
    stats = search_service.get_search_statistics(current_user.id)
    
    return render_template(
        'search/results.html',
        results=results,
        total=total,
        page=page,
        stats=stats,
        query=query,
        search_type=search_type
    )
```

## Autocomplete Integration (JavaScript)

### Basic Autocomplete Setup

```html
<!-- Include jQuery and jQuery UI -->
<script src="https://code.jquery.com/jquery-3.7.0.min.js"></script>
<script src="https://code.jquery.com/ui/1.13.2/jquery-ui.min.js"></script>
<link rel="stylesheet" href="https://code.jquery.com/ui/1.13.2/themes/base/jquery-ui.css">

<!-- Search input with autocomplete -->
<input type="text" id="search-input" class="form-control" placeholder="Search documents...">

<script>
$(document).ready(function() {
    $('#search-input').autocomplete({
        source: function(request, response) {
            $.getJSON('/search/api/suggestions', {
                q: request.term,
                limit: 10
            }, function(data) {
                // Combine all suggestions with prefixes
                let suggestions = [];
                
                // Add document suggestions
                data.documents.forEach(doc => {
                    suggestions.push({
                        label: '📄 ' + doc,
                        value: doc,
                        category: 'document'
                    });
                });
                
                // Add tag suggestions
                data.tags.forEach(tag => {
                    suggestions.push({
                        label: '🏷️ ' + tag,
                        value: 'tag:' + tag,
                        category: 'tag'
                    });
                });
                
                // Add category suggestions
                data.categories.forEach(cat => {
                    suggestions.push({
                        label: '📁 ' + cat,
                        value: 'category:' + cat,
                        category: 'category'
                    });
                });
                
                response(suggestions);
            });
        },
        minLength: 2,
        select: function(event, ui) {
            // Handle selection based on category
            if (ui.item.category === 'tag') {
                // Search by tag
                window.location.href = '/search?tags=' + encodeURIComponent(ui.item.value.replace('tag:', ''));
            } else if (ui.item.category === 'category') {
                // Search by category
                window.location.href = '/search?category=' + encodeURIComponent(ui.item.value.replace('category:', ''));
            } else {
                // Regular search
                window.location.href = '/search?q=' + encodeURIComponent(ui.item.value);
            }
            return false;
        }
    });
});
</script>
```

### Tag Input with Autocomplete (Select2)

```html
<!-- Include Select2 -->
<link href="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/css/select2.min.css" rel="stylesheet" />
<script src="https://cdn.jsdelivr.net/npm/select2@4.1.0-rc.0/dist/js/select2.min.js"></script>

<!-- Tags input -->
<select id="tags-input" class="form-control" multiple="multiple">
    <!-- Options will be loaded dynamically -->
</select>

<script>
$(document).ready(function() {
    $('#tags-input').select2({
        tags: true,
        tokenSeparators: [','],
        ajax: {
            url: '/search/api/tags/autocomplete',
            dataType: 'json',
            delay: 250,
            data: function(params) {
                return {
                    q: params.term,
                    limit: 20
                };
            },
            processResults: function(data) {
                return {
                    results: data.map(tag => ({
                        id: tag,
                        text: tag
                    }))
                };
            },
            cache: true
        },
        minimumInputLength: 1,
        placeholder: 'Add tags...'
    });
});
</script>
```

### Category Autocomplete

```html
<!-- Category input -->
<input type="text" id="category-input" class="form-control" placeholder="Select category...">
<input type="hidden" id="category-id" name="categoria_id">

<script>
$(document).ready(function() {
    $('#category-input').autocomplete({
        source: function(request, response) {
            $.getJSON('/search/api/categories/autocomplete', {
                q: request.term,
                limit: 15
            }, function(data) {
                response(data.map(cat => ({
                    label: cat.caminho,  // Show full path
                    value: cat.nome,     // Display name only
                    id: cat.id           // Store ID
                })));
            });
        },
        minLength: 1,
        select: function(event, ui) {
            // Store the category ID in hidden field
            $('#category-id').val(ui.item.id);
            return true;
        }
    });
});
</script>
```

## Advanced Search Form Example

```html
<form action="/search/advanced" method="get" class="search-form">
    <div class="row">
        <div class="col-md-6">
            <div class="form-group">
                <label>Document Name</label>
                <input type="text" name="nome" class="form-control" placeholder="Enter document name...">
            </div>
        </div>
        
        <div class="col-md-6">
            <div class="form-group">
                <label>Category</label>
                <input type="text" id="category-input" class="form-control" placeholder="Select category...">
                <input type="hidden" name="categoria_id" id="category-id">
            </div>
        </div>
    </div>
    
    <div class="row">
        <div class="col-md-6">
            <div class="form-group">
                <label>Tags</label>
                <select name="tags" id="tags-input" class="form-control" multiple></select>
            </div>
        </div>
        
        <div class="col-md-6">
            <div class="form-group">
                <label>File Type</label>
                <select name="tipo_mime" class="form-control">
                    <option value="">All types</option>
                    <option value="application/pdf">PDF</option>
                    <option value="application/msword">Word</option>
                    <option value="application/vnd.ms-excel">Excel</option>
                    <option value="image/jpeg">JPEG Image</option>
                    <option value="image/png">PNG Image</option>
                </select>
            </div>
        </div>
    </div>
    
    <div class="row">
        <div class="col-md-6">
            <div class="form-group">
                <label>Upload Date From</label>
                <input type="date" name="data_inicio" class="form-control">
            </div>
        </div>
        
        <div class="col-md-6">
            <div class="form-group">
                <label>Upload Date To</label>
                <input type="date" name="data_fim" class="form-control">
            </div>
        </div>
    </div>
    
    <div class="row">
        <div class="col-md-6">
            <div class="form-group">
                <label>Min File Size (MB)</label>
                <input type="number" name="tamanho_min" class="form-control" step="0.1">
            </div>
        </div>
        
        <div class="col-md-6">
            <div class="form-group">
                <label>Max File Size (MB)</label>
                <input type="number" name="tamanho_max" class="form-control" step="0.1">
            </div>
        </div>
    </div>
    
    <button type="submit" class="btn btn-primary">
        <i class="fas fa-search"></i> Search
    </button>
    <button type="reset" class="btn btn-secondary">
        <i class="fas fa-times"></i> Clear
    </button>
</form>

<script>
// Convert MB to bytes before submitting
$('.search-form').on('submit', function() {
    let minMB = $('input[name="tamanho_min"]').val();
    let maxMB = $('input[name="tamanho_max"]').val();
    
    if (minMB) {
        $('input[name="tamanho_min"]').val(minMB * 1024 * 1024);
    }
    if (maxMB) {
        $('input[name="tamanho_max"]').val(maxMB * 1024 * 1024);
    }
});
</script>
```

## Quick Filters Implementation

```html
<div class="quick-filters">
    <a href="/search/quick/my_documents" class="btn btn-outline-primary">
        <i class="fas fa-user"></i> My Documents
    </a>
    <a href="/search/quick/recent" class="btn btn-outline-primary">
        <i class="fas fa-clock"></i> Recent
    </a>
    <a href="/search/quick/favorites" class="btn btn-outline-primary">
        <i class="fas fa-star"></i> Favorites
    </a>
    <a href="/search/quick/pending_approval" class="btn btn-outline-warning">
        <i class="fas fa-hourglass-half"></i> Pending Approval
    </a>
</div>
```

## Search Results Display

```html
<div class="search-results">
    <div class="results-header">
        <h3>Search Results</h3>
        <p>Found {{ total_count }} documents</p>
    </div>
    
    {% for doc in results %}
    <div class="result-item">
        <div class="result-icon">
            {% if doc.tipo_mime == 'application/pdf' %}
                <i class="fas fa-file-pdf text-danger"></i>
            {% elif doc.tipo_mime.startswith('image/') %}
                <i class="fas fa-file-image text-primary"></i>
            {% else %}
                <i class="fas fa-file text-secondary"></i>
            {% endif %}
        </div>
        
        <div class="result-content">
            <h5>
                <a href="/documents/{{ doc.id }}">{{ doc.nome }}</a>
            </h5>
            <p class="text-muted">{{ doc.descricao }}</p>
            
            <div class="result-meta">
                <span class="badge bg-secondary">{{ doc.categoria.nome if doc.categoria else 'Uncategorized' }}</span>
                {% for tag in doc.tags %}
                    <span class="badge bg-info">{{ tag.nome }}</span>
                {% endfor %}
                <span class="text-muted">
                    <i class="fas fa-user"></i> {{ doc.usuario.nome }}
                </span>
                <span class="text-muted">
                    <i class="fas fa-calendar"></i> {{ doc.data_upload.strftime('%d/%m/%Y') }}
                </span>
                <span class="text-muted">
                    <i class="fas fa-hdd"></i> {{ doc.tamanho_formatado }}
                </span>
            </div>
        </div>
        
        <div class="result-actions">
            <a href="/documents/{{ doc.id }}/download" class="btn btn-sm btn-primary">
                <i class="fas fa-download"></i> Download
            </a>
        </div>
    </div>
    {% endfor %}
    
    <!-- Pagination -->
    {% if total_pages > 1 %}
    <nav aria-label="Search results pagination">
        <ul class="pagination">
            {% if page > 1 %}
            <li class="page-item">
                <a class="page-link" href="?q={{ query }}&page={{ page - 1 }}">Previous</a>
            </li>
            {% endif %}
            
            {% for p in range(1, total_pages + 1) %}
                {% if p == page %}
                <li class="page-item active">
                    <span class="page-link">{{ p }}</span>
                </li>
                {% else %}
                <li class="page-item">
                    <a class="page-link" href="?q={{ query }}&page={{ p }}">{{ p }}</a>
                </li>
                {% endif %}
            {% endfor %}
            
            {% if page < total_pages %}
            <li class="page-item">
                <a class="page-link" href="?q={{ query }}&page={{ page + 1 }}">Next</a>
            </li>
            {% endif %}
        </ul>
    </nav>
    {% endif %}
</div>
```

## Performance Tips

1. **Use Pagination**: Always paginate results to avoid loading too many documents
2. **Cache Popular Searches**: Consider caching frequently used search queries
3. **Index Optimization**: Ensure database indexes are properly configured
4. **Lazy Loading**: Load document details only when needed
5. **Debounce Autocomplete**: Add delay to autocomplete requests to reduce server load

```javascript
// Debounced autocomplete
let searchTimeout;
$('#search-input').on('input', function() {
    clearTimeout(searchTimeout);
    searchTimeout = setTimeout(function() {
        // Trigger autocomplete
        $('#search-input').autocomplete('search');
    }, 300); // 300ms delay
});
```
