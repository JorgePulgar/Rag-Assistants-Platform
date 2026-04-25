"""Ingestion edge-case tests (T050).

Cases verified:
  1. File > 10 MB  → HTTP 413, no document row created.
  2. Empty file (0 bytes) → HTTP 422, no document row created.
  3. Unsupported format (.xyz) → HTTP 201, document.status = "failed".
  4. Corrupt PDF (non-PDF bytes with .pdf extension) → HTTP 201, document.status = "failed".
"""
import io

import pytest

_MAX_MB = 10
_MAX_BYTES = _MAX_MB * 1024 * 1024


# ── helpers ──────────────────────────────────────────────────────────────────


def _create_assistant(client):
    resp = client.post(
        "/api/assistants",
        json={
            "name": "Edge Case Assistant",
            "instructions": "You are helpful.",
        },
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _upload(client, assistant_id: str, filename: str, content: bytes):
    return client.post(
        f"/api/assistants/{assistant_id}/documents",
        files={"file": (filename, io.BytesIO(content), "application/octet-stream")},
    )


# ── test cases ────────────────────────────────────────────────────────────────


def test_upload_oversized_file_returns_413(client):
    """A file larger than 10 MB must be rejected with HTTP 413 before ingestion."""
    assistant_id = _create_assistant(client)
    big_content = b"x" * (_MAX_BYTES + 1)
    resp = _upload(client, assistant_id, "huge.pdf", big_content)

    assert resp.status_code == 413, f"Expected 413, got {resp.status_code}: {resp.text}"
    assert "10 MB" in resp.json()["detail"]

    # No document row should have been created
    docs = client.get(f"/api/assistants/{assistant_id}/documents").json()
    assert docs == [], "Document row should not be created for oversized file"


def test_upload_empty_file_returns_422(client):
    """A 0-byte file must be rejected with HTTP 422 before ingestion."""
    assistant_id = _create_assistant(client)
    resp = _upload(client, assistant_id, "empty.txt", b"")

    assert resp.status_code == 422, f"Expected 422, got {resp.status_code}: {resp.text}"

    docs = client.get(f"/api/assistants/{assistant_id}/documents").json()
    assert docs == [], "Document row should not be created for empty file"


def test_upload_unsupported_format_returns_failed_status(client):
    """An unsupported extension results in a 201 response with status='failed'."""
    assistant_id = _create_assistant(client)
    resp = _upload(client, assistant_id, "data.xyz", b"some binary content")

    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    doc = resp.json()
    assert doc["status"] == "failed", f"Expected status='failed', got '{doc['status']}'"
    assert doc["error_message"], "error_message should be set"


def test_upload_corrupt_pdf_returns_failed_status(client):
    """Corrupt PDF bytes with a .pdf extension result in 201 with status='failed'."""
    assistant_id = _create_assistant(client)
    corrupt_content = b"This is definitely not a PDF file, just random text bytes."
    resp = _upload(client, assistant_id, "corrupt.pdf", corrupt_content)

    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.text}"
    doc = resp.json()
    assert doc["status"] == "failed", f"Expected status='failed', got '{doc['status']}'"
    assert doc["error_message"], "error_message should be set for corrupt file"
