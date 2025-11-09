"""
Search forms for document search functionality
"""
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, DateField, IntegerField, HiddenField
from wtforms.validators import Optional, Length, NumberRange


class SimpleSearchForm(FlaskForm):
    """Form for simple search"""
    q = StringField(
        'Buscar',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'Nome, descrição ou tags...', 'class': 'form-control'}
    )


class AdvancedSearchForm(FlaskForm):
    """Form for advanced search with multiple filters"""
    nome = StringField(
        'Nome do Documento',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'Nome do documento', 'class': 'form-control'}
    )
    descricao = StringField(
        'Descrição',
        validators=[Optional(), Length(max=500)],
        render_kw={'placeholder': 'Descrição do documento', 'class': 'form-control'}
    )
    categoria_id = SelectField(
        'Categoria',
        coerce=int,
        validators=[Optional()],
        render_kw={'class': 'form-select'}
    )
    tags = StringField(
        'Tags',
        validators=[Optional(), Length(max=255)],
        render_kw={'placeholder': 'Separe as tags com vírgulas', 'class': 'form-control'}
    )
    autor_id = SelectField(
        'Autor',
        coerce=int,
        validators=[Optional()],
        render_kw={'class': 'form-select'}
    )
    tipo_mime = SelectField(
        'Tipo de Arquivo',
        validators=[Optional()],
        render_kw={'class': 'form-select'},
        choices=[
            ('', 'Todos os tipos'),
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
    data_inicio = DateField(
        'Data Inicial',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'type': 'date'}
    )
    data_fim = DateField(
        'Data Final',
        validators=[Optional()],
        render_kw={'class': 'form-control', 'type': 'date'}
    )
    tamanho_min = IntegerField(
        'Tamanho Mínimo (bytes)',
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'class': 'form-control', 'placeholder': 'Ex: 1024'}
    )
    tamanho_max = IntegerField(
        'Tamanho Máximo (bytes)',
        validators=[Optional(), NumberRange(min=0)],
        render_kw={'class': 'form-control', 'placeholder': 'Ex: 10485760'}
    )
    sort_by = SelectField(
        'Ordenar por',
        validators=[Optional()],
        render_kw={'class': 'form-select'},
        choices=[
            ('data_upload_desc', 'Data de Upload (Mais Recente)'),
            ('data_upload_asc', 'Data de Upload (Mais Antigo)'),
            ('nome_asc', 'Nome (A-Z)'),
            ('nome_desc', 'Nome (Z-A)'),
            ('tamanho_desc', 'Tamanho (Maior)'),
            ('tamanho_asc', 'Tamanho (Menor)')
        ],
        default='data_upload_desc'
    )
