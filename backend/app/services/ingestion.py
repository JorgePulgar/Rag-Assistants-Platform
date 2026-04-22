import logging
import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from app.clients import azure_openai, azure_search
from app.config import settings
from app.exceptions import IngestionError
from app.models.assistant import Assistant
from app.models.document import Document
from app.services.parsers import resolve_parser

logger = logging.getLogger(__name__)

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.chunk_size,
    chunk_overlap=settings.chunk_overlap,
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len,
)


def index_document(db: Session, document_id: str, file_path: str) -> None:
    """Full ingestion pipeline: parse → chunk → embed → index.

    Updates document.status to 'indexed' or 'failed' in-place.
    Always commits the status change before returning or raising.
    """
    document = db.get(Document, document_id)
    if document is None:
        raise IngestionError(f"Document {document_id} not found")

    assistant = db.get(Assistant, document.assistant_id)
    if assistant is None:
        raise IngestionError(f"Assistant {document.assistant_id} not found")

    try:
        # 1. Parse — returns page/section units (raw text, not yet split)
        parser = resolve_parser(document.filename)
        parsed_units = parser(file_path)

        if not parsed_units:
            raise IngestionError("No text could be extracted from the document")

        # 2. Chunk (splitter runs per page/section unit to preserve page attribution)
        all_chunks: list[dict] = []
        chunk_index = 0
        for unit in parsed_units:
            sub_texts = _splitter.split_text(unit.text)
            for sub_text in sub_texts:
                all_chunks.append(
                    {
                        "chunk_id": str(uuid.uuid4()),
                        "document_id": document.id,
                        "document_name": document.filename,
                        "page": unit.page,
                        "section": unit.section,
                        "text": sub_text,
                        "chunk_index": chunk_index,
                    }
                )
                chunk_index += 1

        if not all_chunks:
            raise IngestionError("Chunking produced zero chunks")

        # 3. Embed in batches of 16
        texts = [c["text"] for c in all_chunks]
        embeddings = azure_openai.embed_texts(texts)
        for chunk, embedding in zip(all_chunks, embeddings):
            chunk["vector"] = embedding

        # 4. Create the per-assistant index if this is the first document
        azure_search.create_index_if_not_exists(assistant.search_index)

        # 5. Upload chunks
        azure_search.upload_documents(assistant.search_index, all_chunks)

        # 6. Mark indexed
        document.chunk_count = len(all_chunks)
        document.status = "indexed"
        db.commit()

        logger.info(
            "Indexed document %s (%s): %d chunks → %s",
            document.id,
            document.filename,
            len(all_chunks),
            assistant.search_index,
        )

    except Exception as exc:
        logger.error("Ingestion failed for document %s: %s", document_id, exc)
        document.status = "failed"
        document.error_message = str(exc)[:500]
        db.commit()
        if not isinstance(exc, IngestionError):
            raise IngestionError(str(exc)) from exc
        raise
