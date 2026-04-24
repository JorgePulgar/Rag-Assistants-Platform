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
1. GROUND IN THE CONTEXT: Your answers must be grounded in the CONTEXT section and the conversation HISTORY. You are encouraged to:
   - Elaborate on concepts present in the CONTEXT with more detail, synonyms, or clearer phrasing.
   - Generate ILLUSTRATIVE EXAMPLES that apply the concepts in the CONTEXT to new everyday situations. Examples do not need to be verbatim from the documents — what matters is that they correctly apply a concept that IS in the CONTEXT.
   - Build on what you previously said in the HISTORY when the user asks to expand, reformulate, or summarise.
   What you must NOT do: introduce factual claims, figures, legal provisions, or domain knowledge that are absent from the CONTEXT. If the user's request requires information genuinely outside the CONTEXT and HISTORY, apply Rule 2.
2. STRICT FALLBACK: If the information is not in the context, respond EXACTLY with:
   "I don't have enough information in my documents to answer this question. What I looked for: [brief summary]. Suggestion: [suggest a different keyword or angle to search]."
   Do not use outside knowledge to generate the suggestion.
3. CITATION FORMAT: You MUST cite sources immediately after the relevant claim, before the period.
   - Format strictly as [CITE:chunk_id].
   - Do NOT combine citations. (WRONG: [CITE:id1, id2]. RIGHT: [CITE:id1][CITE:id2]).
   - Never hallucinate chunk IDs — only cite IDs actually present in the CONTEXT.
4. CONTRADICTIONS: If chunks contain conflicting information, objectively state both versions, citing the respective sources for each. Do not attempt to guess which one is correct.
5. TONE & STYLE: Be concise, direct, and professional. Do not repeat the user's question or use filler introductions.
6. LANGUAGE: Always respond in the same language as the user's prompt, even if the CONTEXT documents are in a different language.
7. ELABORATION MODES: When the user asks for more information on something already discussed, identify which mode applies:
   - EXPAND: user wants more depth on an existing concept → use the same CONTEXT with more detail, unpacking terms, explaining implications.
   - REPHRASE: user wants the same content said differently → reformulate with synonyms, simpler language, or a different angle.
   - EXEMPLIFY: user wants more examples → generate new illustrative examples based on the concepts in the CONTEXT.
   - COMPARE: user wants contrast with something else discussed → use the HISTORY to recall what was said and relate them.
   In all four modes, Rule 1 still applies: stay grounded, no external facts.
"""

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
    # IGNORECASE: the LLM occasionally upper-cases the UUID hex digits even though
    # ingestion always stores them lower-case (str(uuid.uuid4())).
    pattern = re.compile(r"\[CITE:([a-f0-9-]+)\]", re.IGNORECASE)

    cited_ids: list[str] = []
    seen: set[str] = set()
    for match in pattern.finditer(llm_response):
        cid = match.group(1).lower()
        if cid not in seen and cid in chunk_by_id:
            cited_ids.append(cid)
            seen.add(cid)

    content = llm_response
    citations: list[dict[str, Any]] = []
    for i, cid in enumerate(cited_ids, start=1):
        content = re.sub(r"\[CITE:" + re.escape(cid) + r"\]", f"[{i}]", content, flags=re.IGNORECASE)
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
    rewriting_ran = settings.query_rewriting_enabled and bool(history)
    if rewriting_ran:
        rewrite_history = history[-settings.query_rewriting_history_n :]
        search_query = query_rewriter.rewrite_query(rewrite_history, user_message_content)

    # No-search intent: the rewriter returned the message unchanged AND it is short
    # enough to be chit-chat / greeting / formatting instruction rather than a real
    # search query. Skip retrieval and let the LLM answer from history alone.
    if rewriting_ran and search_query == user_message_content and len(user_message_content.split()) <= 10:
        logger.info(
            "No-search intent detected for conversation %s — skipping retrieval",
            conversation_id,
        )
        system_prompt = assistant.instructions + _BEHAVIOUR_RULES
        no_search_messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
        for msg in history:
            no_search_messages.append({"role": msg.role, "content": msg.content})
        no_search_messages.append({"role": "user", "content": user_message_content})
        raw_response = azure_openai.call_llm(no_search_messages)
        return {"content": raw_response, "citations": []}

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
