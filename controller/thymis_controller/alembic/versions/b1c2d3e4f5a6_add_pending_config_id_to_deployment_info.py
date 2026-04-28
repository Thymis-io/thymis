"""add pending_config_id to deployment_info

Revision ID: b1c2d3e4f5a6
Revises: b7e2f1a3c8d9
Create Date: 2026-04-14 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "b1c2d3e4f5a6"
down_revision = "b7e2f1a3c8d9"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("deployment_info", schema=None) as batch_op:
        batch_op.add_column(sa.Column("pending_config_id", sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table("deployment_info", schema=None) as batch_op:
        batch_op.drop_column("pending_config_id")
