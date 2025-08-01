import datetime
import random
import uuid
from datetime import datetime, timedelta, timezone

import thymis_controller.db_models as db_models
from sqlalchemy.orm import Session

# see https://github.com/encode/starlette/blob/a404872b9192297ccfe93ff036faf884e4d35c08/starlette/responses.py#L109
# cookie[key]["expires"] = expires
# see https://github.com/python/cpython/blob/c9932a9ec8a3077933a85101aae9c3ac155e6d04/Lib/http/cookies.py#L392
# if key == "expires" and isinstance(value, int):
#     append("%s=%s" % (self._reserved[key], _getdate(value)))
# see https://github.com/python/cpython/blob/c9932a9ec8a3077933a85101aae9c3ac155e6d04/Lib/http/cookies.py#L228
# The _getdate() routine is used to set the expiration time in the cookie's HTTP
# header.  By default, _getdate() returns the current time in the appropriate
# "expires" format for a Set-Cookie header.  The one optional argument is an
# offset from now, in seconds.  For example, an offset of -3600 means "one hour
# ago".  The offset may be a floating-point number.
# ==============================================================================
# conclusion: to set the expiration time of a cookie, just set the "expires" key
# as well as max_age to the same amount of seconds
# ==============================================================================
SESSION_LIFETIME = timedelta(minutes=1)
SESSION_LIFETIME_SECONDS = SESSION_LIFETIME.total_seconds()


def create(db_session: Session) -> db_models.WebSession:
    id = uuid.uuid4()
    session_token = random.randbytes(64).hex()
    created_at = datetime.now(timezone.utc)
    web_session = db_models.WebSession(
        id=id, session_token=session_token, created_at=created_at
    )
    db_session.add(web_session)
    db_session.commit()
    return web_session


def validate(db_session: Session, session_id: uuid.UUID, session_token: str) -> bool:
    web_session = (
        db_session.query(db_models.WebSession)
        .filter_by(id=session_id)
        .filter_by(session_token=session_token)
        .first()
    )

    if web_session is None:
        return False

    expiration_time = (
        web_session.created_at.replace(tzinfo=timezone.utc) + SESSION_LIFETIME
    )
    is_expired = expiration_time < datetime.now(timezone.utc)
    if is_expired:
        delete(db_session, session_id)
    return not is_expired


def delete(db_session: Session, session_id: uuid.UUID):
    db_session.query(db_models.WebSession).filter_by(id=session_id).delete()
    db_session.commit()
