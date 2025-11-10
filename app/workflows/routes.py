"""
Workflow routes
"""
from flask import render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app.workflows import workflow_bp
from app.workflows.forms import WorkflowForm, ApprovalActionForm
from app.services.workflow_service import (
    WorkflowService,
    WorkflowServiceError,
    WorkflowNotFoundError,
    ApprovalNotFoundError,
    UnauthorizedApproverError
)
from app.models.user import User
from app.models.document import Documento
from app import db
import json


@workflow_bp.route('/')
@login_required
def list_workflows():
    """List all workflows"""
    # Check if user has permission to manage workflows
    if not current_user.has_permission('approve'):
        flash('Você não tem permissão para acessar workflows', 'danger')
        return redirect(url_for('documents.list_documents'))
    
    workflow_service = WorkflowService()
    
    # Get all workflows (active and inactive)
    workflows = workflow_service.workflow_repo.get_all()
    
    return render_template(
        'workflows/list.html',
        workflows=workflows,
        title='Workflows'
    )


@workflow_bp.route('/new', methods=['GET', 'POST'])
@login_required
def create_workflow():
    """Create new workflow"""
    # Check if user has permission to manage workflows
    if not current_user.has_permission('approve'):
        flash('Você não tem permissão para criar workflows', 'danger')
        return redirect(url_for('workflows.list_workflows'))
    
    form = WorkflowForm()
    
    # Get all active users for approver selection
    users = User.query.filter_by(ativo=True).order_by(User.nome).all()
    
    if form.validate_on_submit():
        try:
            # Parse stages from JSON
            stages_data = json.loads(form.stages_json.data) if form.stages_json.data else []
            
            if not stages_data:
                flash('Adicione pelo menos um estágio ao workflow', 'warning')
                return render_template(
                    'workflows/form.html',
                    form=form,
                    users=users,
                    title='Novo Workflow'
                )
            
            # Build configuration
            configuracao = {
                'stages': stages_data
            }
            
            # Create workflow
            workflow_service = WorkflowService()
            workflow = workflow_service.create_workflow(
                nome=form.nome.data,
                descricao=form.descricao.data,
                configuracao=configuracao,
                criado_por=current_user.id
            )
            
            # Set active status
            if not form.ativo.data:
                workflow.ativo = False
                db.session.commit()
            
            flash(f'Workflow "{workflow.nome}" criado com sucesso!', 'success')
            return redirect(url_for('workflows.list_workflows'))
            
        except WorkflowServiceError as e:
            flash(f'Erro ao criar workflow: {str(e)}', 'danger')
        except Exception as e:
            flash(f'Erro inesperado: {str(e)}', 'danger')
    
    return render_template(
        'workflows/form.html',
        form=form,
        users=users,
        title='Novo Workflow'
    )


@workflow_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_workflow(id):
    """Edit existing workflow"""
    # Check if user has permission to manage workflows
    if not current_user.has_permission('approve'):
        flash('Você não tem permissão para editar workflows', 'danger')
        return redirect(url_for('workflows.list_workflows'))
    
    workflow_service = WorkflowService()
    
    try:
        workflow = workflow_service.get_workflow(id)
    except WorkflowNotFoundError:
        flash('Workflow não encontrado', 'danger')
        return redirect(url_for('workflows.list_workflows'))
    
    form = WorkflowForm(workflow_id=id, obj=workflow)
    
    # Get all active users for approver selection
    users = User.query.filter_by(ativo=True).order_by(User.nome).all()
    
    if form.validate_on_submit():
        try:
            # Parse stages from JSON
            stages_data = json.loads(form.stages_json.data) if form.stages_json.data else []
            
            if not stages_data:
                flash('Adicione pelo menos um estágio ao workflow', 'warning')
                return render_template(
                    'workflows/form.html',
                    form=form,
                    users=users,
                    workflow=workflow,
                    title='Editar Workflow'
                )
            
            # Build configuration
            configuracao = {
                'stages': stages_data
            }
            
            # Update workflow
            workflow_service.update_workflow(
                workflow_id=id,
                nome=form.nome.data,
                descricao=form.descricao.data,
                configuracao=configuracao,
                ativo=form.ativo.data
            )
            
            flash(f'Workflow "{form.nome.data}" atualizado com sucesso!', 'success')
            return redirect(url_for('workflows.list_workflows'))
            
        except WorkflowServiceError as e:
            flash(f'Erro ao atualizar workflow: {str(e)}', 'danger')
        except Exception as e:
            flash(f'Erro inesperado: {str(e)}', 'danger')
    
    # Pre-populate stages JSON for editing
    if request.method == 'GET':
        form.stages_json.data = json.dumps(workflow.configuracao.get('stages', []))
    
    return render_template(
        'workflows/form.html',
        form=form,
        users=users,
        workflow=workflow,
        title='Editar Workflow'
    )


