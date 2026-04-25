import logging
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.exceptions import IngestionError
from app.models.document import Document
from app.schemas.document import DocumentRead
from app.services import document_service, ingestion

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/assistants", tags=["documents"])

_MAX_FILE_BYTES = 10 * 1024 * 1024  # 10 MB


@router.post(
    "/{assistant_id}/documents",
    response_model=DocumentRead,
    status_code=201,
)
async def upload_document(
    assistant_id: str,
    file: UploadFile,
    db: Session = Depends(get_db),
) -> DocumentRead:
    content = await file.read()
    filename = file.filename or "upload"

    if len(content) > _MAX_FILE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum allowed size is {_MAX_FILE_BYTES // (1024 * 1024)} MB.",
        )

    if len(content) == 0:
        raise HTTPException(status_code=422, detail="Uploaded file is empty.")

    doc_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    document = Document(
        id=doc_id,
        assistant_id=assistant_id,
        filename=filename,
        mime_type=file.content_type,
        size_bytes=len(content),
        status="pending",
        uploaded_at=now,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    suffix = Path(filename).suffix or ".tmp"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    try:
        ingestion.index_document(db, doc_id, tmp_path)
    except IngestionError:
        pass  # status already set to "failed" in ingestion service
    finally:
        Path(tmp_path).unlink(missing_ok=True)

    db.refresh(document)
    return DocumentRead.model_validate(document)


@router.get("/{assistant_id}/documents", response_model=list[DocumentRead])
def list_documents(
    assistant_id: str,
    db: Session = Depends(get_db),
) -> list[DocumentRead]:
    return document_service.list_documents(db, assistant_id)


@router.delete("/{assistant_id}/documents/{document_id}", status_code=204)
def delete_document(
    assistant_id: str,
    document_id: str,
    db: Session = Depends(get_db),
) -> None:
    document_service.delete_document(db, assistant_id, document_id)
