"""
Administration routes
"""
from flask import (
    render_template, request, jsonify, send_file, Response,
    flash, redirect, url_for, send_from_directory, current_app
)
from flask_login import login_required, current_user
from datetime import datetime
from functools import wraps
import io
from app.admin import admin_bp
from app.services.audit_service import AuditService
from app.services.admin_service import AdminService


def admin_required(f):
    """Decorator to require admin privileges"""
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        # Check if user has admin or auditor profile
        if not current_user.perfil or current_user.perfil.nome not in ['Administrador', 'Auditor']:
            flash('Privilégios de administrador ou auditor são necessários.', 'danger')
            return redirect(url_for('documents.list_documents'))
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    """Admin dashboard with system statistics"""
    admin_service = AdminService()
    
    # Get dashboard statistics
    stats = admin_service.get_dashboard_statistics()
    upload_stats = admin_service.get_upload_statistics(days=30)
    storage_by_user = admin_service.get_storage_by_user(limit=10)
    recent_activity = admin_service.get_recent_activity(limit=20)
    user_stats = admin_service.get_user_statistics()
    
    return render_template(
        'admin/dashboard.html',
        stats=stats,
        upload_stats=upload_stats,
        storage_by_user=storage_by_user,
        recent_activity=recent_activity,
        user_stats=user_stats
    )


@admin_bp.route('/users')
@admin_required
def users():
    """User management list page"""
    from app.repositories.user_repository import UserRepository, PerfilRepository
    
    user_repo = UserRepository()
    perfil_repo = PerfilRepository()
    
    # Get filter parameters
    search_query = request.args.get('q', '')
    perfil_filter = request.args.get('perfil', type=int)
    status_filter = request.args.get('status', '')
    
    # Build query
    if search_query:
        users_list = user_repo.search_users(search_query, active_only=False)
    else:
        users_list = user_repo.get_all()
    
    # Apply filters
    if perfil_filter:
        users_list = [u for u in users_list if u.perfil_id == perfil_filter]
    
    if status_filter == 'active':
        users_list = [u for u in users_list if u.ativo]
    elif status_filter == 'inactive':
        users_list = [u for u in users_list if not u.ativo]
    
    # Get all profiles for filter dropdown
    perfis = perfil_repo.get_all()
    
    return render_template(
        'admin/users.html',
        users=users_list,
        perfis=perfis,
        search_query=search_query,
        perfil_filter=perfil_filter,
        status_filter=status_filter
    )


# Backwards-compatible endpoint name: some templates or legacy code may use
# 'admin.list_users' — register an alias so both names work until all refs
# are normalized.
try:
    admin_bp.add_url_rule('/users', endpoint='list_users', view_func=users)
except Exception:
    # If rule already exists during import in tests, ignore
    pass


@admin_bp.route('/users/list', methods=['GET'])
@login_required
def users_list_json():
    """API endpoint to get users list in JSON format"""
    from app.repositories.user_repository import UserRepository

    user_repo = UserRepository()

    # Get all active users except current user
    all_users = user_repo.get_all()
    users_list = [
        {
            'id': u.id,
            'nome': u.nome,
            'email': u.email
        }
        for u in all_users
        if u.ativo and u.id != current_user.id
    ]

    return jsonify({'users': users_list})


@admin_bp.route('/users/create', methods=['GET', 'POST'])
@admin_required
def user_create():
    """Create new user"""
    from app.admin.forms import UserCreateForm
    from app.repositories.user_repository import UserRepository, PerfilRepository
    from app.services.audit_service import AuditService
    
    user_repo = UserRepository()
    perfil_repo = PerfilRepository()
    audit_service = AuditService()
    
    form = UserCreateForm()
    
    # Populate profile choices
    perfis = perfil_repo.get_all()
    form.perfil_id.choices = [(p.id, p.nome) for p in perfis]
    
    if form.validate_on_submit():
        try:
            # Create user
            from app.models import User
            user = User(
                nome=form.nome.data,
                email=form.email.data,
                perfil_id=form.perfil_id.data,
                ativo=form.ativo.data
            )
            user.set_password(form.senha.data)
            
            created_user = user_repo.create(
                nome=user.nome,
                email=user.email,
                senha_hash=user.senha_hash,
                perfil_id=user.perfil_id,
                ativo=user.ativo
            )
            
            # Log action
            audit_service.log_action(
                usuario_id=current_user.id,
                acao='user_create',
                tabela='usuarios',
                registro_id=created_user.id,
                dados={'email': created_user.email, 'nome': created_user.nome},
                ip_address=request.remote_addr
            )
            
            flash(f'Usuário {created_user.nome} criado com sucesso!', 'success')
            return redirect(url_for('admin.users'))
        
        except Exception as e:
            flash(f'Erro ao criar usuário: {str(e)}', 'danger')
    
    return render_template('admin/user_form.html', form=form, action='create')


