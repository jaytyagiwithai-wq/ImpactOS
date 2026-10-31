"""add chunk embeddings

Revision ID: e5ea7a723b3b
Revises: 2542134fbe98
Create Date: 2026-10-30 18:42:02.274163

"""
from typing import Sequence, Union

from alembic import op
from pgvector.sqlalchemy import VECTOR
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5ea7a723b3b'
down_revision: Union[str, Sequence[str], None] = '2542134fbe98'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Extensions are database-level PostgreSQL objects, so Alembic cannot
    # discover them from SQLAlchemy model metadata.
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.add_column(
        "chunks",
        sa.Column("embedding", VECTOR(1536), nullable=True),
    )
    op.add_column(
        "chunks",
        sa.Column("embedding_model", sa.String(length=64), nullable=True),
    )
    op.create_check_constraint(
        "ck_chunks_embedding_pair",
        "chunks",
        "(embedding IS NULL AND embedding_model IS NULL) OR "
        "(embedding IS NOT NULL AND embedding_model IS NOT NULL)",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("ck_chunks_embedding_pair", "chunks", type_="check")
    op.drop_column("chunks", "embedding_model")
    op.drop_column("chunks", "embedding")
    # Do not drop the vector extension: it is shared database infrastructure
    # and could be used by another table or migration.
