import asyncio
import uuid

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from thymis_controller import db_models
from thymis_controller.database.base import Base
from thymis_controller.network_relay import NetworkRelay

PUBLIC_KEY = (
    "ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAILeEK565Rafc3wkNOTG3yfgB5V8zm3mTeUHoJ0cMFoMq"
)


def make_relay() -> NetworkRelay:
    relay = NetworkRelay.__new__(NetworkRelay)
    relay.public_key_to_connection_id = {}
    relay.connection_id_to_public_key = {}
    relay.connection_id_to_start_message = {}
    return relay


def register(relay: NetworkRelay, connection_id: str) -> None:
    relay.public_key_to_connection_id[PUBLIC_KEY] = connection_id
    relay.connection_id_to_public_key[connection_id] = PUBLIC_KEY
    relay.connection_id_to_start_message[connection_id] = "start-message"


def test_release_owning_connection_drops_binding():
    relay = make_relay()
    register(relay, "live")

    relay.release_agent_connection("live")

    assert PUBLIC_KEY not in relay.public_key_to_connection_id
    assert relay.connection_id_to_public_key == {}
    assert relay.connection_id_to_start_message == {}


def test_release_stale_connection_keeps_live_binding():
    relay = make_relay()
    register(relay, "stale")
    # the agent reconnected with the same public key before the stale
    # connection finished tearing down
    relay.public_key_to_connection_id[PUBLIC_KEY] = "live"
    relay.connection_id_to_public_key["live"] = PUBLIC_KEY
    relay.connection_id_to_start_message["live"] = "start-message"

    relay.release_agent_connection("stale")

    assert relay.public_key_to_connection_id[PUBLIC_KEY] == "live"
    assert "stale" not in relay.connection_id_to_public_key
    assert "stale" not in relay.connection_id_to_start_message


def test_release_unknown_connection_is_noop():
    relay = make_relay()
    register(relay, "live")

    relay.release_agent_connection("unknown")

    assert relay.public_key_to_connection_id[PUBLIC_KEY] == "live"
    assert relay.connection_id_to_public_key == {"live": PUBLIC_KEY}


def _make_engine(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'relay.sqlite'}")
    Base.metadata.create_all(engine)
    return engine


def test_access_client_unknown_target_returns_none(tmp_path):
    relay = make_relay()
    relay.db_engine = _make_engine(tmp_path)

    assert (
        asyncio.run(relay.get_agent_connection_id_for_access_client(str(uuid.uuid4())))
        is None
    )


def test_access_client_malformed_target_returns_none(tmp_path):
    relay = make_relay()
    relay.db_engine = _make_engine(tmp_path)

    assert (
        asyncio.run(relay.get_agent_connection_id_for_access_client("not-a-uuid"))
        is None
    )


def test_access_client_offline_device_returns_none_then_live_id(tmp_path):
    engine = _make_engine(tmp_path)
    with Session(engine) as session:
        deployment = db_models.DeploymentInfo(ssh_public_key=PUBLIC_KEY)
        session.add(deployment)
        session.commit()
        deployment_id = deployment.id

    relay = make_relay()
    relay.db_engine = engine

    assert (
        asyncio.run(relay.get_agent_connection_id_for_access_client(str(deployment_id)))
        is None
    )

    register(relay, "live")
    assert (
        asyncio.run(relay.get_agent_connection_id_for_access_client(str(deployment_id)))
        == "live"
    )
