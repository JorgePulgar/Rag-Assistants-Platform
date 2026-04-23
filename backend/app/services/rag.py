import logging
import re
from typing import Any

from sqlalchemy.orm import Session

from app.clients import azure_openai
from app.config import settings
from app.models.assistant import Assistant
from app.models.message import Message
from app.services import query_rewriter
from app.services.retrieval import retrieve

logger = logging.getLogger(__name__)

_BEHAVIOUR_RULES = """

BEHAVIOUR RULES:
1. Respond ONLY with information present in the documents provided in the CONTEXT section. Do not use general knowledge.
2. If the information is not in the context, respond exactly with: "I don't have enough information in my documents to answer this question. What I looked for: [brief summary]. Suggestion: [sensible next step]."
3. Cite sources using the inline format [CITE:chunk_id], where chunk_id is the identifier of the chunk that supports the statement.
4. Be concise and direct. Do not repeat the user's question.
5. If chunks contain contradictory information, mention both versions with their citations."""

_NO_CONTEXT_RESPONSE = (
    "I did not find relevant information in this assistant's documents to answer your question. "
    "Suggestion: rephrase the question or upload related documents to this assistant."
)


def _build_context_block(chunks: list[dict[str, Any]], user_message: str) -> str:
    lines: list[str] = ["RETRIEVED CONTEXT:\n"]
    for chunk in chunks:
        page = chunk.get("page")
        page_str = f" | Page: {page}" if page is not None else ""
        lines.append(f"[CITE:{chunk['chunk_id']}]")
        lines.append(f"Document: {chunk['document_name']}{page_str}")
        lines.append(f"Content: {chunk['text']}\n")
    lines.append(f"USER QUESTION: {user_message}")
    return "\n".join(lines)


def _post_process(
    llm_response: str, chunks: list[dict[str, Any]]
) -> tuple[str, list[dict[str, Any]]]:
    """Replace [CITE:id] markers with sequential [N] labels; build structured citations."""
    chunk_by_id = {c["chunk_id"]: c for c in chunks}
    pattern = re.compile(r"\[CITE:([a-f0-9-]+)\]")

    cited_ids: list[str] = []
    seen: set[str] = set()
    for match in pattern.finditer(llm_response):
        cid = match.group(1)
        if cid not in seen and cid in chunk_by_id:
            cited_ids.append(cid)
            seen.add(cid)

    content = llm_response
    citations: list[dict[str, Any]] = []
    for i, cid in enumerate(cited_ids, start=1):
        content = content.replace(f"[CITE:{cid}]", f"[{i}]")
        chunk = chunk_by_id[cid]
        citations.append(
            {
                "document_id": chunk["document_id"],
                "document_name": chunk["document_name"],
                "page": chunk.get("page"),
                "chunk_text": chunk["text"][:300],
            }
        )

    return content, citations


def generate_response(
    db: Session,
    assistant: Assistant,
    conversation_id: str,
    user_message_content: str,
) -> dict[str, Any]:
    """Run the full RAG pipeline for one user turn.

    History is loaded from SQLite so memory persists across sessions. The
    current user message is passed explicitly and must NOT be persisted to
    the database before this call — doing so would double it in the prompt.

    Args:
        db: SQLAlchemy session (read-only use: load conversation history).
        assistant: the SQLAlchemy Assistant model instance.
        conversation_id: ID of the conversation being continued.
        user_message_content: the current user question (not yet in the DB).

    Returns:
        Dict with "content" (str) and "citations" (list[dict]).
    """
    # Load history first: needed for query rewriting and for the LLM prompt.
    # .desc() + .limit() gives the most recent N; .reverse() restores chronological order.
    history = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.desc())
        .limit(settings.history_max_messages)
        .all()
    )
    history.reverse()

    # Query rewriting: when there is prior history, produce a standalone search
    # query so that referential follow-ups ("tell me more about point 2") embed
    # with topical signal rather than the raw short phrase.
    search_query = user_message_content
    if settings.query_rewriting_enabled and history:
        rewrite_history = history[-settings.query_rewriting_history_n :]
        search_query = query_rewriter.rewrite_query(rewrite_history, user_message_content)

    chunks = retrieve(assistant.search_index, search_query)

    if not chunks:
        logger.info(
            "No chunks above threshold for conversation %s — returning hardcoded no-context response",
            conversation_id,
        )
        return {"content": _NO_CONTEXT_RESPONSE, "citations": []}

    system_prompt = assistant.instructions + _BEHAVIOUR_RULES
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})

    # Context block uses the original user message (rewriting is an internal retrieval concern).
    context_block = _build_context_block(chunks, user_message_content)
    messages.append({"role": "user", "content": context_block})

    logger.info(
        "Calling LLM for conversation %s: %d history message(s), %d chunk(s)",
        conversation_id,
        len(history),
        len(chunks),
    )
    raw_response = azure_openai.call_llm(messages)
    content, citations = _post_process(raw_response, chunks)

    return {"content": content, "citations": citations}
