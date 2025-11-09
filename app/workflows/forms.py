"""
Workflow management forms
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, FieldList, FormField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models.user import User
from app.repositories.workflow_repository import WorkflowRepository


class WorkflowStageForm(FlaskForm):
    """Form for a single workflow stage"""
    class Meta:
        csrf = False  # Disable CSRF for nested forms
    
    name = StringField(
        'Nome do Estágio',
        validators=[DataRequired('Nome do estágio é obrigatório'), Length(max=100)],
        render_kw={'placeholder': 'Ex: Revisão Inicial, Aprovação Final...'}
    )
    approvers = SelectMultipleField(
        'Aprovadores',
        coerce=int,
        validators=[DataRequired('Selecione pelo menos um aprovador')],
        choices=[]
    )
    require_all = BooleanField(
        'Requer aprovação de todos',
        default=False
    )


class WorkflowForm(FlaskForm):
    """Form for creating/editing workflows"""
    nome = StringField(
        'Nome do Workflow',
        validators=[DataRequired('Nome é obrigatório'), Length(max=100)],
        render_kw={'placeholder': 'Ex: Aprovação de Contratos, Revisão de Documentos...'}
    )
    descricao = TextAreaField(
        'Descrição',
        validators=[Optional(), Length(max=500)],
        render_kw={'placeholder': 'Descrição do processo de aprovação', 'rows': 3}
    )
    ativo = BooleanField(
        'Ativo',
        default=True
    )
    
    # Hidden field to store stages JSON
    stages_json = HiddenField('Stages JSON')
    
    def __init__(self, workflow_id=None, *args, **kwargs):
        """Initialize form"""
        super(WorkflowForm, self).__init__(*args, **kwargs)
        self.workflow_id = workflow_id
    
    def validate_nome(self, field):
        """Validate workflow name uniqueness"""
        workflow_repo = WorkflowRepository()
        existing = workflow_repo.get_by_name(field.data)
        
        if existing and (not self.workflow_id or existing.id != self.workflow_id):
            raise ValidationError('Já existe um workflow com este nome')


class ApprovalActionForm(FlaskForm):
    """Form for approving/rejecting documents"""
    comentario = TextAreaField(
        'Comentário',
        validators=[DataRequired('Comentário é obrigatório'), Length(max=1000)],
        render_kw={'placeholder': 'Adicione seus comentários sobre a decisão...', 'rows': 4}
    )
    acao = HiddenField('Ação', validators=[DataRequired()])
