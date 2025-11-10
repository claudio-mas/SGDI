"""Add permission flags to perfis table

Revision ID: 002
Revises: 001
Create Date: 2025-11-09 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add boolean permission columns to perfis
    op.add_column('perfis', sa.Column('pode_criar_documentos', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('perfis', sa.Column('pode_editar_proprios', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('perfis', sa.Column('pode_excluir_proprios', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('perfis', sa.Column('pode_visualizar_todos', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('perfis', sa.Column('pode_editar_todos', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('perfis', sa.Column('pode_excluir_todos', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('perfis', sa.Column('pode_gerenciar_usuarios', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('perfis', sa.Column('pode_gerenciar_categorias', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('perfis', sa.Column('pode_gerenciar_workflows', sa.Boolean(), nullable=False, server_default=sa.text('0')))
    op.add_column('perfis', sa.Column('pode_visualizar_auditoria', sa.Boolean(), nullable=False, server_default=sa.text('0')))

    # Remove server_default after population (optional)
    with op.get_context().autocommit_block():
        pass


def downgrade() -> None:
    op.drop_column('perfis', 'pode_visualizar_auditoria')
    op.drop_column('perfis', 'pode_gerenciar_workflows')
    op.drop_column('perfis', 'pode_gerenciar_categorias')
    op.drop_column('perfis', 'pode_gerenciar_usuarios')
    op.drop_column('perfis', 'pode_excluir_todos')
    op.drop_column('perfis', 'pode_editar_todos')
    op.drop_column('perfis', 'pode_visualizar_todos')
    op.drop_column('perfis', 'pode_excluir_proprios')
    op.drop_column('perfis', 'pode_editar_proprios')
    op.drop_column('perfis', 'pode_criar_documentos')
