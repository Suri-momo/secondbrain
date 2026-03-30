"""Document model."""
from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.conversation import Conversation


class Document(Base):
    """
    Represents an uploaded or imported document.

    Supports PDFs, text files, audio files, URLs, and Twitter bookmarks.
    """

    __tablename__ = "documents"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    conversation_id: Mapped[UUID] = mapped_column(ForeignKey("conversations.id"), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[str] = mapped_column(
        String(50), nullable=False
    )  # "pdf", "txt", "audio", "url", "twitter"
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)  # Size in bytes
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Relationship
    conversation: Mapped["Conversation"] = relationship(
        "Conversation", back_populates="documents"
    )

    def __repr__(self) -> str:
        return (
            f"<Document(id={self.id}, file_name='{self.file_name}', "
            f"file_type='{self.file_type}')>"
        )
