"""
Document management forms
"""
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, TextAreaField, SelectField, SelectMultipleField, HiddenField
from wtforms.validators import DataRequired, Length, Optional


class DocumentUploadForm(FlaskForm):
    """Form for uploading documents"""
    files = FileField(
        'Arquivos',
        validators=[
            FileRequired('Por favor, selecione pelo menos um arquivo'),
            FileAllowed(
                ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'tif', 'tiff'],
                'Tipo de arquivo não permitido'
            )
        ]
    )
    nome = StringField(
        'Nome do Documento',
        validators=[Optional(), Length(max=255)]
    )
    descricao = TextAreaField(
        'Descrição',
        validators=[Optional(), Length(max=1000)]
    )
    categoria_id = SelectField(
        'Categoria',
        coerce=int,
        validators=[Optional()]
    )
    pasta_id = SelectField(
        'Pasta',
        coerce=int,
        validators=[Optional()]
    )
    tags = StringField(
        'Tags',
        validators=[Optional()],
        render_kw={'placeholder': 'Separe as tags com vírgulas'}
    )


class DocumentEditForm(FlaskForm):
    """Form for editing document metadata"""
    nome = StringField(
        'Nome do Documento',
        validators=[DataRequired('Nome é obrigatório'), Length(max=255)]
    )
    descricao = TextAreaField(
        'Descrição',
        validators=[Optional(), Length(max=1000)]
    )
    categoria_id = SelectField(
        'Categoria',
        coerce=int,
        validators=[Optional()]
    )
    pasta_id = SelectField(
        'Pasta',
        coerce=int,
        validators=[Optional()]
    )
    tags = StringField(
        'Tags',
        validators=[Optional()],
        render_kw={'placeholder': 'Separe as tags com vírgulas'}
    )


class DocumentVersionForm(FlaskForm):
    """Form for uploading a new version"""
    file = FileField(
        'Nova Versão',
        validators=[
            FileRequired('Por favor, selecione um arquivo'),
            FileAllowed(
                ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'jpeg', 'png', 'tif', 'tiff'],
                'Tipo de arquivo não permitido'
            )
        ]
    )
    comentario = TextAreaField(
        'Comentário',
        validators=[DataRequired('Comentário é obrigatório'), Length(max=500)],
        render_kw={'placeholder': 'Descreva as mudanças nesta versão'}
    )


class DocumentSearchForm(FlaskForm):
    """Form for searching documents"""
    query = StringField(
        'Buscar',
        validators=[Optional()],
        render_kw={'placeholder': 'Nome, descrição ou tags...'}
    )
    categoria_id = SelectField(
        'Categoria',
        coerce=int,
        validators=[Optional()]
    )
    tipo_mime = SelectField(
        'Tipo de Arquivo',
        validators=[Optional()],
        choices=[
            ('', 'Todos'),
            ('application/pdf', 'PDF'),
            ('application/msword', 'Word (DOC)'),
            ('application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'Word (DOCX)'),
            ('application/vnd.ms-excel', 'Excel (XLS)'),
            ('application/vnd.openxmlformats-officedocument.spreadsheetml.sheet', 'Excel (XLSX)'),
            ('image/jpeg', 'JPEG'),
            ('image/png', 'PNG'),
            ('image/tiff', 'TIFF')
        ]
    )
