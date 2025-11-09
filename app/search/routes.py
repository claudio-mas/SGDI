"""
Search routes
"""
from flask import render_template, request, jsonify
from flask_login import login_required, current_user
from app.search import search_bp
from app.services.search_service import SearchService, SearchServiceError


@search_bp.route('/')
@login_required
def search():
    """
    Simple search page
    
    Query parameters:
        q: Search query
        page: Page number (default 1)
        per_page: Results per page (default 20)
    """
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Limit per_page to reasonable values
    per_page = min(max(per_page, 1), 100)
    
    search_service = SearchService()
    
    if query:
        try:
            results, total_count = search_service.search(
                query=query,
                user_id=current_user.id,
                page=page,
                per_page=per_page
            )
            
            # Calculate pagination info
            total_pages = (total_count + per_page - 1) // per_page
            
            return render_template(
                'search/results.html',
                query=query,
                results=results,
                total_count=total_count,
                page=page,
                per_page=per_page,
                total_pages=total_pages
            )
        except SearchServiceError as e:
            return render_template(
                'search/results.html',
                query=query,
                error=str(e),
                results=[],
                total_count=0
            )
    else:
        # Show search page with statistics
        stats = search_service.get_search_statistics(current_user.id)
        return render_template('search/search.html', stats=stats)


