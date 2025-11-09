"""Add full-text search support

Revision ID: add_fulltext_search
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


# revision identifiers, used by Alembic.
revision = 'add_fulltext_search'
down_revision = None  # Update this to point to your latest migration
branch_label = None
depends_on = None


def upgrade():
    """
    Add conteudo_texto column and set up SQL Server Full-Text Search
    """
    # Add conteudo_texto column for storing extracted text
    op.add_column('documentos', 
        sa.Column('conteudo_texto', sa.Text(), nullable=True)
    )
    
    # Note: Full-text catalog and index creation is done via raw SQL
    # because Alembic doesn't have native support for full-text search
    
    # The actual catalog and index creation should be done by calling
    # SearchService.setup_fulltext_catalog() after migration
    # or manually via SQL Server Management Studio
    
    print("Column 'conteudo_texto' added to documentos table.")
    print("To complete full-text search setup, run:")
    print("  from app.services.search_service import SearchService")
    print("  SearchService.setup_fulltext_catalog()")


def downgrade():
    """
    Remove full-text search support
    """
    # Drop full-text index if exists
    connection = op.get_bind()
    try:
        connection.execute(text("""
            IF EXISTS (SELECT * FROM sys.fulltext_indexes WHERE object_id = OBJECT_ID('documentos'))
            DROP FULLTEXT INDEX ON documentos
        """))
    except:
        pass
    
    # Drop column
    op.drop_column('documentos', 'conteudo_texto')
