"""Unit tests for Pydantic schemas."""
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import (
    ConversationCreate,
    ConversationUpdate,
    DocumentCreate,
    MessageCreate,
    SummaryCreate,
)


class TestConversationSchemas:
    """Test conversation schemas."""

    def test_conversation_create_valid(self):
        """Test creating a valid conversation."""
        data = {"title": "My Conversation"}
        schema = ConversationCreate(**data)
        assert schema.title == "My Conversation"

    def test_conversation_create_empty_title(self):
        """Test that empty title is rejected."""
        with pytest.raises(ValidationError):
            ConversationCreate(title="")

    def test_conversation_create_title_too_long(self):
        """Test that title longer than 255 characters is rejected."""
        with pytest.raises(ValidationError):
            ConversationCreate(title="A" * 256)

    def test_conversation_update_optional(self):
        """Test that all fields in ConversationUpdate are optional."""
        schema = ConversationUpdate()
        assert schema.title is None


class TestMessageSchemas:
    """Test message schemas."""

    def test_message_create_valid(self):
        """Test creating a valid message."""
        conversation_id = uuid4()
        data = {
            "conversation_id": conversation_id,
            "role": "user",
            "content": "Hello!",
        }
        schema = MessageCreate(**data)
        assert schema.conversation_id == conversation_id
        assert schema.role == "user"
        assert schema.content == "Hello!"

    def test_message_create_invalid_role(self):
        """Test that invalid role is rejected."""
        conversation_id = uuid4()
        with pytest.raises(ValidationError):
            MessageCreate(
                conversation_id=conversation_id,
                role="invalid",
                content="Hello!",
            )

    def test_message_create_empty_content(self):
        """Test that empty content is rejected."""
        conversation_id = uuid4()
        with pytest.raises(ValidationError):
            MessageCreate(
                conversation_id=conversation_id,
                role="user",
                content="",
            )

    def test_message_valid_roles(self):
        """Test that user, assistant, and system roles are valid."""
        conversation_id = uuid4()
        for role in ["user", "assistant", "system"]:
            schema = MessageCreate(
                conversation_id=conversation_id,
                role=role,
                content="Test",
            )
            assert schema.role == role


class TestDocumentSchemas:
    """Test document schemas."""

    def test_document_create_valid(self):
        """Test creating a valid document."""
        conversation_id = uuid4()
        data = {
            "conversation_id": conversation_id,
            "file_name": "test.pdf",
            "file_path": "/uploads/test.pdf",
            "file_type": "pdf",
            "file_size": 1024,
        }
        schema = DocumentCreate(**data)
        assert schema.conversation_id == conversation_id
        assert schema.file_name == "test.pdf"
        assert schema.file_type == "pdf"
        assert schema.file_size == 1024

    def test_document_create_invalid_file_type(self):
        """Test that invalid file_type is rejected."""
        conversation_id = uuid4()
        with pytest.raises(ValidationError):
            DocumentCreate(
                conversation_id=conversation_id,
                file_name="test.doc",
                file_path="/uploads/test.doc",
                file_type="doc",  # Invalid, not in allowed types
            )

    def test_document_create_valid_file_types(self):
        """Test that all valid file types are accepted."""
        conversation_id = uuid4()
        for file_type in ["pdf", "txt", "audio", "url", "twitter"]:
            schema = DocumentCreate(
                conversation_id=conversation_id,
                file_name=f"test.{file_type}",
                file_path=f"/uploads/test.{file_type}",
                file_type=file_type,
            )
            assert schema.file_type == file_type

    def test_document_create_negative_file_size(self):
        """Test that negative file_size is rejected."""
        conversation_id = uuid4()
        with pytest.raises(ValidationError):
            DocumentCreate(
                conversation_id=conversation_id,
                file_name="test.pdf",
                file_path="/uploads/test.pdf",
                file_type="pdf",
                file_size=-1,
            )


class TestSummarySchemas:
    """Test summary schemas."""

    def test_summary_create_valid(self):
        """Test creating a valid summary."""
        conversation_id = uuid4()
        data = {
            "conversation_id": conversation_id,
            "summary_text": "This is a test summary",
            "voice": "alloy",
        }
        schema = SummaryCreate(**data)
        assert schema.conversation_id == conversation_id
        assert schema.summary_text == "This is a test summary"
        assert schema.voice == "alloy"

    def test_summary_create_with_audio(self):
        """Test creating a summary with audio metadata."""
        conversation_id = uuid4()
        data = {
            "conversation_id": conversation_id,
            "summary_text": "Test summary",
            "audio_url": "/uploads/summary.mp3",
            "audio_duration": 180,
            "voice": "nova",
        }
        schema = SummaryCreate(**data)
        assert schema.audio_url == "/uploads/summary.mp3"
        assert schema.audio_duration == 180
        assert schema.voice == "nova"

    def test_summary_create_empty_text(self):
        """Test that empty summary_text is rejected."""
        conversation_id = uuid4()
        with pytest.raises(ValidationError):
            SummaryCreate(
                conversation_id=conversation_id,
                summary_text="",
            )

    def test_summary_create_negative_duration(self):
        """Test that negative audio_duration is rejected."""
        conversation_id = uuid4()
        with pytest.raises(ValidationError):
            SummaryCreate(
                conversation_id=conversation_id,
                summary_text="Test",
                audio_duration=-1,
            )
