from sqlalchemy import (
    JSON,
    UUID,
    BigInteger,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    LargeBinary,
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
    exception = Column(Text, nullable=True)
    task_type = Column(String(50), nullable=False)
    task_submission_data = Column(JSON, nullable=True)  # New field for submission data

    # Composite Task Fields
    parent_task_id = Column(Uuid(as_uuid=True), ForeignKey("tasks.id"), nullable=True)
    children = Column(JSON, nullable=True)

    # Unified Process Fields
    process_program = Column(String(255), nullable=True)
    process_args = Column(JSON, nullable=True)
    process_env = Column(JSON, nullable=True)
    process_stdout = Column(LargeBinary, nullable=True)
    process_stderr = Column(LargeBinary, nullable=True)

    # Nix-Specific Extensions
    nix_status = Column(JSON, nullable=True)
    nix_errors = Column(JSON, nullable=True)
    nix_files_linked = Column(Integer, nullable=True)
    nix_bytes_linked = Column(BigInteger, nullable=True)
    nix_corrupted_paths = Column(Integer, nullable=True)
    nix_untrusted_paths = Column(Integer, nullable=True)
    nix_error_logs = Column(JSON, nullable=True)
    nix_warning_logs = Column(JSON, nullable=True)
    nix_notice_logs = Column(JSON, nullable=True)
    nix_info_logs = Column(JSON, nullable=True)

    def add_exception(self, exception: str):
        if self.exception is None:
            self.exception = exception
        else:
            self.exception += "\n" + exception
