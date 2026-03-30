"""Unit tests for SQLAlchemy models."""
from datetime import datetime
from uuid import UUID

import pytest

from app.models import Conversation, Document, Message, Summary


def test_conversation_creation():
    """Test creating a Conversation model instance."""
    conversation = Conversation(title="Test Conversation")

    assert conversation.title == "Test Conversation"
    # Note: id, created_at, updated_at are only set when inserted into database
    assert conversation.messages == []
    assert conversation.documents == []
    assert conversation.summaries == []


def test_message_creation():
    """Test creating a Message model instance."""
    from uuid import uuid4

    conversation_id = uuid4()
    message = Message(
        conversation_id=conversation_id, role="user", content="Hello, SecondBrain!"
    )

    assert message.conversation_id == conversation_id
    assert message.role == "user"
    assert message.content == "Hello, SecondBrain!"
    # Note: id and created_at are only set when inserted into database


def test_document_creation():
    """Test creating a Document model instance."""
    from uuid import uuid4

    conversation_id = uuid4()
    document = Document(
        conversation_id=conversation_id,
        file_name="test.pdf",
        file_path="/uploads/test.pdf",
        file_type="pdf",
        file_size=1024,
    )

    assert document.conversation_id == conversation_id
    assert document.file_name == "test.pdf"
    assert document.file_path == "/uploads/test.pdf"
    assert document.file_type == "pdf"
    assert document.file_size == 1024
    assert document.extracted_text is None
    # Note: id and created_at are only set when inserted into database


def test_summary_creation():
    """Test creating a Summary model instance."""
    from uuid import uuid4

    conversation_id = uuid4()
    summary = Summary(
        conversation_id=conversation_id,
        summary_text="This is a test summary",
        voice="alloy",
    )

    assert summary.conversation_id == conversation_id
    assert summary.summary_text == "This is a test summary"
    assert summary.audio_url is None
    assert summary.audio_duration is None
    assert summary.voice == "alloy"
    # Note: id and created_at are only set when inserted into database


def test_conversation_repr():
    """Test Conversation __repr__ method."""
    conversation = Conversation(title="Test Conversation")
    repr_str = repr(conversation)

    assert "Conversation" in repr_str
    assert str(conversation.id) in repr_str
    assert "Test Conversation" in repr_str


def test_message_repr():
    """Test Message __repr__ method."""
    conversation = Conversation(title="Test")
    message = Message(conversation_id=conversation.id, role="user", content="Hello!")
    repr_str = repr(message)

    assert "Message" in repr_str
    assert str(message.id) in repr_str
    assert message.role in repr_str
    assert "Hello!" in repr_str


def test_message_repr_truncates_long_content():
    """Test Message __repr__ truncates content longer than 50 characters."""
    conversation = Conversation(title="Test")
    long_content = "A" * 100
    message = Message(conversation_id=conversation.id, role="user", content=long_content)
    repr_str = repr(message)

    assert "..." in repr_str
    assert len(long_content) > 50
