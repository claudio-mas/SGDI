"""Initial schema with all tables

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create perfis table
    op.create_table('perfis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=50), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nome')
    )
    
    # Create usuarios table
    op.create_table('usuarios',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=120), nullable=False),
        sa.Column('senha_hash', sa.String(length=255), nullable=False),
        sa.Column('perfil_id', sa.Integer(), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=False),
        sa.Column('tentativas_login', sa.Integer(), nullable=False),
        sa.Column('bloqueado_ate', sa.DateTime(), nullable=True),
        sa.Column('ultimo_acesso', sa.DateTime(), nullable=True),
        sa.Column('data_cadastro', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['perfil_id'], ['perfis.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_usuarios_email'), 'usuarios', ['email'], unique=True)
    
    # Create password_resets table
    op.create_table('password_resets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=100), nullable=False),
        sa.Column('expiracao', sa.DateTime(), nullable=False),
        sa.Column('usado', sa.Boolean(), nullable=False),
        sa.Column('data_criacao', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_password_resets_token'), 'password_resets', ['token'], unique=True)
    
    # Create categorias table
    op.create_table('categorias',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('categoria_pai_id', sa.Integer(), nullable=True),
        sa.Column('icone', sa.String(length=50), nullable=True),
        sa.Column('cor', sa.String(length=7), nullable=True),
        sa.Column('ordem', sa.Integer(), nullable=True),
        sa.Column('ativo', sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(['categoria_pai_id'], ['categorias.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nome')
    )
    
    # Create pastas table
    op.create_table('pastas',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('pasta_pai_id', sa.Integer(), nullable=True),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('cor', sa.String(length=7), nullable=True),
        sa.Column('ordem', sa.Integer(), nullable=True),
        sa.Column('data_criacao', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['pasta_pai_id'], ['pastas.id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create tags table
    op.create_table('tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=50), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nome')
    )
    
    # Create workflows table
    op.create_table('workflows',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=100), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('configuracao_json', sa.Text(), nullable=False),
        sa.Column('ativo', sa.Boolean(), nullable=False),
        sa.Column('data_criacao', sa.DateTime(), nullable=False),
        sa.Column('criado_por', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['criado_por'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nome')
    )
    
    # Create documentos table
    op.create_table('documentos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('caminho_arquivo', sa.String(length=500), nullable=False),
        sa.Column('nome_arquivo_original', sa.String(length=255), nullable=False),
        sa.Column('tamanho_bytes', sa.BigInteger(), nullable=False),
        sa.Column('tipo_mime', sa.String(length=100), nullable=False),
        sa.Column('hash_arquivo', sa.String(length=64), nullable=False),
        sa.Column('categoria_id', sa.Integer(), nullable=True),
        sa.Column('pasta_id', sa.Integer(), nullable=True),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('versao_atual', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('criptografado', sa.Boolean(), nullable=False),
        sa.Column('data_upload', sa.DateTime(), nullable=False),
        sa.Column('data_modificacao', sa.DateTime(), nullable=True),
        sa.Column('data_exclusao', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['categoria_id'], ['categorias.id'], ),
        sa.ForeignKeyConstraint(['pasta_id'], ['pastas.id'], ),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_documentos_hash_arquivo'), 'documentos', ['hash_arquivo'], unique=False)
    op.create_index(op.f('ix_documentos_usuario_id'), 'documentos', ['usuario_id'], unique=False)
    op.create_index(op.f('ix_documentos_status'), 'documentos', ['status'], unique=False)
    op.create_index(op.f('ix_documentos_data_upload'), 'documentos', ['data_upload'], unique=False)
    
    # Create documento_tags table
    op.create_table('documento_tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('documento_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.Column('data_associacao', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['documento_id'], ['documentos.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('documento_id', 'tag_id', name='uq_documento_tag')
    )
    
    # Create versoes table
    op.create_table('versoes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('documento_id', sa.Integer(), nullable=False),
        sa.Column('numero_versao', sa.Integer(), nullable=False),
        sa.Column('caminho_arquivo', sa.String(length=500), nullable=False),
        sa.Column('tamanho_bytes', sa.BigInteger(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('comentario', sa.Text(), nullable=False),
        sa.Column('data_criacao', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['documento_id'], ['documentos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('documento_id', 'numero_versao', name='uq_documento_versao')
    )
    op.create_index(op.f('ix_versoes_documento_id'), 'versoes', ['documento_id'], unique=False)
    op.create_index(op.f('ix_versoes_data_criacao'), 'versoes', ['data_criacao'], unique=False)
    
    # Create permissoes table
    op.create_table('permissoes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('documento_id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('tipo_permissao', sa.String(length=20), nullable=False),
        sa.Column('data_concessao', sa.DateTime(), nullable=False),
        sa.Column('concedido_por', sa.Integer(), nullable=False),
        sa.Column('data_expiracao', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['concedido_por'], ['usuarios.id'], ),
        sa.ForeignKeyConstraint(['documento_id'], ['documentos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('documento_id', 'usuario_id', 'tipo_permissao', name='uq_documento_usuario_permissao')
    )
    op.create_index(op.f('ix_permissoes_documento_id'), 'permissoes', ['documento_id'], unique=False)
    op.create_index(op.f('ix_permissoes_usuario_id'), 'permissoes', ['usuario_id'], unique=False)
    op.create_index('idx_permissao_documento_usuario', 'permissoes', ['documento_id', 'usuario_id'], unique=False)
    
    # Create aprovacao_documentos table
    op.create_table('aprovacao_documentos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('documento_id', sa.Integer(), nullable=False),
        sa.Column('workflow_id', sa.Integer(), nullable=False),
        sa.Column('submetido_por', sa.Integer(), nullable=False),
        sa.Column('estagio_atual', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('data_submissao', sa.DateTime(), nullable=False),
        sa.Column('data_conclusao', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['documento_id'], ['documentos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['submetido_por'], ['usuarios.id'], ),
        sa.ForeignKeyConstraint(['workflow_id'], ['workflows.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_aprovacao_documentos_documento_id'), 'aprovacao_documentos', ['documento_id'], unique=False)
    
    # Create historico_aprovacoes table
    op.create_table('historico_aprovacoes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('aprovacao_id', sa.Integer(), nullable=False),
        sa.Column('estagio', sa.Integer(), nullable=False),
        sa.Column('aprovador_id', sa.Integer(), nullable=False),
        sa.Column('acao', sa.String(length=20), nullable=False),
        sa.Column('comentario', sa.Text(), nullable=False),
        sa.Column('data_acao', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['aprovacao_id'], ['aprovacao_documentos.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['aprovador_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_historico_aprovacoes_aprovacao_id'), 'historico_aprovacoes', ['aprovacao_id'], unique=False)
    
    # Create log_auditoria table
    op.create_table('log_auditoria',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=True),
        sa.Column('acao', sa.String(length=50), nullable=False),
        sa.Column('tabela', sa.String(length=50), nullable=True),
        sa.Column('registro_id', sa.Integer(), nullable=True),
        sa.Column('dados_json', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.String(length=255), nullable=True),
        sa.Column('data_hora', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_log_auditoria_usuario_id'), 'log_auditoria', ['usuario_id'], unique=False)
    op.create_index(op.f('ix_log_auditoria_acao'), 'log_auditoria', ['acao'], unique=False)
    op.create_index(op.f('ix_log_auditoria_tabela'), 'log_auditoria', ['tabela'], unique=False)
    op.create_index(op.f('ix_log_auditoria_registro_id'), 'log_auditoria', ['registro_id'], unique=False)
    op.create_index(op.f('ix_log_auditoria_data_hora'), 'log_auditoria', ['data_hora'], unique=False)
    op.create_index('idx_audit_usuario_data', 'log_auditoria', ['usuario_id', 'data_hora'], unique=False)
    op.create_index('idx_audit_tabela_registro', 'log_auditoria', ['tabela', 'registro_id'], unique=False)


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table('log_auditoria')
    op.drop_table('historico_aprovacoes')
    op.drop_table('aprovacao_documentos')
    op.drop_table('permissoes')
    op.drop_table('versoes')
    op.drop_table('documento_tags')
    op.drop_table('documentos')
    op.drop_table('workflows')
    op.drop_table('tags')
    op.drop_table('pastas')
    op.drop_table('categorias')
    op.drop_table('password_resets')
    op.drop_table('usuarios')
    op.drop_table('perfis')
