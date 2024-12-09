from sqlalchemy import (
    JSON,
    UUID,
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    Uuid,
)
from thymis_controller.database.base import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Uuid(as_uuid=True), primary_key=True, index=True)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    state = Column(String(50), nullable=False)
    display_name = Column(String(255), nullable=False)
    exception = Column(Text, nullable=True)
    type = Column(String(50), nullable=False)
    task_submission_data = Column(JSON, nullable=True)  # New field for submission data

    # Composite Task Fields
    parent_task_id = Column(Uuid(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    children = Column(JSON, nullable=True)

    # Unified Process Fields
    process_program = Column(String(255), nullable=True)
    process_args = Column(JSON, nullable=True)
    process_env = Column(JSON, nullable=True)
    process_stdout = Column(Text, nullable=True)
    process_stderr = Column(Text, nullable=True)

    # Nix-Specific Extensions
    nix_status = Column(JSON, nullable=True)
    nix_files_linked = Column(Integer, nullable=True)
    nix_bytes_linked = Column(BigInteger, nullable=True)
    nix_corrupted_paths = Column(Integer, nullable=True)
    nix_untrusted_paths = Column(Integer, nullable=True)
    nix_errors = Column(JSON, nullable=True)

    nix_warnings = Column(JSON, nullable=True)
    nix_notices = Column(JSON, nullable=True)
    nix_infos = Column(JSON, nullable=True)
