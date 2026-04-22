from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    assistant_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("assistants.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    assistant: Mapped["Assistant"] = relationship(  # type: ignore[name-defined]
        "Assistant", back_populates="conversations"
    )
    messages: Mapped[list["Message"]] = relationship(  # type: ignore[name-defined]
        "Message", back_populates="conversation", cascade="all, delete-orphan"
    )
