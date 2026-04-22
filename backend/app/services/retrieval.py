import logging
from typing import Any

from app.clients import azure_openai, azure_search
from app.config import settings
from app.exceptions import RetrievalError

logger = logging.getLogger(__name__)


def retrieve(index_name: str, query: str) -> list[dict[str, Any]]:
    """Embed the query, run hybrid + semantic search, return top-k chunks above threshold.

    Args:
        index_name: Azure AI Search index for this assistant (one index per assistant).
        query: raw user question text.

    Returns:
        Filtered list of chunk dicts from Azure AI Search.
        Empty list when nothing clears the score threshold (triggers "I don't know" path).
    """
    try:
        embedding = azure_openai.embed_texts([query])[0]
    except Exception as exc:
        raise RetrievalError(f"Failed to embed query: {exc}") from exc

    try:
        raw = azure_search.search(
            index_name=index_name,
            query=query,
            query_embedding=embedding,
            top_k=settings.retrieval_top_k,
        )
    except Exception as exc:
        raise RetrievalError(f"Azure AI Search query failed: {exc}") from exc

    filtered = [
        r
        for r in raw
        if (r.get("@search.reranker_score") or 0.0) >= settings.retrieval_score_threshold
    ]

    logger.info(
        "Retrieval on %s: %d raw result(s), %d above threshold %.2f",
        index_name,
        len(raw),
        len(filtered),
        settings.retrieval_score_threshold,
    )
    return filtered
