"""add_name_to_deployment_info

Revision ID: b7e2f1a3c8d9
Revises: 6a32d509779a
Create Date: 2026-04-01 22:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = "b7e2f1a3c8d9"
down_revision = "6a32d509779a"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("deployment_info", schema=None) as batch_op:
        batch_op.add_column(sa.Column("name", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("deployment_info", schema=None) as batch_op:
        batch_op.drop_column("name")
