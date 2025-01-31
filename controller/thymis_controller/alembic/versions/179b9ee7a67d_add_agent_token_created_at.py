"""empty message

Revision ID: 179b9ee7a67d
Revises: 9dc5fb3bec50
Create Date: 2025-01-30 15:47:25.592802

"""

import datetime

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "179b9ee7a67d"
down_revision = "9dc5fb3bec50"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("agent_tokens", sa.Column("created_at", sa.DateTime()))

    now = datetime.datetime.now()
    op.execute(f"UPDATE agent_tokens SET created_at = '{now}' WHERE created_at IS NULL")


def downgrade():
    op.drop_column("agent_tokens", "created_at")
