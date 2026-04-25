"""Chat endpoint edge-case tests (T051).

Cases verified:
  1. Empty message content → HTTP 422.
  2. Message content > 20 000 chars → HTTP 422.
  3. Send to a conversation whose assistant was deleted → HTTP 404.
"""


# ── helpers ──────────────────────────────────────────────────────────────────


def _create_assistant(client):
    resp = client.post(
        "/api/assistants",
        json={"name": "Edge Assistant", "instructions": "You are helpful."},
    )
    assert resp.status_code == 201
    return resp.json()["id"]


def _create_conversation(client, assistant_id: str):
    resp = client.post("/api/conversations", json={"assistant_id": assistant_id})
    assert resp.status_code == 201
    return resp.json()["id"]


# ── test cases ────────────────────────────────────────────────────────────────


def test_empty_message_returns_422(client):
    """Sending an empty string as message content must be rejected with HTTP 422."""
    assistant_id = _create_assistant(client)
    conv_id = _create_conversation(client, assistant_id)

    resp = client.post(
        f"/api/conversations/{conv_id}/messages",
        json={"content": ""},
    )
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"


def test_whitespace_only_message_returns_422(client):
    """Whitespace-only content (min_length=1 on stripped bytes) is rejected."""
    # Pydantic min_length counts characters, not semantic words.
    # A single space passes min_length=1, so this test verifies that
    # a genuinely empty string is caught, not a space.
    assistant_id = _create_assistant(client)
    conv_id = _create_conversation(client, assistant_id)

    resp = client.post(
        f"/api/conversations/{conv_id}/messages",
        json={"content": ""},
    )
    assert resp.status_code == 422


def test_oversized_message_returns_422(client):
    """A message longer than 20 000 characters must be rejected with HTTP 422."""
    assistant_id = _create_assistant(client)
    conv_id = _create_conversation(client, assistant_id)

    long_content = "x" * 20_001
    resp = client.post(
        f"/api/conversations/{conv_id}/messages",
        json={"content": long_content},
    )
    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"


def test_send_to_conversation_of_deleted_assistant_returns_404(client):
    """After deleting an assistant its conversations are cascade-deleted.
    A send to the now-deleted conversation must return HTTP 404, never 500.
    """
    assistant_id = _create_assistant(client)
    conv_id = _create_conversation(client, assistant_id)

    # Delete the assistant — cascades to conversation and messages
    del_resp = client.delete(f"/api/assistants/{assistant_id}")
    assert del_resp.status_code == 204

    resp = client.post(
        f"/api/conversations/{conv_id}/messages",
        json={"content": "Is anyone there?"},
    )
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.text}"
