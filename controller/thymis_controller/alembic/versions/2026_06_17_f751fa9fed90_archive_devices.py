"""archive devices

Revision ID: f751fa9fed90
Revises: c4e7a9b21f3d
Create Date: 2026-06-17 17:53:21.363638

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "f751fa9fed90"
down_revision = "c4e7a9b21f3d"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("deployment_info", schema=None) as batch_op:
        batch_op.add_column(sa.Column("archived", sa.Boolean(), nullable=True))

    # Set archived to True for all devices that haven't been seen in the last 7 days, and False for the rest
    op.execute(
        """
        UPDATE deployment_info
        SET archived = CASE
            WHEN last_seen IS NULL THEN 1
            WHEN last_seen < datetime('now', '-7 days') THEN 1
            ELSE 0
        END
    """
    )

    with op.batch_alter_table("deployment_info", schema=None) as batch_op:
        batch_op.alter_column("archived", nullable=False)


def downgrade():
    with op.batch_alter_table("deployment_info", schema=None) as batch_op:
        batch_op.drop_column("archived")
