"""add agent files

Revision ID: c3d9e1a4f7b8
Revises: a1f0c7d3e5b2
Create Date: 2026-09-25

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c3d9e1a4f7b8"
down_revision = "a1f0c7d3e5b2"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agent_files",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column(
            "conversation_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("agent_conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("media_type", sa.String(length=100), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("size", sa.Integer(), nullable=False),
        sa.Column("content", sa.LargeBinary(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_agent_files_id"), "agent_files", ["id"], unique=False)
    op.create_index(
        op.f("ix_agent_files_conversation_id"),
        "agent_files",
        ["conversation_id"],
        unique=False,
    )


def downgrade():
    op.drop_index(op.f("ix_agent_files_conversation_id"), table_name="agent_files")
    op.drop_index(op.f("ix_agent_files_id"), table_name="agent_files")
    op.drop_table("agent_files")
