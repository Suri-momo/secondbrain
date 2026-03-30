"""Message schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class MessageBase(BaseModel):
    """Base message schema with common fields."""

    role: str = Field(..., pattern="^(user|assistant|system)$", description="Message role")
    content: str = Field(..., min_length=1, description="Message content")


class MessageCreate(MessageBase):
    """Schema for creating a new message."""

    conversation_id: UUID


class Message(MessageBase):
    """Schema for message responses."""

    id: UUID
    conversation_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
