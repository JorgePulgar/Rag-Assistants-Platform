"""RAG prompt construction tests (T030).

Three cases from RAG_SPEC / CONSTITUTION:
  1. With context  — LLM is called; prompt contains system + history + context block.
  2. Without context — LLM is NOT called; hardcoded no-context message returned.
  3. Long history   — LLM call contains at most HISTORY_MAX_MESSAGES prior turns.
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — registers all models with Base
from app.config import settings
from app.db import Base
from app.models.assistant import Assistant
from app.models.conversation import Conversation
from app.models.message import Message
from app.services import rag


def _make_db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _record) -> None:  # type: ignore[no-untyped-def]
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    return Session()


def _assistant(db, instructions: str = "You are a helpful assistant.") -> Assistant:
    a = Assistant(
        id=str(uuid.uuid4()),
        name="Test Assistant",
        instructions=instructions,
        description=None,
        search_index=f"test-idx-{uuid.uuid4().hex[:8]}",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(a)
    db.commit()
    return a


def _conversation(db, assistant_id: str) -> Conversation:
    c = Conversation(
        id=str(uuid.uuid4()),
        assistant_id=assistant_id,
        title="Test",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(c)
    db.commit()
    return c


def _add_message(db, conversation_id: str, role: str, content: str) -> None:
    db.add(
        Message(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            role=role,
            content=content,
            citations=None,
            created_at=datetime.now(timezone.utc),
        )
    )
    db.commit()


def _chunk(chunk_id: str | None = None) -> dict:
    return {
        "chunk_id": chunk_id or str(uuid.uuid4()),
        "document_id": str(uuid.uuid4()),
        "document_name": "test_doc.pdf",
        "page": 1,
        "text": "Some relevant content from the document.",
        "@search.reranker_score": 2.5,
    }


# ── Case 1: with context ───────────────────────────────────────────────────────

def test_with_context_calls_llm_and_includes_all_prompt_sections():
    """LLM receives system + history + context block; citations are resolved."""
    db = _make_db()
    assistant = _assistant(db)
    conv = _conversation(db, assistant.id)

    _add_message(db, conv.id, "user", "What is clause 3?")
    _add_message(db, conv.id, "assistant", "Clause 3 deals with termination.")

    chunk = _chunk()
    captured: list[list[dict]] = []

    def fake_llm(messages: list[dict]) -> str:
        captured.append(messages)
        return f"The answer is here [CITE:{chunk['chunk_id']}]."

    with (
        patch("app.services.rag.retrieve", return_value=[chunk]),
        # Rewriter returns an enriched query (different from original) so the no-search-intent
        # heuristic does not fire and the test reaches the retrieval + LLM path.
        patch("app.services.rag.query_rewriter.rewrite_query", return_value="What does clause 4 of the contract say about obligations?"),
        patch("app.clients.azure_openai.call_llm", side_effect=fake_llm),
    ):
        result = rag.generate_response(db, assistant, conv.id, "Tell me about clause 4.")

    assert captured, "LLM was not called"
    messages = captured[0]

    # System prompt: assistant instructions + BEHAVIOUR RULES
    assert messages[0]["role"] == "system"
    assert assistant.instructions in messages[0]["content"]
    assert "BEHAVIOUR RULES" in messages[0]["content"]

    # History preserves roles
    history_roles = [m["role"] for m in messages[1:-1]]
    assert "user" in history_roles
    assert "assistant" in history_roles

    # Last message contains context block and current question
    last = messages[-1]
    assert last["role"] == "user"
    assert "RETRIEVED CONTEXT" in last["content"]
    assert "Tell me about clause 4." in last["content"]
    assert chunk["chunk_id"] in last["content"]

    # Citations are resolved to structured objects
    assert len(result["citations"]) == 1
    assert result["citations"][0]["document_name"] == chunk["document_name"]
    assert result["citations"][0]["page"] == chunk["page"]
    assert "[1]" in result["content"]


# ── Case 2: without context — LLM must NOT be called ─────────────────────────

def test_without_context_skips_llm_and_returns_hardcoded_message():
    """When retrieval is empty the LLM is never invoked and citations are []."""
    db = _make_db()
    assistant = _assistant(db)
    conv = _conversation(db, assistant.id)

    llm_called = False

    def fail_if_called(messages: list[dict]) -> str:
        nonlocal llm_called
        llm_called = True
        return "Should not reach here"

    with (
        patch("app.services.rag.retrieve", return_value=[]),
        patch("app.clients.azure_openai.call_llm", side_effect=fail_if_called),
    ):
        result = rag.generate_response(db, assistant, conv.id, "What is X?")

    assert not llm_called, "LLM was called despite empty retrieval result"
    assert result["citations"] == []
    assert "did not find" in result["content"].lower()


# ── Case 3: long history trimmed to HISTORY_MAX_MESSAGES ─────────────────────

def test_long_history_is_trimmed_to_max():
    """History injected into the LLM prompt must not exceed HISTORY_MAX_MESSAGES."""
    db = _make_db()
    assistant = _assistant(db)
    conv = _conversation(db, assistant.id)

    excess = settings.history_max_messages + 6
    for i in range(excess):
        _add_message(db, conv.id, "user" if i % 2 == 0 else "assistant", f"Message {i}")

    chunk = _chunk()
    captured: list[list[dict]] = []

    def fake_llm(messages: list[dict]) -> str:
        captured.append(messages)
        return "Answer."

    with (
        patch("app.services.rag.retrieve", return_value=[chunk]),
        patch("app.clients.azure_openai.call_llm", side_effect=fake_llm),
    ):
        rag.generate_response(db, assistant, conv.id, "Latest question.")

    assert captured, "LLM was not called"
    messages = captured[0]
    # messages = [system] + [history…] + [context/user]
    history_count = len(messages) - 2
    assert history_count <= settings.history_max_messages, (
        f"History not trimmed: {history_count} message(s) sent to LLM "
        f"(cap is {settings.history_max_messages})"
    )


# ── _post_process citation rendering (T047k) ──────────────────────────────────

def test_post_process_single_citation():
    """Single [CITE:id] marker is replaced with [1] and a citation object is built."""
    cid = str(uuid.uuid4())
    chunk = {
        "chunk_id": cid,
        "document_id": str(uuid.uuid4()),
        "document_name": "doc.pdf",
        "page": 3,
        "text": "Relevant excerpt from page 3.",
    }
    content, citations = rag._post_process(f"The answer is here [CITE:{cid}].", [chunk])

    assert "[1]" in content
    assert f"[CITE:{cid}]" not in content
    assert len(citations) == 1
    assert citations[0]["document_name"] == "doc.pdf"
    assert citations[0]["page"] == 3


def test_post_process_consecutive_citations():
    """Two consecutive [CITE:id1][CITE:id2] markers are each replaced with [1] and [2]."""
    cid1 = str(uuid.uuid4())
    cid2 = str(uuid.uuid4())
    chunks = [
        {"chunk_id": cid1, "document_id": str(uuid.uuid4()), "document_name": "a.pdf", "page": 1, "text": "A"},
        {"chunk_id": cid2, "document_id": str(uuid.uuid4()), "document_name": "b.pdf", "page": 2, "text": "B"},
    ]
    llm_text = f"First claim [CITE:{cid1}][CITE:{cid2}] second claim."
    content, citations = rag._post_process(llm_text, chunks)

    assert "[1]" in content
    assert "[2]" in content
    assert f"[CITE:{cid1}]" not in content
    assert f"[CITE:{cid2}]" not in content
    assert len(citations) == 2
    assert citations[0]["document_name"] == "a.pdf"
    assert citations[1]["document_name"] == "b.pdf"


def test_post_process_citation_at_end_of_sentence():
    """[CITE:id] at the end of a sentence (before nothing / after period) is replaced."""
    cid = str(uuid.uuid4())
    chunk = {"chunk_id": cid, "document_id": str(uuid.uuid4()), "document_name": "c.pdf", "page": 5, "text": "C"}
    content, citations = rag._post_process(f"The contract terminates after 30 days [CITE:{cid}]", [chunk])

    assert content.endswith("[1]")
    assert len(citations) == 1


def test_post_process_case_insensitive_citation():
    """[CITE:ID] with uppercase hex is still matched and replaced (LLM may upper-case UUIDs)."""
    cid_lower = str(uuid.uuid4())
    cid_upper = cid_lower.upper()
    chunk = {"chunk_id": cid_lower, "document_id": str(uuid.uuid4()), "document_name": "d.pdf", "page": 1, "text": "D"}
    content, citations = rag._post_process(f"Answer [CITE:{cid_upper}].", [chunk])

    assert "[1]" in content
    assert len(citations) == 1


def test_post_process_unknown_chunk_id_is_stripped(caplog):
    """[CITE:id] whose chunk_id is not in the retrieved set must be stripped, not left literal.

    Residual artefacts like "[CITE:12][1]" occur when the LLM references an ID
    from a prior turn that is no longer in the current retrieval result (T055b).
    """
    import logging

    known_cid = str(uuid.uuid4())
    unknown_cid = str(uuid.uuid4())
    chunk = {
        "chunk_id": known_cid,
        "document_id": str(uuid.uuid4()),
        "document_name": "e.pdf",
        "page": 2,
        "text": "Known content.",
    }
    llm_text = f"Valid claim [CITE:{known_cid}] and hallucinated [CITE:{unknown_cid}]."

    with caplog.at_level(logging.INFO, logger="app.services.rag"):
        content, citations = rag._post_process(llm_text, [chunk])

    # Known citation is replaced with [1]
    assert "[1]" in content
    assert f"[CITE:{known_cid}]" not in content

    # Unknown citation is stripped entirely — no literal [CITE:...] text remains
    assert f"[CITE:{unknown_cid}]" not in content
    assert "[CITE:" not in content

    # Exactly one citation object is built
    assert len(citations) == 1
    assert citations[0]["document_name"] == "e.pdf"

    # The anomaly is logged
    assert unknown_cid in caplog.text
