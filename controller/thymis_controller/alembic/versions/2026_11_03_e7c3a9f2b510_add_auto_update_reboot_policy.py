"""add auto_update_reboot_policy to controller_settings

Revision ID: e7c3a9f2b510
Revises: d4b8c2e6f1a3
Create Date: 2026-11-03 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e7c3a9f2b510"
down_revision = "d4b8c2e6f1a3"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("controller_settings", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "auto_update_reboot_policy",
                sa.String(length=32),
                nullable=False,
                server_default="never",
            )
        )


def downgrade():
    with op.batch_alter_table("controller_settings", schema=None) as batch_op:
        batch_op.drop_column("auto_update_reboot_policy")
