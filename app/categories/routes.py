"""
Category management routes
"""
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.categories import category_bp
from app.categories.forms import CategoryForm, FolderForm
from app.services.category_service import CategoryService, FolderService
from app.repositories.category_repository import CategoryRepository, FolderRepository


# Initialize services
category_service = CategoryService()
folder_service = FolderService()
category_repo = CategoryRepository()
folder_repo = FolderRepository()


# ============================================================================
# CATEGORY ROUTES
# ============================================================================

@category_bp.route('/')
@login_required
def list_categories():
    """List all categories with hierarchy"""
    try:
        categories = category_service.get_all_categories()
        hierarchy = category_service.get_category_hierarchy()
        
        # Get document counts for each category
        category_stats = {}
        for cat in categories:
            category_stats[cat.id] = category_repo.get_document_count(cat.id, include_subcategories=True)
        
        return render_template(
            'categories/list.html',
            categories=categories,
            hierarchy=hierarchy,
            category_stats=category_stats
        )
    except Exception as e:
        flash(f'Erro ao carregar categorias: {str(e)}', 'danger')
        return redirect(url_for('documents.list_documents'))


@category_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_category():
    """Create new category"""
    # Check if user has admin permissions
    if not current_user.perfil or current_user.perfil.nome not in ['Administrador', 'Gerente']:
        flash('Você não tem permissão para criar categorias', 'danger')
        return redirect(url_for('categories.list_categories'))
    
    form = CategoryForm()
    
    if form.validate_on_submit():
        try:
            data = {
                'nome': form.nome.data,
                'descricao': form.descricao.data,
                'categoria_pai_id': form.categoria_pai_id.data if form.categoria_pai_id.data else None,
                'icone': form.icone.data,
                'cor': form.cor.data,
                'ordem': form.ordem.data or 0
            }
            
            categoria = category_service.create_category(data, current_user.id)
            flash(f'Categoria "{categoria.nome}" criada com sucesso!', 'success')
            return redirect(url_for('categories.list_categories'))
        except Exception as e:
            flash(f'Erro ao criar categoria: {str(e)}', 'danger')
    
    return render_template('categories/form.html', form=form, title='Nova Categoria')


@category_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    """Edit category"""
    # Check if user has admin permissions
    if not current_user.perfil or current_user.perfil.nome not in ['Administrador', 'Gerente']:
        flash('Você não tem permissão para editar categorias', 'danger')
        return redirect(url_for('categories.list_categories'))
    
    categoria = category_service.get_category_by_id(id)
    if not categoria:
        flash('Categoria não encontrada', 'danger')
        return redirect(url_for('categories.list_categories'))
    
    form = CategoryForm(categoria_id=id)
    
    if form.validate_on_submit():
        try:
            data = {
                'nome': form.nome.data,
                'descricao': form.descricao.data,
                'categoria_pai_id': form.categoria_pai_id.data if form.categoria_pai_id.data else None,
                'icone': form.icone.data,
                'cor': form.cor.data,
                'ordem': form.ordem.data or 0
            }
            
            categoria = category_service.update_category(id, data, current_user.id)
            flash(f'Categoria "{categoria.nome}" atualizada com sucesso!', 'success')
            return redirect(url_for('categories.list_categories'))
        except Exception as e:
            flash(f'Erro ao atualizar categoria: {str(e)}', 'danger')
    
    # Populate form with current category data on GET
    if not form.is_submitted():
        form.nome.data = categoria.nome
        form.descricao.data = categoria.descricao
        form.categoria_pai_id.data = categoria.categoria_pai_id
        form.icone.data = categoria.icone
        form.cor.data = categoria.cor or '#007bff'
        form.ordem.data = categoria.ordem
    
    return render_template('categories/form.html', form=form, title='Editar Categoria', categoria=categoria)


@category_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_category(id):
    """Delete category"""
    # Check if user has admin permissions
    if not current_user.perfil or current_user.perfil.nome not in ['Administrador', 'Gerente']:
        flash('Você não tem permissão para excluir categorias', 'danger')
        return redirect(url_for('categories.list_categories'))
    
    try:
        categoria = category_service.get_category_by_id(id)
        if not categoria:
            flash('Categoria não encontrada', 'danger')
            return redirect(url_for('categories.list_categories'))
        
        nome = categoria.nome
        category_service.delete_category(id, current_user.id)
        flash(f'Categoria "{nome}" excluída com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir categoria: {str(e)}', 'danger')
    
    return redirect(url_for('categories.list_categories'))


@category_bp.route('/<int:id>')
@login_required
def view_category(id):
    """View category details"""
    try:
        stats = category_service.get_category_stats(id)
        breadcrumb = category_repo.get_path_to_root(id)
        
        return render_template(
            'categories/view.html',
            categoria=stats['categoria'],
            document_count=stats['document_count'],
            document_count_total=stats['document_count_total'],
            subcategories=stats['subcategories'],
            breadcrumb=breadcrumb
        )
    except Exception as e:
        flash(f'Erro ao carregar categoria: {str(e)}', 'danger')
        return redirect(url_for('categories.list_categories'))


# ============================================================================
# FOLDER ROUTES
# ============================================================================

