import datetime
import secrets

from sqlalchemy.exc import IntegrityError
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
    return db_models.PairingCode.expires_at > datetime.datetime.now(datetime.UTC)


def create(
    session: Session, lifetime: datetime.timedelta = DEFAULT_LIFETIME
) -> db_models.PairingCode:
    code = generate_code()
    pairing_code = db_models.PairingCode(
        code=code,
        normalized_code=normalize(code),
        expires_at=datetime.datetime.now(datetime.UTC) + lifetime,
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


def redeem(session: Session, code: str, nonce: str) -> db_models.AgentToken | None:
    if not nonce:
        return None
    pairing_code = get_valid(session, code)
    if pairing_code is None:
        return None
    if pairing_code.redeemed_at is None:
        pairing_code.redeemed_at = datetime.datetime.now(datetime.UTC)
        pairing_code.device_nonce = nonce
        session.add(
            db_models.AgentToken(
                token=f"thymis-{secrets.token_hex(64)}",
                pairing_code_id=pairing_code.id,
            )
        )
        try:
            session.commit()
        except IntegrityError:
            # Lost the race; the reloaded claim fails the check below.
            session.rollback()
    if pairing_code.device_nonce != nonce:
        return None
    return pairing_code.successor


def revoke(session: Session, code: str) -> bool:
    pairing_code = get_valid(session, code)
    if pairing_code is None:
        return False
    pairing_code.revoked = True
    if pairing_code.successor is not None:
        pairing_code.successor.revoked = True
    session.commit()
    return True
