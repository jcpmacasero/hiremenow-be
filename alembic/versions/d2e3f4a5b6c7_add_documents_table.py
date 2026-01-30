"""add documents table

Revision ID: d2e3f4a5b6c7
Revises: c1a2b3c4d5e6
Create Date: 2026-01-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d2e3f4a5b6c7"
down_revision: Union[str, Sequence[str], None] = "c1a2b3c4d5e6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE documenttype AS ENUM "
        "('passport', 'resume', 'photo', 'certificate', 'agreement', 'other')"
    )
    op.execute(
        "CREATE TYPE documentstatus AS ENUM ('pending_review', 'approved', 'rejected')"
    )
    op.create_table(
        "documents",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM(
                "passport", "resume", "photo", "certificate", "agreement", "other",
                name="documenttype", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("file_url", sa.String(length=500), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=True),
        sa.Column("mime_type", sa.String(length=100), nullable=True),
        sa.Column(
            "status",
            postgresql.ENUM("pending_review", "approved", "rejected", name="documentstatus", create_type=False),
            nullable=False,
            server_default="pending_review",
        ),
        sa.Column("reviewed_by", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("rejection_reason", sa.Text(), nullable=True),
        sa.Column("expires_at", sa.DateTime(), nullable=True),
        sa.Column("uploaded_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["reviewed_by"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_documents_candidate_id", "documents", ["candidate_id"], unique=False)
    op.create_index("ix_documents_status", "documents", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_documents_status", table_name="documents")
    op.drop_index("ix_documents_candidate_id", table_name="documents")
    op.drop_table("documents")
    op.execute("DROP TYPE IF EXISTS documentstatus")
    op.execute("DROP TYPE IF EXISTS documenttype")
