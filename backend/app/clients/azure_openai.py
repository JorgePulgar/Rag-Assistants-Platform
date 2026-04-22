import logging
import time

from openai import AzureOpenAI, RateLimitError

from app.config import settings

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_EMBED_BATCH_SIZE = 16


def get_openai_client() -> AzureOpenAI:
    return AzureOpenAI(
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        azure_endpoint=settings.azure_openai_endpoint,
    )


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a list of texts in batches of 16. Returns one vector per text."""
    client = get_openai_client()
    embeddings: list[list[float]] = []
    for i in range(0, len(texts), _EMBED_BATCH_SIZE):
        batch = texts[i : i + _EMBED_BATCH_SIZE]
        embeddings.extend(_embed_batch(client, batch))
    return embeddings


def _embed_batch(client: AzureOpenAI, texts: list[str]) -> list[list[float]]:
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.embeddings.create(
                model=settings.azure_openai_embedding_deployment,
                input=texts,
            )
            return [item.embedding for item in response.data]
        except RateLimitError as exc:
            wait = 2**attempt
            logger.warning(
                "Embedding rate-limited, retry %d/%d in %ds", attempt + 1, _MAX_RETRIES, wait
            )
            if attempt == _MAX_RETRIES - 1:
                raise
            time.sleep(wait)
    raise RuntimeError("Unreachable")  # pragma: no cover


def call_llm(messages: list[dict]) -> str:
    """Send a chat completion request. Returns the assistant message content."""
    client = get_openai_client()
    for attempt in range(_MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=settings.azure_openai_llm_deployment,
                messages=messages,  # type: ignore[arg-type]
            )
            return response.choices[0].message.content or ""
        except RateLimitError as exc:
            wait = 2**attempt
            logger.warning(
                "LLM rate-limited, retry %d/%d in %ds", attempt + 1, _MAX_RETRIES, wait
            )
            if attempt == _MAX_RETRIES - 1:
                raise
            time.sleep(wait)
    raise RuntimeError("Unreachable")  # pragma: no cover