@workflow_bp.route('/<int:id>/toggle', methods=['POST'])
@login_required
def toggle_workflow(id):
    """Toggle workflow active status"""
    # Check if user has permission to manage workflows
    if not current_user.has_permission('approve'):
        return jsonify({'success': False, 'message': 'Sem permissão'}), 403
    
    workflow_service = WorkflowService()
    
    try:
        workflow = workflow_service.get_workflow(id)
        workflow_service.update_workflow(
            workflow_id=id,
            ativo=not workflow.ativo
        )
        
        status = 'ativado' if not workflow.ativo else 'desativado'
        return jsonify({
            'success': True,
            'message': f'Workflow {status} com sucesso',
            'ativo': not workflow.ativo
        })
        
    except WorkflowNotFoundError:
        return jsonify({'success': False, 'message': 'Workflow não encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@workflow_bp.route('/approvals')
@login_required
def pending_approvals():
    """List pending approvals for current user"""
    workflow_service = WorkflowService()
    
    # Get pending approvals where user is an approver
    approvals = workflow_service.get_pending_approvals_for_user(current_user.id)
    
    return render_template(
        'workflows/approvals.html',
        approvals=approvals,
        title='Aprovações Pendentes'
    )


@workflow_bp.route('/approval/<int:id>')
@login_required
def view_approval(id):
    """View approval details"""
    workflow_service = WorkflowService()
    
    try:
        approval = workflow_service.aprovacao_repo.get_by_id(id)
        if not approval:
            flash('Aprovação não encontrada', 'danger')
            return redirect(url_for('workflows.pending_approvals'))
        
        # Get approval history
        history = workflow_service.get_approval_history(id)
        
        # Check if user is authorized approver
        is_approver = workflow_service._is_authorized_approver(approval, current_user.id)
        
        # Create form for approval/rejection
        form = ApprovalActionForm()
        
        return render_template(
            'workflows/approval_detail.html',
            approval=approval,
            history=history,
            is_approver=is_approver,
            form=form,
            title='Detalhes da Aprovação'
        )
        
    except Exception as e:
        flash(f'Erro ao carregar aprovação: {str(e)}', 'danger')
        return redirect(url_for('workflows.pending_approvals'))


@workflow_bp.route('/approval/<int:id>/approve', methods=['POST'])
@login_required
def approve_document(id):
    """Approve document"""
    workflow_service = WorkflowService()
    form = ApprovalActionForm()
    
    if form.validate_on_submit():
        try:
            workflow_service.approve_document(
                aprovacao_id=id,
                aprovador_id=current_user.id,
                comentario=form.comentario.data
            )
            
            flash('Documento aprovado com sucesso!', 'success')
            return redirect(url_for('workflows.pending_approvals'))
            
        except ApprovalNotFoundError:
            flash('Aprovação não encontrada', 'danger')
        except UnauthorizedApproverError:
            flash('Você não está autorizado a aprovar este documento', 'danger')
        except WorkflowServiceError as e:
            flash(f'Erro ao aprovar documento: {str(e)}', 'danger')
        except Exception as e:
            flash(f'Erro inesperado: {str(e)}', 'danger')
    else:
        flash('Comentário é obrigatório para aprovação', 'warning')
    
    return redirect(url_for('workflows.view_approval', id=id))


# Backwards-compatible alias: allow POST to '/<id>/approve' in addition to '/approval/<id>/approve'
try:
    workflow_bp.add_url_rule('/<int:id>/approve', endpoint='approve_document_short', view_func=approve_document, methods=['POST'])
except Exception:
    pass


@workflow_bp.route('/submit', methods=['POST'])
@login_required
def submit_for_approval():
    """Endpoint to submit a document for a workflow (used by UI/tests)"""
    try:
        documento_id = request.form.get('documento_id', type=int)
        workflow_id = request.form.get('workflow_id', type=int)

        if not documento_id or not workflow_id:
            return jsonify({'success': False, 'message': 'Missing parameters'}), 400

        workflow_service = WorkflowService()
        aprovacao = workflow_service.submit_for_approval(
            documento_id=documento_id,
            workflow_id=workflow_id,
            submetido_por=current_user.id
        )

        return jsonify({'success': True, 'aprovacao_id': aprovacao.id})
    except WorkflowNotFoundError:
        return jsonify({'success': False, 'message': 'Workflow not found'}), 404
    except WorkflowServiceError as e:
        return jsonify({'success': False, 'message': str(e)}), 400
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@workflow_bp.route('/approval/<int:id>/reject', methods=['POST'])
@login_required
def reject_document(id):
    """Reject document"""
    workflow_service = WorkflowService()
    form = ApprovalActionForm()
    
    if form.validate_on_submit():
        try:
            workflow_service.reject_document(
                aprovacao_id=id,
                aprovador_id=current_user.id,
                comentario=form.comentario.data
            )
            
            flash('Documento rejeitado', 'info')
            return redirect(url_for('workflows.pending_approvals'))
            
        except ApprovalNotFoundError:
            flash('Aprovação não encontrada', 'danger')
        except UnauthorizedApproverError:
            flash('Você não está autorizado a rejeitar este documento', 'danger')
        except WorkflowServiceError as e:
            flash(f'Erro ao rejeitar documento: {str(e)}', 'danger')
        except Exception as e:
            flash(f'Erro inesperado: {str(e)}', 'danger')
    else:
        flash('Comentário é obrigatório para rejeição', 'warning')
    
    return redirect(url_for('workflows.view_approval', id=id))
