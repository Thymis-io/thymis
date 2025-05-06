"""empty message

Revision ID: 9c84d1271466
Revises: 142c94c6b394
Create Date: 2025-05-05 15:30:08.868307

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "9c84d1271466"
down_revision = "142c94c6b394"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "agent_connections",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("connected_at", sa.DateTime(), nullable=False),
        sa.Column("disconnected_at", sa.DateTime(), nullable=True),
        sa.Column("deployment_info_id", sa.Uuid(), nullable=True),
        sa.ForeignKeyConstraint(
            ["deployment_info_id"],
            ["deployment_info.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade():
    op.drop_table("agent_connections")
