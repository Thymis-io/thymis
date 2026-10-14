"""add paring codes

Revision ID: c1da0b25c57a
Revises: e0c02eaf8190
Create Date: 2026-10-14 16:00:46.906330

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "c1da0b25c57a"
down_revision = "e0c02eaf8190"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "pairing_codes",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("normalized_code", sa.String(), nullable=False),
        sa.Column("device_nonce", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("redeemed_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    with op.batch_alter_table("pairing_codes", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_pairing_codes_id"), ["id"], unique=False)
        batch_op.create_index(
            batch_op.f("ix_pairing_codes_normalized_code"),
            ["normalized_code"],
            unique=True,
        )

    with op.batch_alter_table("agent_tokens", schema=None) as batch_op:
        batch_op.add_column(sa.Column("pairing_code_id", sa.Uuid(), nullable=True))
        batch_op.alter_column(
            "original_disk_config_commit", existing_type=sa.VARCHAR(), nullable=True
        )
        batch_op.alter_column(
            "original_disk_config_id", existing_type=sa.VARCHAR(), nullable=True
        )
        batch_op.create_index(
            batch_op.f("ix_agent_tokens_pairing_code_id"),
            ["pairing_code_id"],
            unique=True,
        )
        batch_op.create_foreign_key(
            "fk_agent_tokens_pairing_code_id",
            "pairing_codes",
            ["pairing_code_id"],
            ["id"],
        )


def downgrade():
    with op.batch_alter_table("agent_tokens", schema=None) as batch_op:
        batch_op.drop_constraint("fk_agent_tokens_pairing_code_id", type_="foreignkey")
        batch_op.drop_index(batch_op.f("ix_agent_tokens_pairing_code_id"))
        batch_op.alter_column(
            "original_disk_config_id", existing_type=sa.VARCHAR(), nullable=False
        )
        batch_op.alter_column(
            "original_disk_config_commit", existing_type=sa.VARCHAR(), nullable=False
        )
        batch_op.drop_column("pairing_code_id")

    with op.batch_alter_table("pairing_codes", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_pairing_codes_normalized_code"))
        batch_op.drop_index(batch_op.f("ix_pairing_codes_id"))

    op.drop_table("pairing_codes")
