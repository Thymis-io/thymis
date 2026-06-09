"""add_log_entry_composite_indexes

Revision ID: 84112566ca43
Revises: b1c2d3e4f5a6
Create Date: 2026-06-09 13:25:09.047975

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "84112566ca43"
down_revision = "b1c2d3e4f5a6"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("log_entries", schema=None) as batch_op:
        batch_op.create_index(
            "ix_log_entries_deployment_info_id_timestamp",
            ["deployment_info_id", "timestamp"],
            unique=False,
        )
        batch_op.create_index(
            "ix_log_entries_ssh_public_key_timestamp",
            ["ssh_public_key", "timestamp"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("log_entries", schema=None) as batch_op:
        batch_op.drop_index("ix_log_entries_ssh_public_key_timestamp")
        batch_op.drop_index("ix_log_entries_deployment_info_id_timestamp")
