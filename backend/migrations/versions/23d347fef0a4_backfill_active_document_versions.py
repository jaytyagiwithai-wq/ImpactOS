"""backfill active document versions

Revision ID: 23d347fef0a4
Revises: 698530042a8d
Create Date: 2026-10-31 08:44:39.982214

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '23d347fef0a4'
down_revision: Union[str, Sequence[str], None] = '698530042a8d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE documents AS d
        SET active_version_id = (
            SELECT dv.id
            FROM document_versions AS dv
            WHERE dv.document_id = d.id
              AND dv.status = 'ready'
            ORDER BY dv.version_number DESC
            LIMIT 1
        )
        WHERE d.active_version_id IS NULL
          AND EXISTS (
              SELECT 1
              FROM document_versions AS dv
              WHERE dv.document_id = d.id
                AND dv.status = 'ready'
          )
        """
    )


def downgrade() -> None:
    """Downgrade schema."""
    pass
