---
name: azure-integration
description: Conventions for integrating Azure AI Foundry (LLM + embeddings) and Azure AI Search. Use it when writing Azure clients, handling credentials, creating/deleting indexes, or when an Azure error needs explicit handling. Do not use it for domain logic that does not touch Azure directly.
---

# Azure Integration — Conventions for Azure clients

## When to activate

Activate this skill when the task touches:
- Writing or modifying `clients/azure_openai.py` or `clients/azure_search.py`.
- Creating, deleting, or modifying Azure AI Search indexes.
- Network or authentication error handling against Azure.
- Environment variable configuration for Azure.
- Any test that requires real Azure calls.

**Do not** activate for: pure RAG logic (use `rag-patterns`), endpoints
that do not touch Azure, UI.

## Authentication

We use **API Key** for both services in this project. Managed Identity or
Entra ID would be preferable in production, but for an MVP with academic
credits the API key is sufficient and simpler.

Environment variables:
```
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_API_VERSION=2024-10-21

AZURE_SEARCH_ENDPOINT=https://your-search.search.windows.net
AZURE_SEARCH_API_KEY=...
```

Never read `os.getenv` directly from business modules. Always go through
`config.py` using Pydantic Settings.

## Azure AI Foundry client (LLM + embeddings)

Use the official `openai` SDK with Azure configuration:

```python
from openai import AzureOpenAI

def get_openai_client() -> AzureOpenAI:
    return AzureOpenAI(
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    )
```

**IMPORTANT**: on calls, the `model` parameter is the **deployment name**
(not the base model name). This is an Azure particularity that often
confuses:

```python
client.chat.completions.create(
    model=settings.AZURE_OPENAI_LLM_DEPLOYMENT,  # e.g. "gpt-4o-mini"
    messages=[...],
)

client.embeddings.create(
    model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
    input=[...],
)
```

## Azure AI Search client

Use `azure-search-documents`:

```python
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.core.credentials import AzureKeyCredential

def get_index_client() -> SearchIndexClient:
    return SearchIndexClient(
        endpoint=settings.AZURE_SEARCH_ENDPOINT,
        credential=AzureKeyCredential(settings.AZURE_SEARCH_API_KEY),
    )

def get_search_client(index_name: str) -> SearchClient:
    return SearchClient(
        endpoint=settings.AZURE_SEARCH_ENDPOINT,
        index_name=index_name,
        credential=AzureKeyCredential(settings.AZURE_SEARCH_API_KEY),
    )
```

## Index schema (template)

Every assistant uses the same schema. Centralise it in a function:

```python
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchField,
    SearchFieldDataType,
    VectorSearch,
    VectorSearchProfile,
    HnswAlgorithmConfiguration,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
)

def build_index_schema(index_name: str) -> SearchIndex:
    return SearchIndex(
        name=index_name,
        fields=[
            SimpleField(name="chunk_id", type=SearchFieldDataType.String, key=True),
            SimpleField(name="document_id", type=SearchFieldDataType.String, filterable=True),
            SimpleField(name="document_name", type=SearchFieldDataType.String, retrievable=True),
            SimpleField(name="page", type=SearchFieldDataType.Int32, retrievable=True),
            SimpleField(name="section", type=SearchFieldDataType.String, retrievable=True),
            SearchableField(name="text", type=SearchFieldDataType.String, analyzer_name="es.microsoft"),
            SearchField(
                name="vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="default-profile",
            ),
        ],
        vector_search=VectorSearch(
            profiles=[VectorSearchProfile(
                name="default-profile",
                algorithm_configuration_name="default-hnsw",
            )],
            algorithms=[HnswAlgorithmConfiguration(name="default-hnsw")],
        ),
        semantic_search=SemanticSearch(
            configurations=[SemanticConfiguration(
                name="default-semantic-config",
                prioritized_fields=SemanticPrioritizedFields(
                    content_fields=[SemanticField(field_name="text")],
                ),
            )],
        ),
    )
```

## Index naming

Azure AI Search regex: `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`, length 2–128.

Project convention: `assistant-{uuid_hex_without_dashes}`.

```python
def build_index_name(assistant_id: UUID) -> str:
    return f"assistant-{assistant_id.hex}"
```

## Azure error handling

Azure errors, in rough order of frequency:

1. **Rate limit (429)**: `openai.RateLimitError` or
   `azure.core.exceptions.HttpResponseError` with status 429. Retry with
   exponential backoff (3 attempts: 1s, 2s, 4s).

2. **Authentication (401)**: invalid credential. Do not retry; log and
   surface as 502 to the client.

3. **Resource not found (404)**: for index operations this means the
   index does not exist. Expected on CREATE; on READ/DELETE, distinguish
   legitimate case from bug.

4. **Timeout**: default 60s, configurable. On failure, log and surface.

Recommended pattern:

```python
from openai import RateLimitError, APIError
from azure.core.exceptions import HttpResponseError
import time

def call_with_retry(fn, *args, max_retries=3, **kwargs):
    last_exc = None
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except (RateLimitError, HttpResponseError) as e:
            if isinstance(e, HttpResponseError) and e.status_code != 429:
                raise
            last_exc = e
            wait = 2 ** attempt
            logger.warning(f"Rate limit, retry {attempt+1}/{max_retries} in {wait}s")
            time.sleep(wait)
    raise last_exc
```

## Tests that hit Azure

Mark them with `pytest.mark.integration` and skip when credentials are
missing:

```python
import pytest
import os

pytestmark = pytest.mark.skipif(
    not os.getenv("AZURE_OPENAI_API_KEY"),
    reason="Azure credentials not configured",
)

def test_embedding_roundtrip():
    client = get_openai_client()
    response = client.embeddings.create(
        model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
        input=["test"],
    )
    assert len(response.data[0].embedding) == 1536
```

For isolation tests, use a `test-` prefix on the index name and clean up
in a `finally` block:

```python
def test_isolation():
    index_a = f"test-assistant-a-{uuid4().hex[:8]}"
    index_b = f"test-assistant-b-{uuid4().hex[:8]}"
    try:
        # ... create indexes, upload docs, verify isolation
    finally:
        index_client.delete_index(index_a)
        index_client.delete_index(index_b)
```

## Checklist before merging Azure code

- [ ] Credentials are read from `settings`, not direct `os.getenv`.
- [ ] The deployment name (not the model name) is passed in `model=`.
- [ ] Rate limits are explicitly handled.
- [ ] Integration tests are marked and can be skipped.
- [ ] Test indexes are prefixed and cleaned up.
- [ ] No hardcoded credentials, including in logs.
