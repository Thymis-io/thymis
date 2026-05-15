"""add_ram_bytes_and_notes_to_deployment_info

Revision ID: 20e7fc7d369d
Revises: 6ace24c0d4de
Create Date: 2026-05-14

"""
import sqlalchemy as sa
from alembic import op

revision = "20e7fc7d369d"
down_revision = "6ace24c0d4de"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("deployment_info", schema=None) as batch_op:
        batch_op.add_column(sa.Column("ram_bytes", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("notes", sa.Text(), nullable=True))


def downgrade():
    with op.batch_alter_table("deployment_info", schema=None) as batch_op:
        batch_op.drop_column("notes")
        batch_op.drop_column("ram_bytes")
