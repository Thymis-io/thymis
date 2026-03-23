"""add controller_settings table

Revision ID: a1b2c3d4e5f6
Revises: 40befde2965c
Create Date: 2026-03-23 00:00:00.000000

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "a1b2c3d4e5f6"
down_revision = "40befde2965c"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "controller_settings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "auto_update_enabled", sa.Boolean(), nullable=False, server_default="0"
        ),
        sa.Column(
            "auto_update_schedule",
            sa.String(length=255),
            nullable=False,
            server_default="daily",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Insert the single default row
    op.execute(
        "INSERT INTO controller_settings (id, auto_update_enabled, auto_update_schedule) VALUES (1, 0, 'daily')"
    )


def downgrade():
    op.drop_table("controller_settings")
