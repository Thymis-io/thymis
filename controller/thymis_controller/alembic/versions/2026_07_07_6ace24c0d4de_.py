"""empty message

Revision ID: 6ace24c0d4de
Revises: f751fa9fed90
Create Date: 2026-07-07 20:50:50.261360

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "6ace24c0d4de"
down_revision = "f751fa9fed90"
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table("log_entries", schema=None) as batch_op:
        batch_op.create_index(
            "ix_log_entries_deployment_info_id_programname",
            ["deployment_info_id", "programname"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("log_entries", schema=None) as batch_op:
        batch_op.drop_index("ix_log_entries_deployment_info_id_programname")
