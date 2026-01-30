"""add job_matches table

Revision ID: c1a2b3c4d5e6
Revises: 780c7d0879a3
Create Date: 2026-01-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "c1a2b3c4d5e6"
down_revision: Union[str, Sequence[str], None] = "780c7d0879a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE matchstatus AS ENUM "
        "('suggested', 'candidate_interested', 'admin_approved', 'confirmed', 'rejected')"
    )
    op.create_table(
        "job_matches",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("candidate_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("match_reasons", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="[]"),
        sa.Column(
            "status",
            postgresql.ENUM(
                "suggested", "candidate_interested", "admin_approved", "confirmed", "rejected",
                name="matchstatus", create_type=False,
            ),
            nullable=False,
            server_default="suggested",
        ),
        sa.Column("suggested_at", sa.DateTime(), nullable=False),
        sa.Column("confirmed_at", sa.DateTime(), nullable=True),
        sa.Column("rejected_reason", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["candidate_id"], ["candidates.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_job_matches_candidate_id", "job_matches", ["candidate_id"], unique=False)
    op.create_index("ix_job_matches_job_id", "job_matches", ["job_id"], unique=False)
    op.create_unique_constraint(
        "uq_job_matches_candidate_job", "job_matches", ["candidate_id", "job_id"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_job_matches_candidate_job", "job_matches", type_="unique")
    op.drop_index("ix_job_matches_job_id", table_name="job_matches")
    op.drop_index("ix_job_matches_candidate_id", table_name="job_matches")
    op.drop_table("job_matches")
    op.execute("DROP TYPE IF EXISTS matchstatus")
