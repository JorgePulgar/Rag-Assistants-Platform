import re
import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.exceptions import AssistantNotFoundError
from app.models.assistant import Assistant
from app.schemas.assistant import AssistantCreate, AssistantRead, AssistantUpdate

_INDEX_NAME_RE = re.compile(r"^[a-z0-9-]{2,128}$")


def _make_search_index(assistant_id: str) -> str:
    """Derive the Azure AI Search index name from the assistant UUID.

    Format: assistant-{32 hex chars with no dashes}.
    Always satisfies ^[a-z0-9-]{2,128}$.
    """
    hex_id = assistant_id.replace("-", "")
    return f"assistant-{hex_id}"


def create_assistant(db: Session, data: AssistantCreate) -> AssistantRead:
    assistant_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    assistant = Assistant(
        id=assistant_id,
        name=data.name,
        instructions=data.instructions,
        description=data.description,
        search_index=_make_search_index(assistant_id),
        created_at=now,
        updated_at=now,
    )
    db.add(assistant)
    db.commit()
    db.refresh(assistant)
    return AssistantRead.model_validate(assistant)


def list_assistants(db: Session) -> list[AssistantRead]:
    rows = db.query(Assistant).order_by(Assistant.created_at.desc()).all()
    return [AssistantRead.model_validate(a) for a in rows]


def get_assistant(db: Session, assistant_id: str) -> AssistantRead:
    assistant = db.get(Assistant, assistant_id)
    if assistant is None:
        raise AssistantNotFoundError(assistant_id)
    return AssistantRead.model_validate(assistant)


def update_assistant(db: Session, assistant_id: str, data: AssistantUpdate) -> AssistantRead:
    assistant = db.get(Assistant, assistant_id)
    if assistant is None:
        raise AssistantNotFoundError(assistant_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(assistant, field, value)
    assistant.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(assistant)
    return AssistantRead.model_validate(assistant)


def delete_assistant(db: Session, assistant_id: str) -> None:
    assistant = db.get(Assistant, assistant_id)
    if assistant is None:
        raise AssistantNotFoundError(assistant_id)
    db.delete(assistant)
    db.commit()
