from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CitationObject(BaseModel):
    document_id: str
    document_name: str
    page: int | None
    chunk_text: str


class ConversationCreate(BaseModel):
    assistant_id: str


class ConversationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    assistant_id: str
    title: str
    created_at: datetime
    updated_at: datetime


class MessageCreate(BaseModel):
    content: str = Field(..., min_length=1, max_length=20_000)


class MessageRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    conversation_id: str
    role: str
    content: str
    citations: list[CitationObject] | None
    created_at: datetime


class SendMessageResponse(BaseModel):
    message: MessageRead
