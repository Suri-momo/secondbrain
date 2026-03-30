"""Document schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class DocumentBase(BaseModel):
    """Base document schema with common fields."""

    file_name: str = Field(..., min_length=1, max_length=255)
    file_path: str = Field(..., min_length=1, max_length=512)
    file_type: str = Field(
        ..., pattern="^(pdf|txt|audio|url|twitter)$", description="Type of document"
    )
    file_size: int | None = Field(None, ge=0, description="File size in bytes")
    extracted_text: str | None = Field(None, description="Extracted text content")


class DocumentCreate(DocumentBase):
    """Schema for creating a new document."""

    conversation_id: UUID


class Document(DocumentBase):
    """Schema for document responses."""

    id: UUID
    conversation_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
