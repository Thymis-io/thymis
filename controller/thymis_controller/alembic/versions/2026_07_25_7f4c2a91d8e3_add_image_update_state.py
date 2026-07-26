"""add image update state

Revision ID: 7f4c2a91d8e3
Revises: e0c02eaf8190
Create Date: 2026-07-25 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

revision = "7f4c2a91d8e3"
down_revision = "e0c02eaf8190"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("deployment_info", schema=None) as batch_op:
        batch_op.add_column(sa.Column("image_update_state", sa.JSON(), nullable=True))
        batch_op.add_column(
            sa.Column("pending_image_version", sa.Text(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("pending_image_task_id", sa.Uuid(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("pending_image_config_id", sa.Text(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("pending_image_config_commit", sa.Text(), nullable=True)
        )


def downgrade():
    with op.batch_alter_table("deployment_info", schema=None) as batch_op:
        batch_op.drop_column("pending_image_config_commit")
        batch_op.drop_column("pending_image_config_id")
        batch_op.drop_column("pending_image_task_id")
        batch_op.drop_column("pending_image_version")
        batch_op.drop_column("image_update_state")
