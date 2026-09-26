"""add agent conversations

Revision ID: a1f0c7d3e5b2
Revises: e0c02eaf8190
Create Date: 2026-09-25

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1f0c7d3e5b2"
down_revision = "e0c02eaf8190"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agent_conversations",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("user_key", sa.String(length=320), nullable=False),
        sa.Column("title", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        op.f("ix_agent_conversations_id"), "agent_conversations", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_agent_conversations_user_key"),
        "agent_conversations",
        ["user_key"],
        unique=False,
    )

    op.create_table(
        "agent_messages",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "conversation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("agent_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("position", sa.Integer(), nullable=False),
        sa.Column("message", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(
        op.f("ix_agent_messages_id"), "agent_messages", ["id"], unique=False
    )
    op.create_index(
        op.f("ix_agent_messages_conversation_id"),
        "agent_messages",
        ["conversation_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(
        op.f("ix_agent_messages_conversation_id"), table_name="agent_messages"
    )
    op.drop_index(op.f("ix_agent_messages_id"), table_name="agent_messages")
    op.drop_table("agent_messages")

    op.drop_index(
        op.f("ix_agent_conversations_user_key"), table_name="agent_conversations"
    )
    op.drop_index(op.f("ix_agent_conversations_id"), table_name="agent_conversations")
    op.drop_table("agent_conversations")
