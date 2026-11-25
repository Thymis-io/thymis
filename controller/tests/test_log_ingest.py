import asyncio
import uuid
from datetime import datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from thymis_controller import db_models, models
from thymis_controller.database.base import Base
from thymis_controller.log_ingest import LogIngestor

PUBKEY = "ssh-ed25519 AAAAtest"


def _entry() -> models.LogEntry:
    return models.LogEntry(
        uuid=uuid.uuid4(),
        timestamp=datetime.now(timezone.utc),
        message="queued",
        host="homepi4",
        facility=1,
        severity=6,
        programname="test",
        syslogtag="test:",
    )


def _engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'logs.sqlite'}")
    Base.metadata.create_all(engine)
    return engine


def _count(engine) -> int:
    with Session(engine) as session:
        return session.query(db_models.LogEntry).count()


def test_stop_flushes_pending_entries(tmp_path):
    engine = _engine(tmp_path)
    ingestor = LogIngestor(engine)

    ingestor.submit(PUBKEY, [_entry(), _entry()])
    asyncio.run(ingestor.stop())

    assert _count(engine) == 2


def test_full_queue_drops_without_raising(tmp_path):
    engine = _engine(tmp_path)
    ingestor = LogIngestor(engine, max_queue=1)

    ingestor.submit(PUBKEY, [_entry()])
    ingestor.submit(PUBKEY, [_entry()])

    asyncio.run(ingestor.stop())

    assert _count(engine) == 1


def test_running_writer_flushes_submitted_entries(tmp_path):
    engine = _engine(tmp_path)
    ingestor = LogIngestor(engine)

    async def scenario():
        ingestor.start()
        ingestor.submit(PUBKEY, [_entry()])
        await asyncio.sleep(0.1)
        await ingestor.stop()

    asyncio.run(scenario())

    assert _count(engine) == 1