@category_bp.route('/folders')
@login_required
def list_folders():
    """List user's folders with hierarchy"""
    try:
        folders = folder_service.get_user_folders(current_user.id)
        hierarchy = folder_service.get_folder_hierarchy(current_user.id)
        
        # Get document counts for each folder
        folder_stats = {}
        for folder in folders:
            folder_stats[folder.id] = folder_repo.get_document_count(folder.id)
        
        return render_template(
            'categories/folders.html',
            folders=folders,
            hierarchy=hierarchy,
            folder_stats=folder_stats
        )
    except Exception as e:
        flash(f'Erro ao carregar pastas: {str(e)}', 'danger')
        return redirect(url_for('documents.list_documents'))


@category_bp.route('/folders/new', methods=['GET', 'POST'])
@login_required
def create_folder():
    """Create new folder"""
    form = FolderForm(usuario_id=current_user.id)
    
    if form.validate_on_submit():
        try:
            data = {
                'nome': form.nome.data,
                'descricao': form.descricao.data,
                'pasta_pai_id': form.pasta_pai_id.data if form.pasta_pai_id.data else None,
                'cor': form.cor.data,
                'ordem': form.ordem.data or 0
            }
            
            pasta = folder_service.create_folder(data, current_user.id)
            flash(f'Pasta "{pasta.nome}" criada com sucesso!', 'success')
            return redirect(url_for('categories.list_folders'))
        except Exception as e:
            flash(f'Erro ao criar pasta: {str(e)}', 'danger')
    
    return render_template('categories/folder_form.html', form=form, title='Nova Pasta')


@category_bp.route('/folders/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_folder(id):
    """Edit folder"""
    pasta = folder_service.get_folder_by_id(id)
    if not pasta:
        flash('Pasta não encontrada', 'danger')
        return redirect(url_for('categories.list_folders'))
    
    # Verify ownership
    if pasta.usuario_id != current_user.id:
        flash('Você não tem permissão para editar esta pasta', 'danger')
        return redirect(url_for('categories.list_folders'))
    
    form = FolderForm(usuario_id=current_user.id, pasta_id=id, obj=pasta)
    
    if form.validate_on_submit():
        try:
            data = {
                'nome': form.nome.data,
                'descricao': form.descricao.data,
                'pasta_pai_id': form.pasta_pai_id.data if form.pasta_pai_id.data else None,
                'cor': form.cor.data,
                'ordem': form.ordem.data or 0
            }
            
            pasta = folder_service.update_folder(id, data, current_user.id)
            flash(f'Pasta "{pasta.nome}" atualizada com sucesso!', 'success')
            return redirect(url_for('categories.list_folders'))
        except Exception as e:
            flash(f'Erro ao atualizar pasta: {str(e)}', 'danger')
    
    return render_template('categories/folder_form.html', form=form, title='Editar Pasta', pasta=pasta)


@category_bp.route('/folders/<int:id>/delete', methods=['POST'])
@login_required
def delete_folder(id):
    """Delete folder"""
    try:
        pasta = folder_service.get_folder_by_id(id)
        if not pasta:
            flash('Pasta não encontrada', 'danger')
            return redirect(url_for('categories.list_folders'))
        
        # Verify ownership
        if pasta.usuario_id != current_user.id:
            flash('Você não tem permissão para excluir esta pasta', 'danger')
            return redirect(url_for('categories.list_folders'))
        
        nome = pasta.nome
        folder_service.delete_folder(id, current_user.id)
        flash(f'Pasta "{nome}" excluída com sucesso!', 'success')
    except Exception as e:
        flash(f'Erro ao excluir pasta: {str(e)}', 'danger')
    
    return redirect(url_for('categories.list_folders'))


@category_bp.route('/folders/<int:id>')
@login_required
def view_folder(id):
    """View folder details"""
    try:
        pasta = folder_service.get_folder_by_id(id)
        if not pasta:
            flash('Pasta não encontrada', 'danger')
            return redirect(url_for('categories.list_folders'))
        
        # Verify ownership
        if pasta.usuario_id != current_user.id:
            flash('Você não tem permissão para visualizar esta pasta', 'danger')
            return redirect(url_for('categories.list_folders'))
        
        stats = folder_service.get_folder_stats(id)
        breadcrumb = folder_service.get_folder_breadcrumb(id)
        
        return render_template(
            'categories/folder_view.html',
            pasta=stats['pasta'],
            document_count=stats['document_count'],
            subfolders=stats['subfolders'],
            breadcrumb=breadcrumb
        )
    except Exception as e:
        flash(f'Erro ao carregar pasta: {str(e)}', 'danger')
        return redirect(url_for('categories.list_folders'))


# ============================================================================
# API ENDPOINTS
# ============================================================================

@category_bp.route('/api/categories/hierarchy')
@login_required
def api_category_hierarchy():
    """API endpoint for category hierarchy (for tree views)"""
    try:
        hierarchy = category_service.get_category_hierarchy()
        return jsonify({'success': True, 'data': hierarchy})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@category_bp.route('/api/folders/hierarchy')
@login_required
def api_folder_hierarchy():
    """API endpoint for folder hierarchy (for tree views)"""
    try:
        hierarchy = folder_service.get_folder_hierarchy(current_user.id)
        return jsonify({'success': True, 'data': hierarchy})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
