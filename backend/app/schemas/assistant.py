from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AssistantCreate(BaseModel):
    name: str = Field(..., max_length=200)
    instructions: str
    description: str | None = None


class AssistantUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    instructions: str | None = None
    description: str | None = None


class AssistantRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    instructions: str
    description: str | None
    search_index: str
    created_at: datetime
    updated_at: datetime
