"""Ingestion isolation test — verifies per-assistant index separation (T023).

Marked @pytest.mark.integration: hits real Azure AI Search.
Skipped automatically when AZURE_SEARCH_API_KEY is not set.
Each test run uses unique index names and cleans up in a finally block.
"""
import time
from uuid import uuid4

import pytest

from app.clients import azure_search
from app.config import settings

pytestmark = pytest.mark.integration


@pytest.fixture(autouse=True)
def require_azure() -> None:
    if not settings.azure_search_api_key:
        pytest.skip("AZURE_SEARCH_API_KEY not set — skipping integration test")


def _fake_vector() -> list[float]:
    """Return a valid 1536-dim vector for upload (content doesn't matter for isolation)."""
    return [0.01] * 1536


def test_indexes_are_structurally_isolated() -> None:
    """Chunks uploaded to index A must not appear in index B."""
    suffix = uuid4().hex[:8]
    index_a = f"test-assistant-a-{suffix}"
    index_b = f"test-assistant-b-{suffix}"

    doc_a_id = str(uuid4())
    doc_b_id = str(uuid4())

    try:
        azure_search.create_index_if_not_exists(index_a)
        azure_search.create_index_if_not_exists(index_b)

        chunks_a = [
            {
                "chunk_id": str(uuid4()),
                "document_id": doc_a_id,
                "document_name": "legal_contract.txt",
                "page": None,
                "section": None,
                "text": "Contract termination clause: either party may terminate with 30 days notice.",
                "chunk_index": 0,
                "vector": _fake_vector(),
            }
        ]
        chunks_b = [
            {
                "chunk_id": str(uuid4()),
                "document_id": doc_b_id,
                "document_name": "cooking_recipe.txt",
                "page": None,
                "section": None,
                "text": "Pasta carbonara recipe: cook spaghetti, mix with egg and pancetta.",
                "chunk_index": 0,
                "vector": _fake_vector(),
            }
        ]

        azure_search.upload_documents(index_a, chunks_a)
        azure_search.upload_documents(index_b, chunks_b)

        # Azure AI Search indexes near-real-time; wait briefly for consistency
        time.sleep(3)

        # A's document must NOT appear in B's index
        client_b = azure_search.get_search_client(index_b)
        results_in_b = list(
            client_b.search(
                search_text="*",
                filter=f"document_id eq '{doc_a_id}'",
                top=10,
            )
        )
        assert results_in_b == [], (
            f"Isolation broken: {len(results_in_b)} chunk(s) from assistant A "
            f"found in assistant B's index."
        )

        # A's document MUST appear in A's index
        client_a = azure_search.get_search_client(index_a)
        results_in_a = list(
            client_a.search(
                search_text="*",
                filter=f"document_id eq '{doc_a_id}'",
                top=10,
            )
        )
        assert len(results_in_a) == 1, (
            f"Expected 1 chunk in A's index, got {len(results_in_a)}"
        )

        # B's document must NOT appear in A's index
        results_b_in_a = list(
            client_a.search(
                search_text="*",
                filter=f"document_id eq '{doc_b_id}'",
                top=10,
            )
        )
        assert results_b_in_a == [], (
            f"Isolation broken: chunk from assistant B found in assistant A's index."
        )

    finally:
        azure_search.delete_index(index_a)
        azure_search.delete_index(index_b)


def test_delete_document_removes_only_its_chunks() -> None:
    """After deleting a document, its chunks are gone but others remain."""
    suffix = uuid4().hex[:8]
    index_name = f"test-assistant-del-{suffix}"

    doc_1_id = str(uuid4())
    doc_2_id = str(uuid4())

    try:
        azure_search.create_index_if_not_exists(index_name)

        chunks = [
            {
                "chunk_id": str(uuid4()),
                "document_id": doc_1_id,
                "document_name": "doc1.txt",
                "page": None,
                "section": None,
                "text": "Document one content.",
                "chunk_index": 0,
                "vector": _fake_vector(),
            },
            {
                "chunk_id": str(uuid4()),
                "document_id": doc_2_id,
                "document_name": "doc2.txt",
                "page": None,
                "section": None,
                "text": "Document two content.",
                "chunk_index": 0,
                "vector": _fake_vector(),
            },
        ]
        azure_search.upload_documents(index_name, chunks)
        time.sleep(3)

        azure_search.delete_documents_by_document_id(index_name, doc_1_id)
        time.sleep(2)

        client = azure_search.get_search_client(index_name)

        remaining_1 = list(
            client.search(search_text="*", filter=f"document_id eq '{doc_1_id}'", top=10)
        )
        assert remaining_1 == [], "Doc 1 chunks should have been deleted"

        remaining_2 = list(
            client.search(search_text="*", filter=f"document_id eq '{doc_2_id}'", top=10)
        )
        assert len(remaining_2) == 1, "Doc 2 chunks must not be affected by doc 1 deletion"

    finally:
        azure_search.delete_index(index_name)
