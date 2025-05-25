"""ratings.message_id NOT NULL

Revision ID: 69f323a27888
Revises: afca8294b85b
Create Date: 2025-05-25 16:20:15.538234
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# ───────────────────────────────────────────────────────────────────────────
revision: str = "69f323a27888"
down_revision: Union[str, None] = "afca8294b85b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# ───────────────────────────────────────────────────────────────────────────


def upgrade() -> None:
    # Remove old ratings without a linked message
    op.execute("DELETE FROM ratings WHERE message_id IS NULL")

    # Set message_id column as NOT NULL
    op.alter_column(
        "ratings",
        "message_id",
        existing_type=sa.Integer(),
        nullable=False,
    )


def downgrade() -> None:
    # Allow NULL in message_id column (rollback)
    op.alter_column(
        "ratings",
        "message_id",
        existing_type=sa.Integer(),
        nullable=True,
    )
