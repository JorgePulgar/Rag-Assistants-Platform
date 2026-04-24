"""Tests for conversational memory behaviour (T047e / T033 audit / T047l).

test_query_rewriting_resolves_referential_followup
    Regression for Bug 2: a referential follow-up ("tell me more about point 2")
    must be rewritten into a topically enriched query before retrieval, not passed
    raw.  Verifies that retrieve() is called with the rewritten query and that the
    rewritten query carries keywords from the referenced topic (B) and not from the
    unreferenced topic (A).

test_conversation_persists_across_sessions
    Regression for T033: messages committed in one SQLAlchemy session are visible
    from a fresh session on the same engine — simulating a backend restart while
    preserving conversation history.

test_elaboration_does_not_return_no_context_response
    Regression for Rule 1 fix (T047l): asking the assistant to elaborate on a
    previous answer must not return the hardcoded no-context string.  The pipeline
    must rewrite the referential query, retrieve relevant chunks, call the LLM, and
    return a substantive response (> 100 chars).
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import patch

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — registers all models with Base
from app.db import Base
from app.models.assistant import Assistant
from app.models.conversation import Conversation
from app.models.message import Message
from app.services import rag


# ── helpers shared by both tests ──────────────────────────────────────────────

def _make_engine():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _enable_fk(dbapi_conn, _record) -> None:  # type: ignore[no-untyped-def]
        dbapi_conn.execute("PRAGMA foreign_keys=ON")

    Base.metadata.create_all(bind=engine)
    return engine


def _make_db(engine=None):
    if engine is None:
        engine = _make_engine()
    return sessionmaker(bind=engine)()


def _assistant(db) -> Assistant:  # type: ignore[no-untyped-def]
    a = Assistant(
        id=str(uuid.uuid4()),
        name="Memory Test Assistant",
        instructions="You are a helpful assistant.",
        description=None,
        search_index=f"test-mem-{uuid.uuid4().hex[:8]}",
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
        title="Memory Test",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db.add(c)
    db.commit()
    return c


def _add_message(db, conversation_id: str, role: str, content: str) -> Message:
    msg = Message(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role=role,
        content=content,
        citations=None,
        created_at=datetime.now(timezone.utc),
    )
    db.add(msg)
    db.commit()
    return msg


# ── Test 1: query rewriting resolves referential follow-ups (Bug 2) ───────────

def test_query_rewriting_resolves_referential_followup() -> None:
    """retrieve() for turn 2 must be called with the rewritten query, not the raw
    follow-up phrase 'tell me more about point 2'.

    The rewritten query must contain keywords from topic B (the referenced topic)
    and must NOT contain keywords from topic A (the unreferenced topic).
    """
    db = _make_db()
    assistant = _assistant(db)
    conv = _conversation(db, assistant.id)

    topic_a = "Procedimiento de apremio fiscal"
    topic_b = "Régimen exterior de la Unión Europea"

    # Seed turn 1: the assistant previously named both topics.
    _add_message(db, conv.id, "user", "What are the two main topics in section 2?")
    _add_message(
        db,
        conv.id,
        "assistant",
        f"Section 2 covers two topics: (1) {topic_a}, and (2) {topic_b}.",
    )

    # The rewriter enriches the follow-up with topic B context.
    rewritten_query = f"{topic_b}: obligations for non-EU entrepreneurs providing services"

    topic_b_chunk = {
        "chunk_id": str(uuid.uuid4()),
        "document_id": str(uuid.uuid4()),
        "document_name": "fiscal_guide.pdf",
        "page": 5,
        "text": f"Chapter on {topic_b}: non-EU entrepreneurs must register in the member state.",
        "@search.reranker_score": 2.8,
    }

    captured_queries: list[str] = []

    def capturing_retrieve(index_name: str, query: str) -> list[dict]:  # type: ignore[type-arg]
        captured_queries.append(query)
        return [topic_b_chunk]

    with (
        patch("app.services.rag.query_rewriter.rewrite_query", return_value=rewritten_query),
        patch("app.services.rag.retrieve", side_effect=capturing_retrieve),
        patch(
            "app.clients.azure_openai.call_llm",
            return_value=f"The {topic_b} requires [CITE:{topic_b_chunk['chunk_id']}].",
        ),
    ):
        result = rag.generate_response(db, assistant, conv.id, "tell me more about point 2")

    assert captured_queries, "retrieve() was not called"

    actual_query = captured_queries[0]
    assert actual_query == rewritten_query, (
        f"retrieve() was called with the raw user message instead of the rewritten query.\n"
        f"  Expected: {rewritten_query!r}\n"
        f"  Got:      {actual_query!r}"
    )

    # Keyword from topic B present in the rewritten query.
    topic_b_keyword = topic_b.split()[0]  # "Régimen"
    assert topic_b_keyword in actual_query, (
        f"Topic B keyword {topic_b_keyword!r} not found in rewritten query: {actual_query!r}"
    )

    # Keyword from topic A absent from the rewritten query.
    topic_a_keyword = topic_a.split()[0]  # "Procedimiento"
    assert topic_a_keyword not in actual_query, (
        f"Topic A keyword {topic_a_keyword!r} unexpectedly found in rewritten query: {actual_query!r}"
    )

    # The result cites the topic B chunk.
    assert len(result["citations"]) == 1
    assert result["citations"][0]["document_name"] == topic_b_chunk["document_name"]


# ── Test 2: conversation history persists across sessions (T033) ──────────────

def test_conversation_persists_across_sessions() -> None:
    """Messages committed in one SQLAlchemy session are visible from a new session
    on the same engine, simulating a backend restart with SQLite on disk.

    This is the persistence guarantee: memory survives restarts because messages
    live in SQLite, not in process memory.
    """
    engine = _make_engine()
    Session = sessionmaker(bind=engine)  # noqa: N806

    # Session 1: write data and close.
    db1 = Session()
    a = Assistant(
        id=str(uuid.uuid4()),
        name="Persist Test",
        instructions="You help.",
        description=None,
        search_index=f"test-persist-{uuid.uuid4().hex[:8]}",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db1.add(a)
    c = Conversation(
        id=str(uuid.uuid4()),
        assistant_id=a.id,
        title="Persist Conversation",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
    )
    db1.add(c)
    m1 = _add_message(db1, c.id, "user", "First question")
    m2 = _add_message(db1, c.id, "assistant", "First answer")
    conv_id, msg1_id, msg2_id = c.id, m1.id, m2.id
    db1.close()

    # Session 2: open a fresh session and verify the data is there.
    db2 = Session()
    loaded_conv = db2.get(Conversation, conv_id)
    assert loaded_conv is not None, "Conversation not found after session restart"
    assert loaded_conv.title == "Persist Conversation"

    messages = (
        db2.query(Message)
        .filter(Message.conversation_id == conv_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    assert len(messages) == 2, f"Expected 2 messages after restart, got {len(messages)}"
    assert messages[0].id == msg1_id
    assert messages[0].role == "user"
    assert messages[0].content == "First question"
    assert messages[1].id == msg2_id
    assert messages[1].role == "assistant"
    assert messages[1].content == "First answer"
    db2.close()


# ── Test 3: elaboration does not return the hardcoded no-context response (T047l) ──

def test_elaboration_does_not_return_no_context_response() -> None:
    """Regression for Rule 1 fix: asking the assistant to elaborate on a previous
    answer must not return the hardcoded no-context string.

    Turn 1: question that elicits a structured answer citing document content.
    Turn 2: referential elaboration request ("can you expand more on that last part?").

    Asserts:
      - The response does NOT start with the hardcoded empty-retrieval prefix.
      - The response is substantive (> 100 characters).
    """
    db = _make_db()
    assistant = _assistant(db)
    conv = _conversation(db, assistant.id)

    chunk = {
        "chunk_id": str(uuid.uuid4()),
        "document_id": str(uuid.uuid4()),
        "document_name": "process_guide.pdf",
        "page": 2,
        "text": (
            "The approval process has three steps: "
            "(1) Submit request form, (2) Wait for committee review, "
            "(3) Receive written confirmation within 10 business days."
        ),
        "@search.reranker_score": 3.0,
    }

    # Turn 1: question + structured assistant answer seeded in history.
    _add_message(db, conv.id, "user", "What are the steps in the approval process?")
    _add_message(
        db,
        conv.id,
        "assistant",
        f"The approval process has three steps: (1) Submit request form, "
        f"(2) Wait for committee review, (3) Receive written confirmation "
        f"within 10 business days. [CITE:{chunk['chunk_id']}]",
    )

    # Turn 2: elaboration on the last step.
    elaboration_query = "can you expand more on that last part?"
    rewritten_query = (
        "What happens during step 3 of the approval process — receiving written confirmation?"
    )
    elaboration_response = (
        "The third step — receiving written confirmation — means the committee sends "
        "an official letter or email within 10 business days of approving your request. "
        f"The document states this explicitly. [CITE:{chunk['chunk_id']}]"
    )

    with (
        patch("app.services.rag.query_rewriter.rewrite_query", return_value=rewritten_query),
        patch("app.services.rag.retrieve", return_value=[chunk]),
        patch("app.clients.azure_openai.call_llm", return_value=elaboration_response),
    ):
        result = rag.generate_response(db, assistant, conv.id, elaboration_query)

    no_context_prefix = "I did not find relevant information"
    assert not result["content"].startswith(no_context_prefix), (
        f"Elaboration triggered the hardcoded no-context response: {result['content']!r}"
    )
    assert len(result["content"]) > 100, (
        f"Elaboration response is too short ({len(result['content'])} chars): {result['content']!r}"
    )
