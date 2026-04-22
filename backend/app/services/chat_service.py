import logging
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.exceptions import AssistantNotFoundError, ConversationNotFoundError
from app.models.assistant import Assistant
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.chat import (
    ConversationCreate,
    ConversationRead,
    MessageCreate,
    MessageRead,
    SendMessageResponse,
)
from app.services import rag

logger = logging.getLogger(__name__)


def create_conversation(db: Session, data: ConversationCreate) -> ConversationRead:
    """Create a new conversation for an assistant."""
    assistant = db.get(Assistant, data.assistant_id)
    if assistant is None:
        raise AssistantNotFoundError(data.assistant_id)

    now = datetime.now(timezone.utc)
    conversation = Conversation(
        id=str(uuid.uuid4()),
        assistant_id=data.assistant_id,
        title=f"Conversation {now.strftime('%Y-%m-%d %H:%M')}",
        created_at=now,
        updated_at=now,
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return ConversationRead.model_validate(conversation)


def list_conversations(db: Session, assistant_id: str) -> list[ConversationRead]:
    """Return all conversations for an assistant, newest first."""
    assistant = db.get(Assistant, assistant_id)
    if assistant is None:
        raise AssistantNotFoundError(assistant_id)

    rows = (
        db.query(Conversation)
        .filter(Conversation.assistant_id == assistant_id)
        .order_by(Conversation.updated_at.desc())
        .all()
    )
    return [ConversationRead.model_validate(c) for c in rows]


def get_messages(db: Session, conversation_id: str) -> list[MessageRead]:
    """Return all messages in a conversation in chronological order."""
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise ConversationNotFoundError(conversation_id)

    messages = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [MessageRead.model_validate(m) for m in messages]


def send_message(db: Session, conversation_id: str, data: MessageCreate) -> SendMessageResponse:
    """Run RAG for the user turn, persist both messages, return the assistant response.

    The user message is persisted AFTER generate_response so that the history
    loaded inside that call contains only prior turns — not the current one,
    which is injected separately as the last message in the LLM prompt.
    """
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise ConversationNotFoundError(conversation_id)

    assistant = db.get(Assistant, conversation.assistant_id)
    if assistant is None:
        raise AssistantNotFoundError(conversation.assistant_id)

    result = rag.generate_response(db, assistant, conversation_id, data.content)

    now = datetime.now(timezone.utc)

    user_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role="user",
        content=data.content,
        citations=None,
        created_at=now,
    )
    db.add(user_msg)

    assistant_msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role="assistant",
        content=result["content"],
        citations=result["citations"],
        created_at=now,
    )
    db.add(assistant_msg)

    conversation.updated_at = now
    db.commit()
    db.refresh(assistant_msg)

    return SendMessageResponse(message=MessageRead.model_validate(assistant_msg))


def delete_conversation(db: Session, conversation_id: str) -> None:
    """Delete a conversation and cascade-delete all its messages."""
    conversation = db.get(Conversation, conversation_id)
    if conversation is None:
        raise ConversationNotFoundError(conversation_id)
    db.delete(conversation)
    db.commit()
