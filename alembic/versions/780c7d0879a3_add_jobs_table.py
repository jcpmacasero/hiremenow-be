"""add jobs table

Revision ID: 780c7d0879a3
Revises: b657303bffaf
Create Date: 2026-01-29 13:07:58.440236

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '780c7d0879a3'
down_revision: Union[str, Sequence[str], None] = 'b657303bffaf'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create enums
    workmode = postgresql.ENUM('onsite', 'accommodation_provided', name='workmode', create_type=False)
    workmode.create(op.get_bind(), checkfirst=True)

    jobtype = postgresql.ENUM('full_time', 'part_time', 'contract', 'seasonal', name='jobtype', create_type=False)
    jobtype.create(op.get_bind(), checkfirst=True)

    jobstatus = postgresql.ENUM('draft', 'pending_approval', 'active', 'paused', 'closed', 'rejected', name='jobstatus', create_type=False)
    jobstatus.create(op.get_bind(), checkfirst=True)

    salaryperiod = postgresql.ENUM('hourly', 'monthly', name='salaryperiod', create_type=False)
    salaryperiod.create(op.get_bind(), checkfirst=True)

    # Create jobs table
    op.create_table(
        'jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('category', sa.String(length=100), nullable=True),
        sa.Column('country', sa.String(length=100), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=True),
        sa.Column('work_mode', sa.Enum('onsite', 'accommodation_provided', name='workmode'), nullable=False, server_default='onsite'),
        sa.Column('job_type', sa.Enum('full_time', 'part_time', 'contract', 'seasonal', name='jobtype'), nullable=False, server_default='full_time'),
        sa.Column('salary_min', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('salary_max', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('salary_currency', sa.String(length=3), nullable=False, server_default='EUR'),
        sa.Column('salary_period', sa.Enum('hourly', 'monthly', name='salaryperiod'), nullable=False, server_default='monthly'),
        sa.Column('benefits', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='[]'),
        sa.Column('requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),
        sa.Column('total_slots', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('filled_slots', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.Enum('draft', 'pending_approval', 'active', 'paused', 'closed', 'rejected', name='jobstatus'), nullable=False, server_default='draft'),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('deadline', sa.Date(), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('published_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='SET NULL')
    )
    op.create_index(op.f('ix_jobs_slug'), 'jobs', ['slug'], unique=True)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_jobs_slug'), table_name='jobs')
    op.drop_table('jobs')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS workmode')
    op.execute('DROP TYPE IF EXISTS jobtype')
    op.execute('DROP TYPE IF EXISTS jobstatus')
    op.execute('DROP TYPE IF EXISTS salaryperiod')
