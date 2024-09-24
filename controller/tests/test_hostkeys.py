import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from thymis_controller import db_models
from thymis_controller.database.base import Base

# Create an in-memory SQLite database for testing
DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(scope="module")
def engine():
    return create_engine(DATABASE_URL)


@pytest.fixture(scope="module")
def tables(engine):
    Base.metadata.create_all(engine)
    yield
    Base.metadata.drop_all(engine)


@pytest.fixture(scope="module")
def session(engine, tables):
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_hostkey(session):
    hostkey = db_models.HostKey(
        identifier="test_id",
        build_hash="test_hash",
        public_key="test_public_key",
        device_host="192.168.1.1",
    )
    session.add(hostkey)
    session.commit()

    retrieved_hostkey = (
        session.query(db_models.HostKey).filter_by(identifier="test_id").first()
    )
    assert retrieved_hostkey is not None
    assert retrieved_hostkey.identifier == "test_id"
    assert retrieved_hostkey.build_hash == "test_hash"
    assert retrieved_hostkey.public_key == "test_public_key"
    assert retrieved_hostkey.device_host == "192.168.1.1"
