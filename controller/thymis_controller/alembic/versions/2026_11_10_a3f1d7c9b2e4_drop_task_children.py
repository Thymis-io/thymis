"""drop tasks.children, derived from parent_task_id instead; index parent_task_id

Revision ID: a3f1d7c9b2e4
Revises: e7c3a9f2b510
Create Date: 2026-11-10 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a3f1d7c9b2e4"
down_revision = "e7c3a9f2b510"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.drop_column("children")
        batch_op.create_index(
            "ix_tasks_parent_task_id_submitted_time",
            ["parent_task_id", "submitted_time"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("tasks", schema=None) as batch_op:
        batch_op.drop_index("ix_tasks_parent_task_id_submitted_time")
        batch_op.add_column(sa.Column("children", sa.JSON(), nullable=True))
