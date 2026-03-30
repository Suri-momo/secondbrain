"""Summary model."""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class Summary(Base):
    """
    Represents an AI-generated summary of a conversation.

    Includes both text summary and optional TTS audio.
    """

    __tablename__ = "summaries"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    audio_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    audio_duration: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )  # Duration in seconds
    voice: Mapped[str] = mapped_column(String(50), default="alloy")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="summaries"
    )

    def __repr__(self) -> str:
        preview = (
            self.summary_text[:50] + "..." if len(self.summary_text) > 50 else self.summary_text
        )
        return f"<Summary(id={self.id}, text='{preview}')>"
