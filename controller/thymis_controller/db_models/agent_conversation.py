from typing import Any, List

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, Uuid
from sqlalchemy.orm import Mapped, relationship
from thymis_controller.database.base import Base


class AgentConversation(Base):
    """One persisted Thymis Assistant conversation, owned by one signed-in user."""

    __tablename__ = "agent_conversations"

    id = Column(Uuid(as_uuid=True), primary_key=True, index=True)
    # Stable per-user identity (see dependencies.get_user_identity) so a
    # conversation survives the one-day web session it was created in.
    user_key = Column(String(320), nullable=False, index=True)
    title = Column(String(120), nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)

    messages: Mapped[List["AgentMessage"]] = relationship(
        "AgentMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AgentMessage.position",
    )

    def __repr__(self):
        return f"<AgentConversation {self.id}>"


class AgentMessage(Base):
    """One AI SDK UI message of a conversation, stored verbatim as JSON."""

    __tablename__ = "agent_messages"

    id = Column(Uuid(as_uuid=True), primary_key=True, index=True)
    conversation_id = Column(
        Uuid(as_uuid=True),
        ForeignKey("agent_conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    position = Column(Integer, nullable=False)
    # Serialized AI SDK UIMessage ({id, role, parts}) so the browser transcript,
    # including tool activity and entity links, round-trips exactly.
    message: Mapped[Any] = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False)

    conversation: Mapped["AgentConversation"] = relationship(
        "AgentConversation", back_populates="messages"
    )

    def __repr__(self):
        return f"<AgentMessage {self.id}>"