@admin_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def user_edit(user_id):
    """Edit existing user"""
    from app.admin.forms import UserEditForm
    from app.repositories.user_repository import UserRepository, PerfilRepository
    from app.services.audit_service import AuditService
    
    user_repo = UserRepository()
    perfil_repo = PerfilRepository()
    audit_service = AuditService()
    
    user = user_repo.get_by_id(user_id)
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('admin.users'))
    
    form = UserEditForm(user_id=user_id, obj=user)
    
    # Populate profile choices
    perfis = perfil_repo.get_all()
    form.perfil_id.choices = [(p.id, p.nome) for p in perfis]
    
    if form.validate_on_submit():
        try:
            # Update user
            user.nome = form.nome.data
            user.email = form.email.data
            user.perfil_id = form.perfil_id.data
            user.ativo = form.ativo.data
            
            # Save changes
            user_repo.save(user)
            
            # Log action
            audit_service.log_action(
                usuario_id=current_user.id,
                acao='user_update',
                tabela='usuarios',
                registro_id=user.id,
                dados={'email': user.email, 'nome': user.nome},
                ip_address=request.remote_addr
            )
            
            flash(f'Usuário {user.nome} atualizado com sucesso!', 'success')
            return redirect(url_for('admin.users'))
        
        except Exception as e:
            flash(f'Erro ao atualizar usuário: {str(e)}', 'danger')
    
    return render_template('admin/user_form.html', form=form, action='edit', user=user)


