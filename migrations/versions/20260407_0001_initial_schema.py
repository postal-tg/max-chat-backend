"""Initial schema for MAX chat bot.

Revision ID: 20260407_0001
Revises:
Create Date: 2026-04-07 12:00:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260407_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("max_user_id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=255), nullable=True),
        sa.Column("first_name", sa.String(length=255), nullable=True),
        sa.Column("last_name", sa.String(length=255), nullable=True),
        sa.Column("is_bot", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("locale", sa.String(length=32), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("total_requests", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("max_user_id", name="uq_users_max_user_id"),
    )
    op.create_index("ix_users_max_user_id", "users", ["max_user_id"], unique=False)

    op.create_table(
        "conversations",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("conversation_type", sa.String(length=32), nullable=False),
        sa.Column("max_chat_id", sa.BigInteger(), nullable=True),
        sa.Column("max_user_id", sa.BigInteger(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("start_payload", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_conversations_user_id", "conversations", ["user_id"], unique=False)
    op.create_index("ix_conversations_max_chat_id", "conversations", ["max_chat_id"], unique=False)
    op.create_index("ix_conversations_max_user_id", "conversations", ["max_user_id"], unique=False)
    op.create_index("ix_conversations_is_active", "conversations", ["is_active"], unique=False)

    op.create_table(
        "messages",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("source_message_timestamp", sa.BigInteger(), nullable=True),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("raw_text", sa.Text(), nullable=False),
        sa.Column("normalized_text", sa.Text(), nullable=False),
        sa.Column("prompt_hash", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("validation_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_messages_user_id", "messages", ["user_id"], unique=False)
    op.create_index("ix_messages_conversation_id", "messages", ["conversation_id"], unique=False)
    op.create_index("ix_messages_role", "messages", ["role"], unique=False)
    op.create_index("ix_messages_prompt_hash", "messages", ["prompt_hash"], unique=False)
    op.create_index("ix_messages_status", "messages", ["status"], unique=False)

    op.create_table(
        "llm_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("conversation_id", sa.Integer(), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("user_message_id", sa.Integer(), sa.ForeignKey("messages.id"), nullable=False),
        sa.Column("assistant_message_id", sa.Integer(), sa.ForeignKey("messages.id"), nullable=True),
        sa.Column("provider_name", sa.String(length=64), nullable=False),
        sa.Column("provider_model", sa.String(length=128), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("prompt_tokens", sa.Integer(), nullable=True),
        sa.Column("completion_tokens", sa.Integer(), nullable=True),
        sa.Column("total_tokens", sa.Integer(), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("request_payload", sa.JSON(), nullable=True),
        sa.Column("response_payload", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_llm_requests_conversation_id", "llm_requests", ["conversation_id"], unique=False)
    op.create_index("ix_llm_requests_user_message_id", "llm_requests", ["user_message_id"], unique=False)
    op.create_index("ix_llm_requests_assistant_message_id", "llm_requests", ["assistant_message_id"], unique=False)
    op.create_index("ix_llm_requests_status", "llm_requests", ["status"], unique=False)

    op.create_table(
        "webhook_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("external_id", sa.String(length=255), nullable=False),
        sa.Column("update_type", sa.String(length=64), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("external_id", name="uq_webhook_events_external_id"),
    )
    op.create_index("ix_webhook_events_external_id", "webhook_events", ["external_id"], unique=False)
    op.create_index("ix_webhook_events_update_type", "webhook_events", ["update_type"], unique=False)
    op.create_index("ix_webhook_events_status", "webhook_events", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_webhook_events_status", table_name="webhook_events")
    op.drop_index("ix_webhook_events_update_type", table_name="webhook_events")
    op.drop_index("ix_webhook_events_external_id", table_name="webhook_events")
    op.drop_table("webhook_events")

    op.drop_index("ix_llm_requests_status", table_name="llm_requests")
    op.drop_index("ix_llm_requests_assistant_message_id", table_name="llm_requests")
    op.drop_index("ix_llm_requests_user_message_id", table_name="llm_requests")
    op.drop_index("ix_llm_requests_conversation_id", table_name="llm_requests")
    op.drop_table("llm_requests")

    op.drop_index("ix_messages_status", table_name="messages")
    op.drop_index("ix_messages_prompt_hash", table_name="messages")
    op.drop_index("ix_messages_role", table_name="messages")
    op.drop_index("ix_messages_conversation_id", table_name="messages")
    op.drop_index("ix_messages_user_id", table_name="messages")
    op.drop_table("messages")

    op.drop_index("ix_conversations_is_active", table_name="conversations")
    op.drop_index("ix_conversations_max_user_id", table_name="conversations")
    op.drop_index("ix_conversations_max_chat_id", table_name="conversations")
    op.drop_index("ix_conversations_user_id", table_name="conversations")
    op.drop_table("conversations")

    op.drop_index("ix_users_max_user_id", table_name="users")
    op.drop_table("users")
