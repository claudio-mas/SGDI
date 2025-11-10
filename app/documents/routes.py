"""
Document management routes
"""
from flask import render_template, request, redirect, url_for, flash, send_file, jsonify, abort
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.documents import document_bp
from app.documents.forms import DocumentUploadForm, DocumentEditForm, DocumentVersionForm, DocumentSearchForm
from app.services.document_service import DocumentService, DocumentServiceError, PermissionDeniedError, DocumentNotFoundError
from app.services.storage_service import StorageService
from app.utils.file_handler import FileHandler
from app.repositories.document_repository import DocumentRepository
from app.repositories.category_repository import CategoryRepository
from app.models.document import Categoria, Pasta
from app import db
import os


# Services are initialized lazily to avoid issues during import
# They will be properly configured when routes are called
storage_service = None
file_handler = None
document_service = None
document_repository = DocumentRepository()

def _init_services():
    """Initialize services with app context"""
    global storage_service, file_handler, document_service
    from flask import current_app
    if storage_service is None:
        storage_service = StorageService(current_app.config['UPLOAD_FOLDER'])
        file_handler = FileHandler(
            current_app.config['ALLOWED_EXTENSIONS'],
            current_app.config['MAX_CONTENT_LENGTH']
        )
        document_service = DocumentService(storage_service, file_handler)


@document_bp.route('/')
@login_required
def list_documents():
    """List documents with filtering and pagination"""
    _init_services()
    from app.models.document import Documento
    from app.models.permission import Permissao
    from datetime import datetime, timedelta
    from sqlalchemy import or_, and_
    
    # Get query parameters
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    view_mode = request.args.get('view', 'table')  # table or grid
    filter_type = request.args.get('filter', 'all')  # all, my, recent, favorites
    categoria_id = request.args.get('categoria_id', type=int)
    search_query = request.args.get('q', '')
    
    # Build query based on filter type
    if filter_type == 'my':
        # My documents only (owned by user)
        documentos_query = Documento.query.filter(
            Documento.usuario_id == current_user.id,
            Documento.status == 'ativo'
        )
    elif filter_type == 'recent':
        # Recent documents (last 7 days) accessible by user
        cutoff_date = datetime.utcnow() - timedelta(days=7)
        documentos_query = Documento.query.outerjoin(Permissao).filter(
            or_(
                Documento.usuario_id == current_user.id,
                Permissao.usuario_id == current_user.id
            ),
            Documento.status == 'ativo',
            Documento.data_upload >= cutoff_date
        ).distinct()
    elif filter_type == 'trash':
        # Trash (deleted documents owned by user)
        documentos_query = Documento.query.filter(
            Documento.usuario_id == current_user.id,
            Documento.status == 'excluido'
        )
    else:
        # All accessible documents (owned or shared)
        documentos_query = Documento.query.outerjoin(Permissao).filter(
            or_(
                Documento.usuario_id == current_user.id,
                Permissao.usuario_id == current_user.id
            ),
            Documento.status == 'ativo'
        ).distinct()
    
    # Apply category filter
    if categoria_id:
        documentos_query = documentos_query.filter(Documento.categoria_id == categoria_id)
    
    # Apply search query
    if search_query:
        search_pattern = f'%{search_query}%'
        documentos_query = documentos_query.filter(
            or_(
                Documento.nome.ilike(search_pattern),
                Documento.descricao.ilike(search_pattern)
            )
        )
    
    # Order by upload date descending
    documentos_query = documentos_query.order_by(Documento.data_upload.desc())
    
    # Paginate results
    pagination = documentos_query.paginate(page=page, per_page=per_page, error_out=False)
    documentos = pagination.items
    
    # Get categories for filter dropdown
    categorias = Categoria.query.filter_by(ativo=True).order_by(Categoria.nome).all()
    
    return render_template(
        'documents/list.html',
        documentos=documentos,
        pagination=pagination,
        view_mode=view_mode,
        filter_type=filter_type,
        categorias=categorias,
        search_query=search_query,
        selected_categoria=categoria_id
    )


