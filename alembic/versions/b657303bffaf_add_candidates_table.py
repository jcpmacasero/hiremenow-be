"""add candidates table

Revision ID: b657303bffaf
Revises: 8a86bbd0adb7
Create Date: 2026-01-29 13:06:08.915317

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b657303bffaf'
down_revision: Union[str, Sequence[str], None] = '8a86bbd0adb7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enums using raw SQL
    op.execute("CREATE TYPE passportstatus AS ENUM ('valid', 'expired', 'none', 'in_progress')")
    op.execute("CREATE TYPE leadsource AS ENUM ('website', 'facebook', 'instagram', 'referral', 'other')")

    # Create candidates table
    op.create_table(
        'candidates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('first_name', sa.String(length=100), nullable=True),
        sa.Column('last_name', sa.String(length=100), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('date_of_birth', sa.Date(), nullable=True),
        sa.Column('nationality', sa.String(length=100), nullable=True),
        sa.Column('current_country', sa.String(length=100), nullable=True),
        sa.Column('passport_status', postgresql.ENUM('valid', 'expired', 'none', 'in_progress', name='passportstatus', create_type=False), nullable=False, server_default='none'),
        sa.Column('passport_expiry', sa.Date(), nullable=True),
        sa.Column('preferred_positions', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('experience_years', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('photo_url', sa.String(length=500), nullable=True),
        sa.Column('resume_url', sa.String(length=500), nullable=True),
        sa.Column('source', postgresql.ENUM('website', 'facebook', 'instagram', 'referral', 'other', name='leadsource', create_type=False), nullable=False, server_default='website'),
        sa.Column('referral_code', sa.String(length=50), nullable=True),
        sa.Column('current_stage', sa.String(length=50), nullable=False, server_default='lead'),
        sa.Column('stage_notes', sa.Text(), nullable=True),
        sa.Column('stage_updated_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('candidates')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS passportstatus')
    op.execute('DROP TYPE IF EXISTS leadsource')
