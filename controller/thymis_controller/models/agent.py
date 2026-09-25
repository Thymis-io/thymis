import datetime
import uuid

from pydantic import BaseModel, JsonValue


class AgentConversationSummary(BaseModel):
    """A persisted Thymis Assistant conversation, without its transcript."""

    id: uuid.UUID
    title: str
    created_at: datetime.datetime
    updated_at: datetime.datetime
    message_count: int


class AgentConversationDetail(AgentConversationSummary):
    """A conversation with its full AI SDK UI-message transcript."""

    messages: list[JsonValue]


__all__ = ["AgentConversationDetail", "AgentConversationSummary"]
