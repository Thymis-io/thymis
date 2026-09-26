import datetime
import uuid

from pydantic import BaseModel, Field, JsonValue, field_validator


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


class AgentConversationRename(BaseModel):
    """A new title for one saved conversation."""

    title: str = Field(min_length=1, max_length=120)

    @field_validator("title")
    @classmethod
    def strip_title(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("A conversation title must not be blank")
        return stripped


__all__ = [
    "AgentConversationDetail",
    "AgentConversationRename",
    "AgentConversationSummary",
]
