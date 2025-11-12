"""Add favoritos table

Revision ID: 003
Revises: 002, add_fulltext_search
Create Date: 2025-11-11 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = ('002', 'add_fulltext_search')
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create favoritos table
    op.create_table(
        'favoritos',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('usuario_id', sa.Integer(), nullable=False),
        sa.Column('documento_id', sa.Integer(), nullable=False),
        sa.Column('data_favoritado', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ),
        sa.ForeignKeyConstraint(['documento_id'], ['documentos.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'usuario_id',
            'documento_id',
            name='uq_usuario_documento_favorito'
        )
    )
    
    # Create indexes for better query performance
    op.create_index(
        op.f('ix_favoritos_usuario_id'),
        'favoritos',
        ['usuario_id'],
        unique=False
    )
    op.create_index(
        op.f('ix_favoritos_documento_id'),
        'favoritos',
        ['documento_id'],
        unique=False
    )


def downgrade() -> None:
    # Drop indexes
    op.drop_index(op.f('ix_favoritos_documento_id'), table_name='favoritos')
    op.drop_index(op.f('ix_favoritos_usuario_id'), table_name='favoritos')
    
    # Drop favoritos table
    op.drop_table('favoritos')
