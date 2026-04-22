from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.assistant import AssistantCreate, AssistantRead, AssistantUpdate
from app.services import assistant_service

router = APIRouter(prefix="/api/assistants", tags=["assistants"])


@router.post("", response_model=AssistantRead, status_code=status.HTTP_201_CREATED)
def create_assistant(data: AssistantCreate, db: Session = Depends(get_db)) -> AssistantRead:
    return assistant_service.create_assistant(db, data)


@router.get("", response_model=list[AssistantRead])
def list_assistants(db: Session = Depends(get_db)) -> list[AssistantRead]:
    return assistant_service.list_assistants(db)


@router.get("/{assistant_id}", response_model=AssistantRead)
def get_assistant(assistant_id: str, db: Session = Depends(get_db)) -> AssistantRead:
    return assistant_service.get_assistant(db, assistant_id)


@router.patch("/{assistant_id}", response_model=AssistantRead)
def update_assistant(
    assistant_id: str, data: AssistantUpdate, db: Session = Depends(get_db)
) -> AssistantRead:
    return assistant_service.update_assistant(db, assistant_id, data)


@router.delete("/{assistant_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_assistant(assistant_id: str, db: Session = Depends(get_db)) -> None:
    assistant_service.delete_assistant(db, assistant_id)
