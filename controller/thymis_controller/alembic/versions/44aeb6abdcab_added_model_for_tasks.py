"""added model for tasks

Revision ID: 44aeb6abdcab
Revises: 02cb9f4abdab
Create Date: 2024-11-21 14:47:51.595656

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "44aeb6abdcab"
down_revision = "02cb9f4abdab"
branch_labels = None
depends_on = None


def upgrade():
    # Create the tasks table
    op.create_table(
        "tasks",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True, nullable=False),
        sa.Column("start_time", sa.DateTime(), nullable=False),
        sa.Column("end_time", sa.DateTime(), nullable=True),
        sa.Column("state", sa.String(50), nullable=False),
        sa.Column("exception", sa.Text(), nullable=True),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column(
            "task_submission_data", sa.JSON(), nullable=True
        ),  # New field for submission data
        # Composite Task Fields
        sa.Column(
            "parent_task_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("tasks.id"),
            nullable=True,
        ),
        sa.Column("children", sa.JSON, nullable=True),
        # Unified Process Fields
        sa.Column("process_program", sa.String(255), nullable=True),
        sa.Column("process_args", sa.JSON(), nullable=True),
        sa.Column("process_env", sa.JSON(), nullable=True),
        sa.Column("process_stdout", sa.Text(), nullable=True),
        sa.Column("process_stderr", sa.Text(), nullable=True),
        # Nix-Specific Extensions
        sa.Column("nix_status", sa.JSON(), nullable=True),
        sa.Column("nix_files_linked", sa.Integer, nullable=True),
        sa.Column("nix_bytes_linked", sa.BigInteger(), nullable=True),
        sa.Column("nix_corrupted_paths", sa.Integer(), nullable=True),
        sa.Column("nix_untrusted_paths", sa.Integer(), nullable=True),
        sa.Column("nix_errors", sa.JSON(), nullable=True),
        sa.Column("nix_warnings", sa.JSON(), nullable=True),
        sa.Column("nix_notices", sa.JSON(), nullable=True),
        sa.Column("nix_infos", sa.JSON(), nullable=True),
    )
    op.create_index(op.f("ix_tasks_id"), "tasks", ["id"], unique=False)


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_tasks_id"), table_name="tasks")
    op.drop_table("tasks")
    # ### end Alembic commands ###