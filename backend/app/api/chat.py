from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.chat import (
    ConversationCreate,
    ConversationRead,
    MessageCreate,
    MessageRead,
    SendMessageResponse,
)
from app.services import chat_service

router = APIRouter(tags=["chat"])


@router.post(
    "/api/conversations",
    response_model=ConversationRead,
    status_code=status.HTTP_201_CREATED,
)
def create_conversation(
    data: ConversationCreate, db: Session = Depends(get_db)
) -> ConversationRead:
    return chat_service.create_conversation(db, data)


@router.get(
    "/api/assistants/{assistant_id}/conversations",
    response_model=list[ConversationRead],
)
def list_conversations(
    assistant_id: str, db: Session = Depends(get_db)
) -> list[ConversationRead]:
    return chat_service.list_conversations(db, assistant_id)


@router.get(
    "/api/conversations/{conversation_id}/messages",
    response_model=list[MessageRead],
)
def get_messages(
    conversation_id: str, db: Session = Depends(get_db)
) -> list[MessageRead]:
    return chat_service.get_messages(db, conversation_id)


@router.post(
    "/api/conversations/{conversation_id}/messages",
    response_model=SendMessageResponse,
)
def send_message(
    conversation_id: str, data: MessageCreate, db: Session = Depends(get_db)
) -> SendMessageResponse:
    return chat_service.send_message(db, conversation_id, data)


@router.delete(
    "/api/conversations/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_conversation(
    conversation_id: str, db: Session = Depends(get_db)
) -> None:
    chat_service.delete_conversation(db, conversation_id)
