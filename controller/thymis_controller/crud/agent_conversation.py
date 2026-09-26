"""Persistence helpers for per-user Thymis Assistant conversations."""

from __future__ import annotations

import datetime
import uuid
from typing import Any

import thymis_controller.db_models as db_models
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

DEFAULT_TITLE = "New chat"
MAX_TITLE_LENGTH = 120


def utcnow() -> datetime.datetime:
    """Naive UTC timestamp, matching the other controller tables."""
    return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)


def create(
    db_session: Session,
    user_key: str,
    title: str = DEFAULT_TITLE,
    now: datetime.datetime | None = None,
) -> db_models.AgentConversation:
    timestamp = now or utcnow()
    conversation = db_models.AgentConversation(
        id=uuid.uuid4(),
        user_key=user_key,
        title=title,
        created_at=timestamp,
        updated_at=timestamp,
    )
    db_session.add(conversation)
    db_session.commit()
    return conversation


def get(
    db_session: Session, user_key: str, conversation_id: uuid.UUID
) -> db_models.AgentConversation | None:
    return (
        db_session.query(db_models.AgentConversation)
        .options(selectinload(db_models.AgentConversation.messages))
        .filter_by(id=conversation_id)
        .filter_by(user_key=user_key)
        .first()
    )


def list_for_user(
    db_session: Session, user_key: str, query: str | None = None
) -> list[db_models.AgentConversation]:
    """List one user's conversations, newest first, optionally filtered by title."""
    statement = db_session.query(db_models.AgentConversation).filter_by(
        user_key=user_key
    )
    if query:
        # Escape LIKE wildcards so a literal % or _ in the query stays literal.
        escaped = query.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
        statement = statement.filter(
            db_models.AgentConversation.title.ilike(f"%{escaped}%", escape="\\")
        )
    return statement.order_by(db_models.AgentConversation.updated_at.desc()).all()


def message_count(
    db_session: Session, conversation: db_models.AgentConversation
) -> int:
    return (
        db_session.query(db_models.AgentMessage)
        .filter_by(conversation_id=conversation.id)
        .count()
    )


def delete(db_session: Session, conversation: db_models.AgentConversation) -> None:
    db_session.delete(conversation)
    db_session.commit()


def title_from_prompt(prompt: str) -> str:
    """Derive a conversation title from the first user prompt."""
    collapsed = " ".join(prompt.split())
    if not collapsed:
        return DEFAULT_TITLE
    if len(collapsed) <= MAX_TITLE_LENGTH:
        return collapsed
    return collapsed[: MAX_TITLE_LENGTH - 1].rstrip() + "…"


def append_messages(
    db_session: Session,
    conversation: db_models.AgentConversation,
    messages: list[dict[str, Any]],
    now: datetime.datetime | None = None,
) -> None:
    """Append AI SDK UI messages to the end of a conversation.

    Each message keeps its own ``id`` inside the stored JSON; the database row id
    is independent of it.
    """

    if not messages:
        return
    timestamp = now or utcnow()
    last_position = (
        db_session.query(func.max(db_models.AgentMessage.position))
        .filter_by(conversation_id=conversation.id)
        .scalar()
        or 0
    )
    for offset, message in enumerate(messages, start=1):
        db_session.add(
            db_models.AgentMessage(
                id=uuid.uuid4(),
                conversation_id=conversation.id,
                position=last_position + offset,
                message=message,
                created_at=timestamp,
            )
        )
    conversation.updated_at = timestamp
    db_session.commit()


def delete_last_message(
    db_session: Session, conversation: db_models.AgentConversation
) -> bool:
    """Drop the newest stored message, e.g. the reply being regenerated."""
    last_message = (
        db_session.query(db_models.AgentMessage)
        .filter_by(conversation_id=conversation.id)
        .order_by(db_models.AgentMessage.position.desc())
        .first()
    )
    if last_message is None:
        return False
    db_session.delete(last_message)
    conversation.updated_at = utcnow()
    db_session.commit()
    return True


def rename(
    db_session: Session, conversation: db_models.AgentConversation, title: str
) -> None:
    conversation.title = title
    db_session.commit()


def create_file(
    db_session: Session,
    conversation: db_models.AgentConversation,
    content: bytes,
    media_type: str,
    filename: str,
    now: datetime.datetime | None = None,
) -> db_models.AgentFile:
    """Store one conversation attachment and return it."""
    agent_file = db_models.AgentFile(
        id=uuid.uuid4(),
        conversation_id=conversation.id,
        media_type=media_type,
        filename=filename,
        size=len(content),
        content=content,
        created_at=now or utcnow(),
    )
    db_session.add(agent_file)
    db_session.commit()
    return agent_file


def get_file(
    db_session: Session, user_key: str, file_id: uuid.UUID
) -> db_models.AgentFile | None:
    """Return one attachment, but only for the user who owns its conversation."""
    return (
        db_session.query(db_models.AgentFile)
        .join(
            db_models.AgentConversation,
            db_models.AgentFile.conversation_id == db_models.AgentConversation.id,
        )
        .filter(db_models.AgentFile.id == file_id)
        .filter(db_models.AgentConversation.user_key == user_key)
        .first()
    )


def transcript(conversation: db_models.AgentConversation) -> list[Any]:
    """Return the stored UI messages in conversation order."""
    return [
        message.message
        for message in sorted(conversation.messages, key=lambda item: item.position)
    ]
