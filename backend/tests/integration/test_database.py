"""Integration tests for database CRUD operations."""
import os
import tempfile
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.database import Base
from app.models import Conversation, Document, Message, Summary


@pytest.fixture
def test_db():
    """Create a temporary test database."""
    # Create a temporary file for the test database
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.db"
    database_url = f"sqlite:///{db_path}"

    # Create engine and tables
    engine = create_engine(database_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)

    # Create session factory
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Yield session for testing
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        engine.dispose()
        # Clean up temporary database
        if db_path.exists():
            db_path.unlink()
        Path(temp_dir).rmdir()


def test_create_conversation(test_db: Session):
    """Test creating a conversation."""
    conversation = Conversation(title="Test Conversation")
    test_db.add(conversation)
    test_db.commit()
    test_db.refresh(conversation)

    # Query back
    retrieved = test_db.query(Conversation).filter_by(id=conversation.id).first()
    assert retrieved is not None
    assert retrieved.title == "Test Conversation"
    assert retrieved.id == conversation.id


def test_create_conversation_with_messages(test_db: Session):
    """Test creating a conversation with messages."""
    # Create conversation
    conversation = Conversation(title="Chat about AI")
    test_db.add(conversation)
    test_db.commit()
    test_db.refresh(conversation)

    # Add messages
    msg1 = Message(
        conversation_id=conversation.id,
        role="user",
        content="What is AI?",
    )
    msg2 = Message(
        conversation_id=conversation.id,
        role="assistant",
        content="AI stands for Artificial Intelligence...",
    )
    test_db.add_all([msg1, msg2])
    test_db.commit()

    # Query back conversation with messages
    retrieved = (
        test_db.query(Conversation)
        .filter_by(id=conversation.id)
        .first()
    )
    assert retrieved is not None
    assert len(retrieved.messages) == 2
    assert retrieved.messages[0].role == "user"
    assert retrieved.messages[1].role == "assistant"


def test_create_conversation_with_documents(test_db: Session):
    """Test creating a conversation with documents."""
    # Create conversation
    conversation = Conversation(title="Study Session")
    test_db.add(conversation)
    test_db.commit()
    test_db.refresh(conversation)

    # Add documents
    doc1 = Document(
        conversation_id=conversation.id,
        file_name="lecture.pdf",
        file_path="/uploads/lecture.pdf",
        file_type="pdf",
        file_size=2048,
        extracted_text="This is a lecture about...",
    )
    doc2 = Document(
        conversation_id=conversation.id,
        file_name="notes.txt",
        file_path="/uploads/notes.txt",
        file_type="txt",
        file_size=512,
        extracted_text="My study notes...",
    )
    test_db.add_all([doc1, doc2])
    test_db.commit()

    # Query back
    retrieved = (
        test_db.query(Conversation)
        .filter_by(id=conversation.id)
        .first()
    )
    assert retrieved is not None
    assert len(retrieved.documents) == 2
    assert retrieved.documents[0].file_type == "pdf"
    assert retrieved.documents[1].file_type == "txt"


def test_create_summary(test_db: Session):
    """Test creating a summary for a conversation."""
    # Create conversation
    conversation = Conversation(title="Discussion")
    test_db.add(conversation)
    test_db.commit()
    test_db.refresh(conversation)

    # Add summary
    summary = Summary(
        conversation_id=conversation.id,
        summary_text="This conversation discussed AI and machine learning topics.",
        audio_url="/uploads/summary.mp3",
        audio_duration=180,
        voice="alloy",
    )
    test_db.add(summary)
    test_db.commit()

    # Query back
    retrieved = (
        test_db.query(Conversation)
        .filter_by(id=conversation.id)
        .first()
    )
    assert retrieved is not None
    assert len(retrieved.summaries) == 1
    assert retrieved.summaries[0].audio_duration == 180


def test_cascade_delete(test_db: Session):
    """Test that deleting a conversation cascades to messages and documents."""
    # Create conversation with messages and documents
    conversation = Conversation(title="Test Cascade")
    test_db.add(conversation)
    test_db.commit()
    test_db.refresh(conversation)

    message = Message(
        conversation_id=conversation.id,
        role="user",
        content="Test message",
    )
    document = Document(
        conversation_id=conversation.id,
        file_name="test.pdf",
        file_path="/uploads/test.pdf",
        file_type="pdf",
    )
    test_db.add_all([message, document])
    test_db.commit()

    # Verify they exist
    assert test_db.query(Message).count() == 1
    assert test_db.query(Document).count() == 1

    # Delete conversation
    test_db.delete(conversation)
    test_db.commit()

    # Verify cascade delete worked
    assert test_db.query(Conversation).count() == 0
    assert test_db.query(Message).count() == 0
    assert test_db.query(Document).count() == 0


def test_update_conversation(test_db: Session):
    """Test updating a conversation."""
    # Create conversation
    conversation = Conversation(title="Original Title")
    test_db.add(conversation)
    test_db.commit()
    test_db.refresh(conversation)

    # Update title
    conversation.title = "Updated Title"
    test_db.commit()
    test_db.refresh(conversation)

    # Verify update
    retrieved = test_db.query(Conversation).filter_by(id=conversation.id).first()
    assert retrieved is not None
    assert retrieved.title == "Updated Title"


def test_query_messages_by_conversation(test_db: Session):
    """Test querying messages by conversation ID."""
    # Create two conversations
    conv1 = Conversation(title="Conversation 1")
    conv2 = Conversation(title="Conversation 2")
    test_db.add_all([conv1, conv2])
    test_db.commit()
    test_db.refresh(conv1)
    test_db.refresh(conv2)

    # Add messages to each
    msg1 = Message(conversation_id=conv1.id, role="user", content="Message 1")
    msg2 = Message(conversation_id=conv1.id, role="assistant", content="Message 2")
    msg3 = Message(conversation_id=conv2.id, role="user", content="Message 3")
    test_db.add_all([msg1, msg2, msg3])
    test_db.commit()

    # Query messages for conv1
    conv1_messages = (
        test_db.query(Message)
        .filter_by(conversation_id=conv1.id)
        .order_by(Message.created_at)
        .all()
    )
    assert len(conv1_messages) == 2
    assert conv1_messages[0].content == "Message 1"
    assert conv1_messages[1].content == "Message 2"

    # Query messages for conv2
    conv2_messages = test_db.query(Message).filter_by(conversation_id=conv2.id).all()
    assert len(conv2_messages) == 1
    assert conv2_messages[0].content == "Message 3"
