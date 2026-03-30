"""Summary schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SummaryBase(BaseModel):
    """Base summary schema with common fields."""

    summary_text: str = Field(..., min_length=1, description="Summary text content")
    audio_url: str | None = Field(None, max_length=512, description="URL to audio file")
    audio_duration: int | None = Field(None, ge=0, description="Audio duration in seconds")
    voice: str = Field(default="alloy", max_length=50, description="TTS voice used")


class SummaryCreate(SummaryBase):
    """Schema for creating a new summary."""

    conversation_id: UUID


class Summary(SummaryBase):
    """Schema for summary responses."""

    id: UUID
    conversation_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