@admin_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def user_toggle_status(user_id):
    """Activate or deactivate user"""
    from app.repositories.user_repository import UserRepository
    from app.services.audit_service import AuditService
    
    user_repo = UserRepository()
    audit_service = AuditService()
    
    user = user_repo.get_by_id(user_id)
    if not user:
        return jsonify({'error': 'Usuário não encontrado'}), 404
    
    # Prevent self-deactivation
    if user.id == current_user.id:
        return jsonify({'error': 'Você não pode desativar sua própria conta'}), 400
    
    try:
        user.ativo = not user.ativo
        user_repo.save(user)
        
        # Log action
        action = 'user_activate' if user.ativo else 'user_deactivate'
        audit_service.log_action(
            usuario_id=current_user.id,
            acao=action,
            tabela='usuarios',
            registro_id=user.id,
            dados={'email': user.email, 'ativo': user.ativo},
            ip_address=request.remote_addr
        )
        
        status_text = 'ativado' if user.ativo else 'desativado'
        return jsonify({
            'success': True,
            'message': f'Usuário {status_text} com sucesso',
            'ativo': user.ativo
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['GET', 'POST'])
@admin_required
def user_reset_password(user_id):
    """Admin reset user password"""
    from app.admin.forms import UserPasswordResetForm
    from app.repositories.user_repository import UserRepository
    from app.services.audit_service import AuditService
    
    user_repo = UserRepository()
    audit_service = AuditService()
    
    user = user_repo.get_by_id(user_id)
    if not user:
        flash('Usuário não encontrado.', 'danger')
        return redirect(url_for('admin.users'))
    
    form = UserPasswordResetForm()
    
    if form.validate_on_submit():
        try:
            user.set_password(form.nova_senha.data)
            user.tentativas_login = 0
            user.bloqueado_ate = None
            user_repo.save(user)
            
            # Log action
            audit_service.log_action(
                usuario_id=current_user.id,
                acao='admin_password_reset',
                tabela='usuarios',
                registro_id=user.id,
                dados={'email': user.email},
                ip_address=request.remote_addr
            )
            
            flash(f'Senha do usuário {user.nome} redefinida com sucesso!', 'success')
            return redirect(url_for('admin.users'))
        
        except Exception as e:
            flash(f'Erro ao redefinir senha: {str(e)}', 'danger')
    
    return render_template('admin/user_reset_password.html', form=form, user=user)


@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    """System settings configuration"""
    from app.admin.forms import SystemSettingsForm
    from app.repositories.settings_repository import SettingsRepository
    from app.services.audit_service import AuditService
    import os
    import sys
    from importlib.metadata import version as get_version
    from werkzeug.utils import secure_filename
    
    settings_repo = SettingsRepository()
    audit_service = AuditService()
    
    # Initialize defaults if needed
    settings_repo.initialize_defaults()
    
    form = SystemSettingsForm()
    
    if form.validate_on_submit():
        try:
            # Update settings
            settings_repo.set_value('max_file_size_mb', form.max_file_size.data, tipo='int')
            settings_repo.set_value('allowed_extensions', form.allowed_extensions.data, tipo='string')
            settings_repo.set_value('trash_retention_days', form.trash_retention_days.data, tipo='int')
            settings_repo.set_value('max_versions_per_document', form.max_versions.data, tipo='int')
            settings_repo.set_value('session_timeout_minutes', form.session_timeout.data, tipo='int')
            
            # Handle logo upload
            if form.logo.data:
                from flask import current_app
                logo_file = form.logo.data
                
                # Generate unique filename to avoid conflicts
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                original_filename = secure_filename(logo_file.filename)
                filename = f'logo_{timestamp}_{original_filename}'
                
                # Create logos directory in uploads folder if it doesn't exist
                logos_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'logos')
                os.makedirs(logos_dir, exist_ok=True)
                
                # Delete old logo file if exists
                old_logo = settings_repo.get_value('system_logo', '')
                if old_logo:
                    old_logo_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_logo)
                    if os.path.exists(old_logo_path):
                        try:
                            os.remove(old_logo_path)
                        except Exception as e:
                            current_app.logger.warning(f'Erro ao remover logo antigo: {str(e)}')
                
                # Save new file
                logo_path = os.path.join(logos_dir, filename)
                logo_file.save(logo_path)
                
                # Store relative path (relative to UPLOAD_FOLDER)
                relative_path = f'logos/{filename}'
                settings_repo.set_value('system_logo', relative_path, tipo='string')
            
            # Log action
            audit_service.log_action(
                usuario_id=current_user.id,
                acao='settings_update',
                tabela='system_settings',
                registro_id=None,
                dados={'updated_by': current_user.email},
                ip_address=request.remote_addr
            )
            
            flash('Configurações atualizadas com sucesso!', 'success')
            return redirect(url_for('admin.settings'))
        
        except Exception as e:
            flash(f'Erro ao atualizar configurações: {str(e)}', 'danger')
    
    # Load current settings
    if request.method == 'GET':
        form.max_file_size.data = settings_repo.get_value('max_file_size_mb', 50)
        form.allowed_extensions.data = settings_repo.get_value('allowed_extensions', 'pdf,doc,docx,xls,xlsx,jpg,png,tif')
        form.trash_retention_days.data = settings_repo.get_value('trash_retention_days', 30)
        form.max_versions.data = settings_repo.get_value('max_versions_per_document', 10)
        form.session_timeout.data = settings_repo.get_value('session_timeout_minutes', 60)
    
    # Get current logo
    current_logo = settings_repo.get_value('system_logo', '')
    
    # Get system version info
    python_version = sys.version.split()[0]
    flask_version = get_version('flask')
    
    return render_template(
        'admin/settings.html',
        form=form,
        current_logo=current_logo,
        python_version=python_version,
        flask_version=flask_version
    )


@admin_bp.route('/reports')
@admin_required
def reports():
    """Reports main page"""
    return render_template('admin/reports.html')


