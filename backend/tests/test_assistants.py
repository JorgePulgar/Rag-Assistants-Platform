"""CRUD tests for the /api/assistants endpoints (T012)."""
import re

from fastapi.testclient import TestClient

_INDEX_RE = re.compile(r"^assistant-[0-9a-f]{32}$")

_PAYLOAD = {
    "name": "Legal Expert",
    "instructions": "You are a lawyer specialised in contracts.",
    "description": "Answers legal questions.",
}


def test_list_assistants_empty(client: TestClient) -> None:
    resp = client.get("/api/assistants")
    assert resp.status_code == 200
    assert resp.json() == []


def test_create_assistant_returns_201(client: TestClient) -> None:
    resp = client.post("/api/assistants", json=_PAYLOAD)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == _PAYLOAD["name"]
    assert body["instructions"] == _PAYLOAD["instructions"]
    assert body["description"] == _PAYLOAD["description"]
    assert _INDEX_RE.match(body["search_index"]), f"Bad index name: {body['search_index']}"
    assert "id" in body
    assert "created_at" in body
    assert "updated_at" in body


def test_create_assistant_search_index_derived_from_id(client: TestClient) -> None:
    resp = client.post("/api/assistants", json=_PAYLOAD)
    body = resp.json()
    expected_index = "assistant-" + body["id"].replace("-", "")
    assert body["search_index"] == expected_index


def test_list_assistants_after_create(client: TestClient) -> None:
    client.post("/api/assistants", json=_PAYLOAD)
    client.post("/api/assistants", json={**_PAYLOAD, "name": "Cooking Assistant"})
    resp = client.get("/api/assistants")
    assert resp.status_code == 200
    names = [a["name"] for a in resp.json()]
    assert "Legal Expert" in names
    assert "Cooking Assistant" in names


def test_get_assistant_by_id(client: TestClient) -> None:
    created = client.post("/api/assistants", json=_PAYLOAD).json()
    resp = client.get(f"/api/assistants/{created['id']}")
    assert resp.status_code == 200
    assert resp.json()["id"] == created["id"]


def test_get_assistant_not_found(client: TestClient) -> None:
    resp = client.get("/api/assistants/nonexistent-id")
    assert resp.status_code == 404
    assert "detail" in resp.json()


def test_update_assistant_name(client: TestClient) -> None:
    created = client.post("/api/assistants", json=_PAYLOAD).json()
    resp = client.patch(f"/api/assistants/{created['id']}", json={"name": "Updated Name"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "Updated Name"
    assert body["instructions"] == _PAYLOAD["instructions"]  # unchanged
    assert body["updated_at"] >= body["created_at"]


def test_update_assistant_not_found(client: TestClient) -> None:
    resp = client.patch("/api/assistants/nonexistent-id", json={"name": "X"})
    assert resp.status_code == 404


def test_delete_assistant(client: TestClient) -> None:
    created = client.post("/api/assistants", json=_PAYLOAD).json()
    resp = client.delete(f"/api/assistants/{created['id']}")
    assert resp.status_code == 204
    assert client.get(f"/api/assistants/{created['id']}").status_code == 404


def test_delete_assistant_not_found(client: TestClient) -> None:
    resp = client.delete("/api/assistants/nonexistent-id")
    assert resp.status_code == 404


def test_two_assistants_have_distinct_search_indexes(client: TestClient) -> None:
    a1 = client.post("/api/assistants", json=_PAYLOAD).json()
    a2 = client.post("/api/assistants", json={**_PAYLOAD, "name": "Second"}).json()
    assert a1["search_index"] != a2["search_index"]
