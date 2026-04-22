from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DocumentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    assistant_id: str
    filename: str
    mime_type: str | None
    size_bytes: int | None
    chunk_count: int | None
    status: str
    error_message: str | None
    uploaded_at: datetime