@document_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    """Upload document"""
    _init_services()
    from app.utils.file_handler import FileValidationError
    
    form = DocumentUploadForm()
    
    # Populate category choices
    categorias = Categoria.query.filter_by(ativo=True).order_by(Categoria.nome).all()
    form.categoria_id.choices = [(0, 'Selecione uma categoria')] + [(c.id, c.nome) for c in categorias]
    
    # Populate folder choices for current user
    pastas = Pasta.query.filter_by(usuario_id=current_user.id).order_by(Pasta.nome).all()
    form.pasta_id.choices = [(0, 'Nenhuma pasta')] + [(p.id, p.nome) for p in pastas]
    
    # Allow processing when form validates OR when a file is present in the request
    if form.validate_on_submit() or (request.method == 'POST' and (request.files.getlist('files') or request.files.get('file'))):
        try:
            # Get uploaded files (support both 'files' and legacy 'file' field used in tests)
            files = request.files.getlist('files')
            if not files or (len(files) == 0 or files[0].filename == ''):
                single = request.files.get('file')
                if single and single.filename:
                    files = [single]
            
            if not files or files[0].filename == '':
                flash('Nenhum arquivo selecionado', 'error')
                return redirect(url_for('documents.upload'))
            
            uploaded_count = 0
            errors = []
            
            for file in files:
                if file and file.filename:
                    try:
                        # Parse tags
                        tags = []
                        if form.tags.data:
                            tags = [tag.strip() for tag in form.tags.data.split(',') if tag.strip()]
                        
                        # Upload document
                        documento = document_service.upload_document(
                            file=file,
                            user_id=current_user.id,
                            nome=form.nome.data if form.nome.data else None,
                            descricao=form.descricao.data,
                            categoria_id=form.categoria_id.data if form.categoria_id.data != 0 else None,
                            pasta_id=form.pasta_id.data if form.pasta_id.data != 0 else None,
                            tags=tags,
                            check_duplicates=True
                        )
                        uploaded_count += 1
                    except FileValidationError as e:
                        errors.append(f"{file.filename}: {str(e)}")
                    except Exception as e:
                        errors.append(f"{file.filename}: {str(e)}")
            
            if uploaded_count > 0:
                flash(f'{uploaded_count} documento(s) enviado(s) com sucesso!', 'success')
            
            if errors:
                for error in errors:
                    flash(error, 'error')
            
            if uploaded_count > 0:
                return redirect(url_for('documents.list_documents'))
            
        except Exception as e:
            flash(f'Erro ao enviar documentos: {str(e)}', 'error')
    
    return render_template('documents/upload.html', form=form)


# Backwards-compatible endpoint name: some templates/legacy code used
# 'documents.upload_document'. Add an alias so both names work until
# all references are normalized.
try:
    # Register an additional rule with the legacy endpoint name
    document_bp.add_url_rule('/upload', endpoint='upload_document', view_func=upload, methods=['GET', 'POST'])
except Exception:
    # If the rule already exists (during imports in tests), ignore
    pass


@document_bp.route('/<int:id>')
@login_required
def view_document(id):
    """View document details"""
    _init_services()
    try:
        # Get document with permission check
        documento = document_service.get_document(id, current_user.id)
        
        # Get version history
        versoes = document_service.get_version_history(id, current_user.id)
        
        # Get document tags
        tags = document_service.get_document_tags(id, current_user.id)
        
        # Get permissions
        from app.models.permission import Permissao
        permissoes = Permissao.query.filter_by(documento_id=id).all()
        
        # Check if user is owner
        is_owner = documento.usuario_id == current_user.id
        
        # Check user permissions
        can_edit = document_service._has_permission(documento, current_user.id, 'editar') or is_owner
        can_delete = document_service._has_permission(documento, current_user.id, 'excluir') or is_owner
        can_share = document_service._has_permission(documento, current_user.id, 'compartilhar') or is_owner
        
        return render_template(
            'documents/view.html',
            documento=documento,
            versoes=versoes,
            tags=tags,
            permissoes=permissoes,
            is_owner=is_owner,
            can_edit=can_edit,
            can_delete=can_delete,
            can_share=can_share
        )
    except PermissionDeniedError:
        # Return 403 so tests can assert permission-denied behavior instead of redirect
        abort(403)
    except DocumentNotFoundError:
        # Document missing -> 404
        abort(404)
    except Exception as e:
        # Unexpected error -> 500
        app.logger.exception(f'Unexpected error viewing document {id}: {e}')
        abort(500)


