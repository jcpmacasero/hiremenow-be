"""add conversations, messages, notifications tables

Revision ID: e3f4a5b6c7d8
Revises: d2e3f4a5b6c7
Create Date: 2026-01-30

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, Sequence[str], None] = "d2e3f4a5b6c7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE TYPE conversationtype AS ENUM ('direct', 'support', 'group')")
    op.execute("CREATE TYPE participantrole AS ENUM ('member', 'admin')")
    op.execute("CREATE TYPE messagecontenttype AS ENUM ('text', 'file', 'image', 'system')")
    op.execute(
        "CREATE TYPE notificationtype AS ENUM "
        "('stage_changed', 'payment_received', 'test_result', 'job_match', "
        "'message_received', 'document_required', 'application_update', 'course_reminder', 'system')"
    )

    op.create_table(
        "conversations",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM("direct", "support", "group", name="conversationtype", create_type=False),
            nullable=False,
            server_default="direct",
        ),
        sa.Column("subject", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "conversation_participants",
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "role",
            postgresql.ENUM("member", "admin", name="participantrole", create_type=False),
            nullable=False,
            server_default="member",
        ),
        sa.Column("joined_at", sa.DateTime(), nullable=False),
        sa.Column("last_read_at", sa.DateTime(), nullable=True),
        sa.Column("is_muted", sa.Boolean(), nullable=False, server_default="false"),
        sa.PrimaryKeyConstraint("conversation_id", "user_id"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conversation_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("sender_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column(
            "content_type",
            postgresql.ENUM("text", "file", "image", "system", name="messagecontenttype", create_type=False),
            nullable=False,
            server_default="text",
        ),
        sa.Column("file_url", sa.String(length=500), nullable=True),
        sa.Column("is_edited", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["conversation_id"], ["conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["sender_id"], ["users.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"], unique=False)

    op.create_table(
        "message_reads",
        sa.Column("message_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("read_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("message_id", "user_id"),
        sa.ForeignKeyConstraint(["message_id"], ["messages.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )

    op.create_table(
        "notifications",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "type",
            postgresql.ENUM(
                "stage_changed", "payment_received", "test_result", "job_match",
                "message_received", "document_required", "application_update", "course_reminder", "system",
                name="notificationtype", create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("message", sa.Text(), nullable=True),
        sa.Column("data", postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default="{}"),
        sa.Column("action_url", sa.String(length=500), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"], unique=False)
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_notifications_is_read", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
    op.drop_table("message_reads")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_table("messages")
    op.drop_table("conversation_participants")
    op.drop_table("conversations")
    op.execute("DROP TYPE IF EXISTS notificationtype")
    op.execute("DROP TYPE IF EXISTS messagecontenttype")
    op.execute("DROP TYPE IF EXISTS participantrole")
    op.execute("DROP TYPE IF EXISTS conversationtype")
