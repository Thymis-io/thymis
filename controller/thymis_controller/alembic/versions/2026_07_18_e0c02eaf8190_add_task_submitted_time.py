"""add task submitted time

Revision ID: e0c02eaf8190
Revises: 20e7fc7d369d
Create Date: 2026-07-18 15:37:02.794580

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "e0c02eaf8190"
down_revision = "20e7fc7d369d"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.add_column(sa.Column("submitted_time", sa.DateTime(), nullable=True))
        batch_op.alter_column("start_time", existing_type=sa.DATETIME(), nullable=True)

    op.execute("UPDATE tasks SET submitted_time = start_time")

    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.alter_column(
            "submitted_time", existing_type=sa.DATETIME(), nullable=False
        )


def downgrade():
    op.execute("UPDATE tasks SET start_time = submitted_time WHERE start_time IS NULL")

    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.alter_column("start_time", existing_type=sa.DATETIME(), nullable=False)
        batch_op.drop_column("submitted_time")