@document_bp.route('/<int:id>/download')
@login_required
def download_document(id):
    """Download document"""
    _init_services()
    try:
        # Get document for download with permission check
        result = document_service.download_document(id, current_user.id)
        
        # Send file as attachment
        return send_file(
            result['file_path'],
            mimetype=result['mime_type'],
            as_attachment=True,
            download_name=result['filename']
        )
    except PermissionDeniedError:
        # Return 403 when permission denied
        abort(403)
    except DocumentNotFoundError:
        # File/document not found -> 404
        abort(404)
    except DocumentServiceError:
        # Storage layer reported missing file or similar -> treat as 404
        abort(404)
    except Exception as e:
        from flask import current_app
        current_app.logger.exception(f'Unexpected error downloading document {id}: {e}')
        abort(500)


@document_bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete_document(id):
    """Delete document (move to trash)"""
    _init_services()
    try:
        documento = document_service.delete_document(id, current_user.id)
        return jsonify({'success': True, 'message': 'Documento movido para a lixeira'})
    except PermissionDeniedError:
        return jsonify({'success': False, 'message': 'Você não tem permissão para excluir este documento'}), 403
    except DocumentNotFoundError:
        return jsonify({'success': False, 'message': 'Documento não encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@document_bp.route('/<int:id>/restore', methods=['POST'])
@login_required
def restore_document(id):
    """Restore document from trash"""
    _init_services()
    try:
        documento = document_service.restore_document(id, current_user.id)
        return jsonify({'success': True, 'message': 'Documento restaurado com sucesso'})
    except PermissionDeniedError:
        return jsonify({'success': False, 'message': 'Você não tem permissão para restaurar este documento'}), 403
    except DocumentNotFoundError:
        return jsonify({'success': False, 'message': 'Documento não encontrado'}), 404
    except DocumentServiceError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@document_bp.route('/bulk-delete', methods=['POST'])
@login_required
def bulk_delete():
    """Bulk delete documents"""
    _init_services()
    try:
        data = request.get_json()
        ids = data.get('ids', [])
        
        deleted_count = 0
        errors = []
        
        for doc_id in ids:
            try:
                document_service.delete_document(int(doc_id), current_user.id)
                deleted_count += 1
            except Exception as e:
                errors.append(f"Documento {doc_id}: {str(e)}")
        
        if errors:
            return jsonify({
                'success': False,
                'message': f'{deleted_count} documento(s) excluído(s). Erros: {"; ".join(errors)}'
            }), 207
        
        return jsonify({
            'success': True,
            'message': f'{deleted_count} documento(s) excluído(s) com sucesso'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@document_bp.route('/<int:id>/preview')
@login_required
def preview_document(id):
    """Preview document (for images and PDFs)"""
    _init_services()
    try:
        # Get document with permission check
        result = document_service.view_document(id, current_user.id)
        documento = result['documento']
        file_path = result['file_path']
        
        # Send file for preview
        return send_file(
            file_path,
            mimetype=documento.tipo_mime,
            as_attachment=False
        )
    except PermissionDeniedError:
        abort(403)
    except DocumentNotFoundError:
        abort(404)
    except Exception as e:
        abort(500)


@document_bp.route('/<int:id>/share', methods=['POST'])
@login_required
def share_document(id):
    """Share a document with another user (simple endpoint used by UI/tests)"""
    _init_services()
    try:
        from app.services.permission_service import PermissionService
        documento = document_service.get_document(id, current_user.id)

        usuario_id = request.form.get('usuario_id', type=int)
        tipo_permissao = request.form.get('tipo_permissao')

        if not usuario_id or not tipo_permissao:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400

        permission_types = [t.strip() for t in tipo_permissao.split(',') if t.strip()]

        perm_service = PermissionService()
        perms = perm_service.share_document(
            documento=documento,
            target_user_id=usuario_id,
            permission_types=permission_types,
            shared_by_user_id=current_user.id,
            send_notification=False
        )

        return jsonify({'success': True, 'created': len(perms)})
    except PermissionDeniedError:
        return jsonify({'success': False, 'message': 'Permission denied'}), 403
    except DocumentNotFoundError:
        return jsonify({'success': False, 'message': 'Document not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@document_bp.route('/<int:id>/upload-version', methods=['POST'])
@login_required
def upload_version(id):
    """Upload a new version of a document"""
    _init_services()
    try:
        file = request.files.get('file')
        comentario = request.form.get('comentario')
        
        if not file or not comentario:
            flash('Arquivo e comentário são obrigatórios', 'error')
            return redirect(url_for('documents.view_document', id=id))
        
        # Create new version
        versao = document_service.create_version(
            document_id=id,
            file=file,
            user_id=current_user.id,
            comentario=comentario
        )
        
        flash('Nova versão criada com sucesso!', 'success')
        return redirect(url_for('documents.view_document', id=id))
        
    except Exception as e:
        flash(f'Erro ao criar nova versão: {str(e)}', 'error')
        return redirect(url_for('documents.view_document', id=id))


@document_bp.route('/<int:id>/restore-version/<int:version_number>', methods=['POST'])
@login_required
def restore_version_route(id, version_number):
    """Restore a previous version"""
    _init_services()
    try:
        documento = document_service.restore_version(id, version_number, current_user.id)
        return jsonify({'success': True, 'message': f'Versão {version_number} restaurada com sucesso'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 400


@document_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_document(id):
    """Edit document metadata"""
    _init_services()
    try:
        # Get document with permission check
        documento = document_service.get_document(id, current_user.id)
        
        # Check if user has permission to edit
        if not document_service._has_permission(documento, current_user.id, 'editar') and documento.usuario_id != current_user.id:
            flash('Você não tem permissão para editar este documento', 'error')
            return redirect(url_for('documents.view_document', id=id))
        
        form = DocumentEditForm(obj=documento)
        
        # Populate category choices
        categorias = Categoria.query.filter_by(ativo=True).order_by(Categoria.nome).all()
        form.categoria_id.choices = [(0, 'Selecione uma categoria')] + [(c.id, c.nome) for c in categorias]
        
        # Populate folder choices for current user
        pastas = Pasta.query.filter_by(usuario_id=current_user.id).order_by(Pasta.nome).all()
        form.pasta_id.choices = [(0, 'Nenhuma pasta')] + [(p.id, p.nome) for p in pastas]
        
        # Pre-populate form with current values
        if request.method == 'GET':
            form.categoria_id.data = documento.categoria_id if documento.categoria_id else 0
            form.pasta_id.data = documento.pasta_id if documento.pasta_id else 0
            
            # Get current tags
            tags = document_service.get_document_tags(id, current_user.id)
            form.tags.data = ', '.join(tags)
        
        if form.validate_on_submit():
            try:
                # Parse tags
                tags = []
                if form.tags.data:
                    tags = [tag.strip() for tag in form.tags.data.split(',') if tag.strip()]
                
                # Update document
                documento = document_service.update_document_metadata(
                    document_id=id,
                    user_id=current_user.id,
                    nome=form.nome.data,
                    descricao=form.descricao.data,
                    categoria_id=form.categoria_id.data if form.categoria_id.data != 0 else None,
                    pasta_id=form.pasta_id.data if form.pasta_id.data != 0 else None,
                    tags=tags
                )
                
                flash('Documento atualizado com sucesso!', 'success')
                return redirect(url_for('documents.view_document', id=id))
                
            except Exception as e:
                flash(f'Erro ao atualizar documento: {str(e)}', 'error')
        
        return render_template('documents/edit.html', form=form, documento=documento)
        
    except PermissionDeniedError:
        flash('Você não tem permissão para editar este documento', 'error')
        return redirect(url_for('documents.list_documents'))
    except DocumentNotFoundError:
        flash('Documento não encontrado', 'error')
        return redirect(url_for('documents.list_documents'))
    except Exception as e:
        flash(f'Erro ao carregar documento: {str(e)}', 'error')
        return redirect(url_for('documents.list_documents'))
