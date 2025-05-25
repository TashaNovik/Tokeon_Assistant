"""drop answer & question

Revision ID: afca8294b85b
Revises: cde96f6032a0
Create Date: 2025-05-25 15:39:18.552013
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# ——————————————————————————————————————————————————————————————
revision: str = "afca8294b85b"
down_revision: Union[str, None] = "cde96f6032a0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None
# ——————————————————————————————————————————————————————————————


def upgrade() -> None:
    # 1) Create "messages" table
    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("role", sa.String(length=16), nullable=False),  # 'user' / 'assistant'
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )
    op.create_index("ix_messages_id", "messages", ["id"])

    # 2) Add "message_id" column to ratings (nullable for migration safety)
    op.add_column("ratings", sa.Column("message_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        None, "ratings", "messages", ["message_id"], ["id"], ondelete="CASCADE"
    )

    # 3) Remove FK and column "answer_id" from ratings
    op.drop_constraint("ratings_answer_id_fkey", "ratings", type_="foreignkey")
    op.drop_column("ratings", "answer_id")

    # 4) Drop old "answers" and "questions" tables
    op.drop_table("answers")
    op.drop_table("questions")


def downgrade() -> None:
    # Simplified downgrade (does not restore lost data)

    # Re-create "answers" table
    op.create_table(
        "answers",
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Re-create "questions" table
    op.create_table(
        "questions",
        sa.Column(
            "session_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("sessions.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "timestamp",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
    )

    # Add "answer_id" column back to ratings
    op.add_column("ratings", sa.Column("answer_id", postgresql.UUID(as_uuid=True)))
    op.create_foreign_key(
        "ratings_answer_id_fkey",
        "ratings",
        "answers",
        ["answer_id"],
        ["session_id"],
        ondelete="CASCADE",
    )

    # Remove "message_id" column from ratings
    op.drop_constraint(None, "ratings", type_="foreignkey")
    op.drop_column("ratings", "message_id")

    # Drop "messages" table
    op.drop_index("ix_messages_id", table_name="messages")
    op.drop_table("messages")
