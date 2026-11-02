"""add reboot-required fields to deployment_info

Revision ID: d4b8c2e6f1a3
Revises: c1da0b25c57a
Create Date: 2026-11-02 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "d4b8c2e6f1a3"
down_revision = "c1da0b25c57a"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("deployment_info", schema=None) as batch_op:
        batch_op.add_column(sa.Column("reboot_required", sa.Boolean(), nullable=True))
        batch_op.add_column(
            sa.Column("reboot_required_reason", sa.Text(), nullable=True)
        )
        batch_op.add_column(
            sa.Column("reboot_required_boot_id", sa.String(), nullable=True)
        )

    op.execute(
        "UPDATE deployment_info SET reboot_required = 0 "
        "WHERE reboot_required IS NULL"
    )

    with op.batch_alter_table("deployment_info", schema=None) as batch_op:
        batch_op.alter_column("reboot_required", nullable=False)


def downgrade():
    with op.batch_alter_table("deployment_info", schema=None) as batch_op:
        batch_op.drop_column("reboot_required_boot_id")
        batch_op.drop_column("reboot_required_reason")
        batch_op.drop_column("reboot_required")
