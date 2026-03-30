"""Conversation schemas."""
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ConversationBase(BaseModel):
    """Base conversation schema with common fields."""

    title: str = Field(..., min_length=1, max_length=255, description="Conversation title")


class ConversationCreate(ConversationBase):
    """Schema for creating a new conversation."""

    pass


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation."""

    title: str | None = Field(None, min_length=1, max_length=255)


class Conversation(ConversationBase):
    """Schema for conversation responses."""

    id: UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