@admin_bp.route('/reports/usage')
@admin_required
def report_usage():
    """Generate usage report"""
    from app.services.report_service import ReportService
    from datetime import datetime, timedelta
    
    report_service = ReportService()
    
    # Get date parameters
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    
    if data_inicio:
        try:
            data_inicio = datetime.fromisoformat(data_inicio)
        except ValueError:
            data_inicio = None
    
    if data_fim:
        try:
            data_fim = datetime.fromisoformat(data_fim)
        except ValueError:
            data_fim = None
    
    # Default to last 30 days
    if not data_inicio:
        data_inicio = datetime.utcnow() - timedelta(days=30)
    if not data_fim:
        data_fim = datetime.utcnow()
    
    # Generate report
    report_data = report_service.generate_usage_report(data_inicio, data_fim)
    
    # Check if export requested
    export_format = request.args.get('export')
    if export_format == 'csv':
        csv_data = report_service.export_report_csv(report_data, 'usage')
        return send_file(
            csv_data,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'relatorio_uso_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    
    return render_template('admin/report_usage.html', report=report_data)


@admin_bp.route('/reports/access')
@admin_required
def report_access():
    """Generate access report"""
    from app.services.report_service import ReportService
    from datetime import datetime, timedelta
    
    report_service = ReportService()
    
    # Get parameters
    data_inicio = request.args.get('data_inicio')
    data_fim = request.args.get('data_fim')
    usuario_id = request.args.get('usuario_id', type=int)
    documento_id = request.args.get('documento_id', type=int)
    
    if data_inicio:
        try:
            data_inicio = datetime.fromisoformat(data_inicio)
        except ValueError:
            data_inicio = None
    
    if data_fim:
        try:
            data_fim = datetime.fromisoformat(data_fim)
        except ValueError:
            data_fim = None
    
    # Default to last 30 days
    if not data_inicio:
        data_inicio = datetime.utcnow() - timedelta(days=30)
    if not data_fim:
        data_fim = datetime.utcnow()
    
    # Generate report
    report_data = report_service.generate_access_report(
        data_inicio, data_fim, usuario_id, documento_id
    )
    
    # Check if export requested
    export_format = request.args.get('export')
    if export_format == 'csv':
        csv_data = report_service.export_report_csv(report_data, 'access')
        return send_file(
            csv_data,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'relatorio_acessos_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    
    # Get users for filter
    from app.repositories.user_repository import UserRepository
    user_repo = UserRepository()
    users = user_repo.get_all()
    
    return render_template('admin/report_access.html', report=report_data, users=users)


@admin_bp.route('/reports/storage')
@admin_required
def report_storage():
    """Generate storage report"""
    from app.services.report_service import ReportService
    from datetime import datetime
    
    report_service = ReportService()
    
    # Generate report
    report_data = report_service.generate_storage_report()
    
    # Check if export requested
    export_format = request.args.get('export')
    if export_format == 'csv':
        csv_data = report_service.export_report_csv(report_data, 'storage')
        return send_file(
            csv_data,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'relatorio_armazenamento_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    
    return render_template('admin/report_storage.html', report=report_data)


# Audit Log Routes

@admin_bp.route('/audit/logs')
@admin_required
def audit_logs():
    """
    View audit logs with filtering and pagination
    
    Query Parameters:
        - usuario_id: Filter by user ID
        - acao: Filter by action type
        - tabela: Filter by table name
        - data_inicio: Start date (ISO format)
        - data_fim: End date (ISO format)
        - ip_address: Filter by IP address
        - page: Page number (default: 1)
        - per_page: Items per page (default: 50)
    """
    audit_service = AuditService()
    
    # Get filter parameters from query string
    usuario_id = request.args.get('usuario_id', type=int)
    acao = request.args.get('acao')
    tabela = request.args.get('tabela')
    ip_address = request.args.get('ip_address')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    
    # Parse date parameters
    data_inicio = None
    data_fim = None
    
    if request.args.get('data_inicio'):
        try:
            data_inicio = datetime.fromisoformat(request.args.get('data_inicio'))
        except ValueError:
            pass
    
    if request.args.get('data_fim'):
        try:
            data_fim = datetime.fromisoformat(request.args.get('data_fim'))
        except ValueError:
            pass
    
    # Get filtered logs
    result = audit_service.filter_logs(
        usuario_id=usuario_id,
        acao=acao,
        tabela=tabela,
        data_inicio=data_inicio,
        data_fim=data_fim,
        ip_address=ip_address,
        page=page,
        per_page=per_page
    )
    
    # Convert logs to dictionaries for JSON response
    logs_data = []
    for log in result['items']:
        logs_data.append({
            'id': log.id,
            'usuario_id': log.usuario_id,
            'usuario_nome': log.usuario.nome if log.usuario else None,
            'acao': log.acao,
            'tabela': log.tabela,
            'registro_id': log.registro_id,
            'dados': log.dados,
            'ip_address': log.ip_address,
            'user_agent': log.user_agent,
            'data_hora': log.data_hora.isoformat() if log.data_hora else None
        })
    
    return jsonify({
        'logs': logs_data,
        'pagination': {
            'total': result['total'],
            'page': result['page'],
            'per_page': result['per_page'],
            'pages': result['pages'],
            'has_prev': result['has_prev'],
            'has_next': result['has_next']
        }
    })


@admin_bp.route('/audit/logs/<int:log_id>')
@admin_required
def audit_log_detail(log_id):
    """Get detailed information about a specific audit log entry"""
    audit_service = AuditService()
    
    log = audit_service.audit_repository.get_by_id(log_id)
    
    if not log:
        return jsonify({'error': 'Audit log not found'}), 404
    
    return jsonify({
        'id': log.id,
        'usuario_id': log.usuario_id,
        'usuario_nome': log.usuario.nome if log.usuario else None,
        'usuario_email': log.usuario.email if log.usuario else None,
        'acao': log.acao,
        'tabela': log.tabela,
        'registro_id': log.registro_id,
        'dados': log.dados,
        'ip_address': log.ip_address,
        'user_agent': log.user_agent,
        'data_hora': log.data_hora.isoformat() if log.data_hora else None
    })


@admin_bp.route('/audit/document/<int:documento_id>')
@admin_required
def audit_document_trail(documento_id):
    """Get complete audit trail for a specific document"""
    audit_service = AuditService()
    
    logs = audit_service.get_document_audit_trail(documento_id)
    
    logs_data = []
    for log in logs:
        logs_data.append({
            'id': log.id,
            'usuario_id': log.usuario_id,
            'usuario_nome': log.usuario.nome if log.usuario else None,
            'acao': log.acao,
            'dados': log.dados,
            'ip_address': log.ip_address,
            'data_hora': log.data_hora.isoformat() if log.data_hora else None
        })
    
    return jsonify({
        'documento_id': documento_id,
        'total_actions': len(logs_data),
        'audit_trail': logs_data
    })


@admin_bp.route('/audit/user/<int:usuario_id>')
@admin_required
def audit_user_activity(usuario_id):
    """Get activity history for a specific user"""
    audit_service = AuditService()
    
    limit = request.args.get('limit', 100, type=int)
    logs = audit_service.get_user_activity(usuario_id, limit=limit)
    
    logs_data = []
    for log in logs:
        logs_data.append({
            'id': log.id,
            'acao': log.acao,
            'tabela': log.tabela,
            'registro_id': log.registro_id,
            'dados': log.dados,
            'ip_address': log.ip_address,
            'data_hora': log.data_hora.isoformat() if log.data_hora else None
        })
    
    return jsonify({
        'usuario_id': usuario_id,
        'total_actions': len(logs_data),
        'activity': logs_data
    })


@admin_bp.route('/audit/recent')
@admin_required
def audit_recent_activity():
    """Get recent system activity"""
    audit_service = AuditService()
    
    hours = request.args.get('hours', 24, type=int)
    limit = request.args.get('limit', 100, type=int)
    
    logs = audit_service.get_recent_activity(hours=hours, limit=limit)
    
    logs_data = []
    for log in logs:
        logs_data.append({
            'id': log.id,
            'usuario_id': log.usuario_id,
            'usuario_nome': log.usuario.nome if log.usuario else None,
            'acao': log.acao,
            'tabela': log.tabela,
            'registro_id': log.registro_id,
            'dados': log.dados,
            'ip_address': log.ip_address,
            'data_hora': log.data_hora.isoformat() if log.data_hora else None
        })
    
    return jsonify({
        'hours': hours,
        'total_actions': len(logs_data),
        'recent_activity': logs_data
    })


@admin_bp.route('/audit/statistics')
@admin_required
def audit_statistics():
    """Get audit statistics"""
    audit_service = AuditService()
    
    # Parse date parameters
    data_inicio = None
    data_fim = None
    
    if request.args.get('data_inicio'):
        try:
            data_inicio = datetime.fromisoformat(request.args.get('data_inicio'))
        except ValueError:
            pass
    
    if request.args.get('data_fim'):
        try:
            data_fim = datetime.fromisoformat(request.args.get('data_fim'))
        except ValueError:
            pass
    
    # Get statistics
    action_stats = audit_service.get_action_statistics(data_inicio, data_fim)
    user_stats = audit_service.get_user_activity_statistics(data_inicio, data_fim, limit=10)
    
    days = request.args.get('days', 30, type=int)
    daily_activity = audit_service.get_daily_activity(days=days)
    
    return jsonify({
        'action_statistics': action_stats,
        'top_users': user_stats,
        'daily_activity': daily_activity,
        'period': {
            'data_inicio': data_inicio.isoformat() if data_inicio else None,
            'data_fim': data_fim.isoformat() if data_fim else None
        }
    })


@admin_bp.route('/audit/export')
@admin_required
def audit_export():
    """
    Export audit logs
    
    Query Parameters:
        - usuario_id: Filter by user ID
        - data_inicio: Start date (ISO format)
        - data_fim: End date (ISO format)
        - format: Export format ('json' or 'csv', default: 'json')
    """
    audit_service = AuditService()
    
    # Get filter parameters
    usuario_id = request.args.get('usuario_id', type=int)
    export_format = request.args.get('format', 'json')
    
    # Parse date parameters
    data_inicio = None
    data_fim = None
    
    if request.args.get('data_inicio'):
        try:
            data_inicio = datetime.fromisoformat(request.args.get('data_inicio'))
        except ValueError:
            pass
    
    if request.args.get('data_fim'):
        try:
            data_fim = datetime.fromisoformat(request.args.get('data_fim'))
        except ValueError:
            pass
    
    # Export logs
    exported_data = audit_service.export_logs(
        usuario_id=usuario_id,
        data_inicio=data_inicio,
        data_fim=data_fim,
        format=export_format
    )
    
    # Prepare response based on format
    if export_format == 'csv':
        # Create CSV response
        output = io.BytesIO()
        output.write(exported_data.encode('utf-8'))
        output.seek(0)
        
        filename = f"audit_logs_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
    
    else:  # JSON format
        return Response(
            exported_data,
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename=audit_logs_{datetime.utcnow().strftime("%Y%m%d_%H%M%S")}.json'
            }
        )


@admin_bp.route('/audit/reports/<report_type>')
@admin_required
def audit_report(report_type):
    """
    Generate audit report
    
    Report Types:
        - summary: Overall system activity summary
        - user_activity: Activity for a specific user (requires usuario_id parameter)
        - document_activity: Activity for a specific document (requires documento_id parameter)
        - security: Security-focused report (login attempts, failures, etc.)
    
    Query Parameters:
        - data_inicio: Start date (ISO format)
        - data_fim: End date (ISO format)
        - usuario_id: User ID (for user_activity report)
        - documento_id: Document ID (for document_activity report)
    """
    audit_service = AuditService()
    
    # Parse date parameters
    data_inicio = None
    data_fim = None
    
    if request.args.get('data_inicio'):
        try:
            data_inicio = datetime.fromisoformat(request.args.get('data_inicio'))
        except ValueError:
            pass
    
    if request.args.get('data_fim'):
        try:
            data_fim = datetime.fromisoformat(request.args.get('data_fim'))
        except ValueError:
            pass
    
    # Get additional parameters
    kwargs = {}
    if request.args.get('usuario_id'):
        kwargs['usuario_id'] = int(request.args.get('usuario_id'))
    if request.args.get('documento_id'):
        kwargs['documento_id'] = int(request.args.get('documento_id'))
    
    try:
        # Generate report
        report = audit_service.generate_audit_report(
            report_type=report_type,
            data_inicio=data_inicio,
            data_fim=data_fim,
            **kwargs
        )
        
        return jsonify(report)
    
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@admin_bp.route('/audit/login-history')
@admin_required
def audit_login_history():
    """Get login attempt history"""
    audit_service = AuditService()
    
    usuario_id = request.args.get('usuario_id', type=int)
    success_only = request.args.get('success_only', 'false').lower() == 'true'
    hours = request.args.get('hours', 24, type=int)
    
    logs = audit_service.get_login_history(
        usuario_id=usuario_id,
        success_only=success_only,
        hours=hours
    )
    
    logs_data = []
    for log in logs:
        logs_data.append({
            'id': log.id,
            'usuario_id': log.usuario_id,
            'usuario_nome': log.usuario.nome if log.usuario else None,
            'acao': log.acao,
            'dados': log.dados,
            'ip_address': log.ip_address,
            'data_hora': log.data_hora.isoformat() if log.data_hora else None
        })
    
    return jsonify({
        'total_attempts': len(logs_data),
        'login_history': logs_data
    })


@admin_bp.route('/uploads/<path:filename>')
def uploaded_file(filename):
    """Serve uploaded files from the uploads folder"""
    return send_from_directory(
        current_app.config['UPLOAD_FOLDER'],
        filename
    )
