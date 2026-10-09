import datetime
import secrets

from sqlalchemy.orm import Session
from thymis_controller import db_models

ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"  # Crockford Base32
DEFAULT_LIFETIME = datetime.timedelta(days=1)


def generate_code(groups: int = 3, group_len: int = 4) -> str:
    raw = "".join(secrets.choice(ALPHABET) for _ in range(groups * group_len))
    return "-".join(raw[i : i + group_len] for i in range(0, len(raw), group_len))


def normalize(code: str) -> str:
    code = code.upper().replace("-", "").replace(" ", "")
    # Forgive common typos: O→0, I/L→1
    return code.translate(str.maketrans("OIL", "011"))


def _unexpired():
    return db_models.PairingCode.expires_at > datetime.datetime.now(
        datetime.timezone.utc
    )


def create(
    session: Session, lifetime: datetime.timedelta = DEFAULT_LIFETIME
) -> db_models.PairingCode:
    """Minting the token with the code is what keeps redemption a pure
    lookup, with no window for two requests to race a successor onto one
    code. The successor inherits the code's expiry so an abandoned code
    leaves no permanent credential; `consume` promotes it on proven use.
    """
    expires_at = datetime.datetime.now(datetime.timezone.utc) + lifetime
    successor = db_models.AgentToken(
        original_disk_config_commit=None,
        original_disk_config_id=None,
        token=f"thymis-{secrets.token_hex(64)}",
        expires_at=expires_at,
    )
    session.add(successor)
    session.flush()  # assign successor.id without ending the transaction
    code = generate_code()
    pairing_code = db_models.PairingCode(
        code=code,
        normalized_code=normalize(code),
        expires_at=expires_at,
        successor_id=successor.id,
    )
    session.add(pairing_code)
    session.commit()
    session.refresh(pairing_code)
    return pairing_code


def get_valid(session: Session, code: str) -> db_models.PairingCode | None:
    return (
        session.query(db_models.PairingCode)
        .filter_by(normalized_code=normalize(code), revoked=False)
        .filter(_unexpired())
        .first()
    )


def redeem(session: Session, code: str) -> db_models.AgentToken | None:
    pairing_code = get_valid(session, code)
    if pairing_code is None:
        return None
    if pairing_code.redeemed_at is None:
        pairing_code.redeemed_at = datetime.datetime.now(datetime.timezone.utc)
        session.commit()
    return pairing_code.successor


def consume(session: Session, successor: db_models.AgentToken) -> None:
    """Call on proven use. Idempotent, and a no-op for image-built tokens,
    which have no pairing code."""
    pairing_code = (
        session.query(db_models.PairingCode)
        .filter_by(successor_id=successor.id, revoked=False)
        .first()
    )
    if pairing_code is None:
        return
    pairing_code.revoked = True
    successor.expires_at = None
    session.commit()


def revoke(session: Session, code: str) -> bool:
    """Revokes the successor too: an unredeemed credential must not outlive
    the code naming it."""
    pairing_code = get_valid(session, code)
    if pairing_code is None:
        return False
    pairing_code.revoked = True
    pairing_code.successor.revoked = True
    session.commit()
    return True
