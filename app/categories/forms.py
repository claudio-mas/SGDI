"""
Category and folder management forms
"""
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, HiddenField, IntegerField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models.document import Categoria, Pasta
from app.repositories.category_repository import CategoryRepository, FolderRepository


class CategoryForm(FlaskForm):
    """Form for creating/editing categories"""
    nome = StringField(
        'Nome da Categoria',
        validators=[DataRequired('Nome é obrigatório'), Length(max=100)],
        render_kw={'placeholder': 'Ex: Contratos, Faturas, RH...'}
    )
    descricao = TextAreaField(
        'Descrição',
        validators=[Optional(), Length(max=500)],
        render_kw={'placeholder': 'Descrição opcional da categoria'}
    )
    categoria_pai_id = SelectField(
        'Categoria Pai',
        coerce=int,
        validators=[Optional()],
        choices=[]
    )
    icone = StringField(
        'Ícone',
        validators=[Optional(), Length(max=50)],
        render_kw={'placeholder': 'Ex: fa-folder, fa-file-contract'}
    )
    cor = StringField(
        'Cor',
        validators=[Optional(), Length(max=7)],
        render_kw={'type': 'color', 'value': '#007bff'}
    )
    ordem = IntegerField(
        'Ordem',
        validators=[Optional()],
        default=0
    )
    
    def __init__(self, categoria_id=None, *args, **kwargs):
        """Initialize form with category choices"""
        super(CategoryForm, self).__init__(*args, **kwargs)
        self.categoria_id = categoria_id
        
        # Populate parent category choices
        category_repo = CategoryRepository()
        categories = category_repo.get_active_categories()
        
        # Build choices excluding current category and its descendants
        choices = [('', 'Nenhuma (Raiz)')]
        for cat in categories:
            # Skip current category and its descendants to prevent circular references
            if categoria_id:
                if cat.id == categoria_id:
                    continue
                if not category_repo.can_move_to_parent(categoria_id, cat.id):
                    continue
            
            # Add indentation based on depth
            depth = category_repo.get_depth(cat.id)
            indent = '—' * depth
            label = f"{indent} {cat.nome}" if depth > 0 else cat.nome
            choices.append((cat.id, label))
        
        self.categoria_pai_id.choices = choices
    
    def validate_nome(self, field):
        """Validate category name uniqueness"""
        category_repo = CategoryRepository()
        existing = category_repo.get_by_name(field.data)
        
        if existing and (not self.categoria_id or existing.id != self.categoria_id):
            raise ValidationError('Já existe uma categoria com este nome')


class FolderForm(FlaskForm):
    """Form for creating/editing folders"""
    nome = StringField(
        'Nome da Pasta',
        validators=[DataRequired('Nome é obrigatório'), Length(max=100)],
        render_kw={'placeholder': 'Ex: Projetos 2024, Documentos Pessoais...'}
    )
    descricao = TextAreaField(
        'Descrição',
        validators=[Optional(), Length(max=500)],
        render_kw={'placeholder': 'Descrição opcional da pasta'}
    )
    pasta_pai_id = SelectField(
        'Pasta Pai',
        coerce=int,
        validators=[Optional()],
        choices=[]
    )
    cor = StringField(
        'Cor',
        validators=[Optional(), Length(max=7)],
        render_kw={'type': 'color', 'value': '#ffc107'}
    )
    ordem = IntegerField(
        'Ordem',
        validators=[Optional()],
        default=0
    )
    
    def __init__(self, usuario_id, pasta_id=None, *args, **kwargs):
        """Initialize form with folder choices for user"""
        super(FolderForm, self).__init__(*args, **kwargs)
        self.usuario_id = usuario_id
        self.pasta_id = pasta_id
        
        # Populate parent folder choices
        folder_repo = FolderRepository()
        folders = folder_repo.get_user_folders(usuario_id)
        
        # Build choices excluding current folder and checking depth
        choices = [('', 'Nenhuma (Raiz)')]
        for folder in folders:
            # Skip current folder
            if pasta_id and folder.id == pasta_id:
                continue
            
            # Check if can move to this parent (depth limit and circular reference)
            if pasta_id and not folder_repo.can_move_to_parent(pasta_id, folder.id):
                continue
            
            # Add indentation based on depth
            indent = '—' * folder.nivel
            label = f"{indent} {folder.nome}" if folder.nivel > 0 else folder.nome
            choices.append((folder.id, label))
        
        self.pasta_pai_id.choices = choices
    
    def validate_pasta_pai_id(self, field):
        """Validate folder depth limit"""
        if field.data:
            folder_repo = FolderRepository()
            parent = folder_repo.get_by_id(field.data)
            if parent and parent.nivel >= 4:  # Max depth is 5 (0-4)
                raise ValidationError('Limite de profundidade atingido (máximo 5 níveis)')
