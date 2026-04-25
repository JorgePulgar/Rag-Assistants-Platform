from datetime import datetime
from typing import Any

from sqlalchemy import Boolean, DateTime, ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # "user" | "assistant"
    content: Mapped[str] = mapped_column(Text, nullable=False)
    citations: Mapped[Any] = mapped_column(JSON, nullable=True)  # list[CitationObject] | None
    is_fallback: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="0", default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    conversation: Mapped["Conversation"] = relationship(  # type: ignore[name-defined]
        "Conversation", back_populates="messages"
    )
