"""Regression test for Bug 1 (T047b).

An assistant with no documents (empty index) must return HTTP 200 with the
hardcoded "I did not find" message, never a 500 error.

The bug: pre-fix, querying a non-existent index raised ResourceNotFoundError
which propagated as 500.  Post-fix, the index exists from the moment the
assistant is created (eager creation), and an empty index correctly triggers
the "I don't know" path.
"""
from unittest.mock import patch

from fastapi.testclient import TestClient


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