@search_bp.route('/advanced')
@login_required
def advanced_search():
    """
    Advanced search page with multiple filters
    
    Query parameters:
        nome: Document name
        descricao: Description
        categoria_id: Category ID
        tags: Comma-separated tag names
        autor_id: Author/owner ID
        tipo_mime: MIME type
        data_inicio: Start date (ISO format)
        data_fim: End date (ISO format)
        tamanho_min: Minimum file size
        tamanho_max: Maximum file size
        page: Page number
        per_page: Results per page
        sort_by: Sort order
    """
    from app.repositories.category_repository import CategoryRepository
    from app.repositories.user_repository import UserRepository
    
    # Get filter parameters
    nome = request.args.get('nome', '').strip()
    descricao = request.args.get('descricao', '').strip()
    categoria_id = request.args.get('categoria_id', type=int)
    tags_str = request.args.get('tags', '').strip()
    autor_id = request.args.get('autor_id', type=int)
    tipo_mime = request.args.get('tipo_mime', '').strip()
    data_inicio = request.args.get('data_inicio', '').strip()
    data_fim = request.args.get('data_fim', '').strip()
    tamanho_min = request.args.get('tamanho_min', type=int)
    tamanho_max = request.args.get('tamanho_max', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    sort_by = request.args.get('sort_by', 'data_upload_desc')
    
    # Parse tags
    tags = [t.strip() for t in tags_str.split(',') if t.strip()] if tags_str else None
    
    # Parse dates
    from datetime import datetime
    data_inicio_dt = None
    data_fim_dt = None
    
    if data_inicio:
        try:
            data_inicio_dt = datetime.fromisoformat(data_inicio)
        except ValueError:
            pass
    
    if data_fim:
        try:
            data_fim_dt = datetime.fromisoformat(data_fim)
        except ValueError:
            pass
    
    search_service = SearchService()
    
    # Check if any filters are applied
    has_filters = any([
        nome, descricao, categoria_id, tags, autor_id, tipo_mime,
        data_inicio_dt, data_fim_dt, tamanho_min, tamanho_max
    ])
    
    if has_filters:
        try:
            results, total_count = search_service.advanced_search(
                user_id=current_user.id,
                nome=nome or None,
                descricao=descricao or None,
                categoria_id=categoria_id,
                tags=tags,
                autor_id=autor_id,
                tipo_mime=tipo_mime or None,
                data_inicio=data_inicio_dt,
                data_fim=data_fim_dt,
                tamanho_min=tamanho_min,
                tamanho_max=tamanho_max,
                page=page,
                per_page=per_page
            )
            
            total_pages = (total_count + per_page - 1) // per_page
            
            # Get categories and users for form
            category_repo = CategoryRepository()
            user_repo = UserRepository()
            categories = category_repo.get_active_categories()
            users = user_repo.get_active_users()
            
            return render_template(
                'search/advanced_results.html',
                results=results,
                total_count=total_count,
                page=page,
                per_page=per_page,
                total_pages=total_pages,
                filters=request.args,
                categories=categories,
                users=users,
                sort_by=sort_by
            )
        except SearchServiceError as e:
            # Get categories and users for form
            category_repo = CategoryRepository()
            user_repo = UserRepository()
            categories = category_repo.get_active_categories()
            users = user_repo.get_active_users()
            
            return render_template(
                'search/advanced.html',
                error=str(e),
                categories=categories,
                users=users
            )
    else:
        # Show advanced search form
        # Get categories and users for form
        category_repo = CategoryRepository()
        user_repo = UserRepository()
        categories = category_repo.get_active_categories()
        users = user_repo.get_active_users()
        
        return render_template(
            'search/advanced.html',
            categories=categories,
            users=users
        )


@search_bp.route('/fulltext')
@login_required
def fulltext_search():
    """
    Full-text search in document content
    
    Query parameters:
        q: Search query
        page: Page number
        per_page: Results per page
    """
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    search_service = SearchService()
    
    if query:
        try:
            results, total_count = search_service.fulltext_search(
                query=query,
                user_id=current_user.id,
                page=page,
                per_page=per_page
            )
            
            total_pages = (total_count + per_page - 1) // per_page
            
            return render_template(
                'search/fulltext_results.html',
                query=query,
                results=results,
                total_count=total_count,
                page=page,
                per_page=per_page,
                total_pages=total_pages
            )
        except SearchServiceError as e:
            return render_template(
                'search/fulltext_results.html',
                query=query,
                error=str(e),
                results=[],
                total_count=0
            )
    else:
        return render_template('search/fulltext.html')


@search_bp.route('/quick/<filter_type>')
@login_required
def quick_filter(filter_type):
    """
    Quick filter results (my_documents, recent, favorites, pending_approval)
    
    Query parameters:
        page: Page number
        per_page: Results per page
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    search_service = SearchService()
    
    try:
        results, total_count = search_service.get_quick_filter_results(
            user_id=current_user.id,
            filter_type=filter_type,
            page=page,
            per_page=per_page
        )
        
        total_pages = (total_count + per_page - 1) // per_page
        
        return render_template(
            'search/quick_filter.html',
            filter_type=filter_type,
            results=results,
            total_count=total_count,
            page=page,
            per_page=per_page,
            total_pages=total_pages
        )
    except SearchServiceError as e:
        return render_template(
            'search/quick_filter.html',
            filter_type=filter_type,
            error=str(e),
            results=[],
            total_count=0
        )


@search_bp.route('/api/suggestions')
@login_required
def suggestions():
    """
    API endpoint for search suggestions (autocomplete)
    
    Query parameters:
        q: Partial query
        limit: Maximum number of suggestions (default 10)
    
    Returns:
        JSON with suggestions:
        {
            'documents': ['doc1', 'doc2', ...],
            'tags': ['tag1', 'tag2', ...],
            'categories': ['cat1', 'cat2', ...]
        }
    """
    partial_query = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)
    
    # Limit to reasonable values
    limit = min(max(limit, 1), 50)
    
    search_service = SearchService()
    
    try:
        suggestions = search_service.get_suggestions(
            partial_query=partial_query,
            user_id=current_user.id,
            limit=limit
        )
        return jsonify(suggestions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@search_bp.route('/api/tags/autocomplete')
@login_required
def tag_autocomplete():
    """
    API endpoint for tag autocomplete
    
    Query parameters:
        q: Partial tag name
        limit: Maximum number of suggestions (default 10)
    
    Returns:
        JSON array of tag names: ['tag1', 'tag2', ...]
    """
    partial_tag = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)
    
    limit = min(max(limit, 1), 50)
    
    search_service = SearchService()
    
    try:
        tags = search_service.get_tag_autocomplete(
            partial_tag=partial_tag,
            limit=limit
        )
        return jsonify(tags)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@search_bp.route('/api/categories/autocomplete')
@login_required
def category_autocomplete():
    """
    API endpoint for category autocomplete
    
    Query parameters:
        q: Partial category name
        limit: Maximum number of suggestions (default 10)
    
    Returns:
        JSON array of category objects:
        [
            {'id': 1, 'nome': 'Category', 'caminho': 'Parent > Category'},
            ...
        ]
    """
    partial_category = request.args.get('q', '').strip()
    limit = request.args.get('limit', 10, type=int)
    
    limit = min(max(limit, 1), 50)
    
    search_service = SearchService()
    
    try:
        categories = search_service.get_category_autocomplete(
            partial_category=partial_category,
            limit=limit
        )
        return jsonify(categories)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
