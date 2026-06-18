"""add_user_info_to_sessions

Revision ID: c4e7a9b21f3d
Revises: 84112566ca43
Create Date: 2026-06-12 12:00:00.000000

"""
import sqlalchemy as sa
from alembic import op

revision = "c4e7a9b21f3d"
down_revision = "84112566ca43"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("sessions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("username", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("given_name", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("family_name", sa.String(), nullable=True))
        batch_op.add_column(sa.Column("email", sa.String(), nullable=True))


def downgrade():
    with op.batch_alter_table("sessions", schema=None) as batch_op:
        batch_op.drop_column("email")
        batch_op.drop_column("family_name")
        batch_op.drop_column("given_name")
        batch_op.drop_column("username")
