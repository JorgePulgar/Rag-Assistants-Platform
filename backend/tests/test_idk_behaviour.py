"""Regression tests for Bug 1 (T047b) and Bug 8 (T057a).

Bug 1: an assistant with no documents (empty index) must return HTTP 200 with the
hardcoded "I did not find" message, never a 500 error.

Bug 8: the "I don't know" warning style must apply regardless of the response language.
The backend now sets `is_fallback=True` on the persisted message so the frontend
does not have to do language-sensitive string matching.
"""
import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient


# ── Bug 1 regression ──────────────────────────────────────────────────────────

def test_no_documents_returns_idk_not_500(client: TestClient) -> None:
    # Create an assistant — Azure is fully mocked by conftest._stub_azure,
    # so create_index_if_not_exists is a no-op.
    resp = client.post(
        "/api/assistants",
        json={"name": "Empty Assistant", "instructions": "You are helpful."},
    )
    assert resp.status_code == 201
    assistant_id = resp.json()["id"]

    # Create a conversation on the assistant.
    resp = client.post("/api/conversations", json={"assistant_id": assistant_id})
    assert resp.status_code == 201
    conv_id = resp.json()["id"]

    # Simulate an empty index: retrieve returns no chunks above the threshold.
    # This is what a real empty Azure index would produce after the Bug 1 fix.
    with patch("app.services.rag.retrieve", return_value=[]):
        resp = client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"content": "What does the contract say about clause 3?"},
        )

    assert resp.status_code == 200, (
        f"Expected 200, got {resp.status_code}. Body: {resp.text}"
    )
    body = resp.json()
    assert "did not find" in body["message"]["content"].lower(), (
        f"Expected hardcoded no-context message, got: {body['message']['content']!r}"
    )
    assert body["message"]["citations"] == [], (
        f"Expected empty citations, got: {body['message']['citations']}"
    )


# ── Bug 8 regression (T057a) ──────────────────────────────────────────────────

def _setup_assistant_and_conversation(client: TestClient) -> tuple[str, str]:
    """Create an assistant and a fresh conversation; return (assistant_id, conv_id)."""
    resp = client.post(
        "/api/assistants",
        json={"name": "Fallback Test Assistant", "instructions": "You are helpful."},
    )
    assert resp.status_code == 201
    assistant_id = resp.json()["id"]

    resp = client.post("/api/conversations", json={"assistant_id": assistant_id})
    assert resp.status_code == 201
    return assistant_id, resp.json()["id"]


def test_empty_retrieval_sets_is_fallback_true(client: TestClient) -> None:
    """Pre-LLM empty-retrieval path must set is_fallback=True on the persisted message."""
    _, conv_id = _setup_assistant_and_conversation(client)

    with patch("app.services.rag.retrieve", return_value=[]):
        resp = client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"content": "¿Qué dice el contrato sobre la cláusula 3?"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["message"]["is_fallback"] is True, (
        f"Expected is_fallback=True for empty-retrieval path, got: {body['message']!r}"
    )


def test_llm_spanish_fallback_sets_is_fallback_true(client: TestClient) -> None:
    """LLM returning a Spanish Rule-2 fallback must set is_fallback=True.

    This is the B8 scenario: the user writes in Spanish, Rule 6 makes the LLM
    respond in Spanish, and the frontend must still show the amber warning style.
    With is_fallback on the backend the frontend no longer does string matching.
    """
    _, conv_id = _setup_assistant_and_conversation(client)

    fake_chunk = {
        "chunk_id": str(uuid.uuid4()),
        "document_id": str(uuid.uuid4()),
        "document_name": "doc.pdf",
        "page": 1,
        "text": "Irrelevant content about a different topic.",
        "@search.reranker_score": 2.0,
    }
    spanish_fallback = (
        "No tengo suficiente información en mis documentos para responder esta pregunta. "
        "Lo que busqué: cláusula 3 del contrato. "
        "Sugerencia: reformula la pregunta o sube documentos relacionados."
    )

    with (
        patch("app.services.rag.retrieve", return_value=[fake_chunk]),
        patch("app.clients.azure_openai.call_llm", return_value=spanish_fallback),
    ):
        resp = client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"content": "¿Qué dice el contrato sobre la cláusula 3?"},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["message"]["is_fallback"] is True, (
        f"Expected is_fallback=True for Spanish Rule-2 fallback, got: {body['message']!r}"
    )
    assert body["message"]["citations"] == []


def test_is_fallback_persists_across_reload(client: TestClient) -> None:
    """is_fallback=True must survive a conversation reload via GET /messages.

    This ensures the frontend can style messages correctly when reopening an
    old conversation, not just on the initial response.
    """
    _, conv_id = _setup_assistant_and_conversation(client)

    with patch("app.services.rag.retrieve", return_value=[]):
        resp = client.post(
            f"/api/conversations/{conv_id}/messages",
            json={"content": "¿Cuál es la capital de Francia?"},
        )
    assert resp.status_code == 200
    sent_id = resp.json()["message"]["id"]

    # Reload the full conversation history
    resp = client.get(f"/api/conversations/{conv_id}/messages")
    assert resp.status_code == 200
    messages = resp.json()

    assistant_msgs = [m for m in messages if m["role"] == "assistant"]
    assert len(assistant_msgs) == 1
    assert assistant_msgs[0]["id"] == sent_id
    assert assistant_msgs[0]["is_fallback"] is True, (
        f"is_fallback was not persisted: {assistant_msgs[0]!r}"
    )
