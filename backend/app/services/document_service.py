import logging

from sqlalchemy.orm import Session

from app.clients import azure_search
from app.exceptions import AssistantNotFoundError, DocumentNotFoundError
from app.models.assistant import Assistant
from app.models.document import Document
from app.schemas.document import DocumentRead

logger = logging.getLogger(__name__)


def list_documents(db: Session, assistant_id: str) -> list[DocumentRead]:
    assistant = db.get(Assistant, assistant_id)
    if assistant is None:
        raise AssistantNotFoundError(assistant_id)
    rows = (
        db.query(Document)
        .filter(Document.assistant_id == assistant_id)
        .order_by(Document.uploaded_at.desc())
        .all()
    )
    return [DocumentRead.model_validate(d) for d in rows]


def delete_document(db: Session, assistant_id: str, document_id: str) -> None:
    document = db.get(Document, document_id)
    if document is None or document.assistant_id != assistant_id:
        raise DocumentNotFoundError(document_id)

    assistant = db.get(Assistant, assistant_id)
    if assistant and document.status == "indexed":
        try:
            azure_search.delete_documents_by_document_id(assistant.search_index, document_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                "Could not remove chunks for document %s from %s: %s",
                document_id,
                assistant.search_index,
                exc,
            )

    db.delete(document)
    db.commit()
