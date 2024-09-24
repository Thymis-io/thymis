from thymis_controller import db_models


def test_create_hostkey(db_session):
    hostkey = db_models.HostKey(
        identifier="test_id",
        build_hash="test_hash",
        public_key="test_public_key",
        device_host="192.168.1.1",
    )
    db_session.add(hostkey)
    db_session.commit()

    retrieved_hostkey = (
        db_session.query(db_models.HostKey).filter_by(identifier="test_id").first()
    )
    assert retrieved_hostkey is not None
    assert retrieved_hostkey.identifier == "test_id"
    assert retrieved_hostkey.build_hash == "test_hash"
    assert retrieved_hostkey.public_key == "test_public_key"
    assert retrieved_hostkey.device_host == "192.168.1.1"
