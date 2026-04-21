---
name: azure-integration
description: Convenciones para integrar Azure AI Foundry (LLM + embeddings) y Azure AI Search. Úsala cuando escribas clientes a Azure, manejes credenciales, crees/borres índices, o cuando un error de Azure necesite tratamiento. No la uses para lógica de dominio que no toque Azure directamente.
---

# Azure Integration — Convenciones para clientes Azure

## Cuándo activar esta skill

Activa esta skill cuando la tarea toque:
- Escritura o modificación de `clients/azure_openai.py` o `clients/azure_search.py`.
- Creación, borrado o modificación de índices en Azure AI Search.
- Manejo de errores de red o autenticación contra Azure.
- Configuración de variables de entorno relacionadas con Azure.
- Cualquier test que requiera llamadas reales a Azure.

**No** la actives para: lógica de RAG pura (usa `rag-patterns`),
endpoints sin tocar Azure, UI.

## Autenticación

Se usa **API Key** para ambos servicios en este proyecto. Managed Identity
o Entra ID sería mejor en producción, pero para MVP con crédito académico
la API key es suficiente y simple.

Variables de entorno:
```
AZURE_OPENAI_ENDPOINT=https://tu-recurso.openai.azure.com/
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_API_VERSION=2024-10-21

AZURE_SEARCH_ENDPOINT=https://tu-search.search.windows.net
AZURE_SEARCH_API_KEY=...
```

Nunca leer `os.getenv` directamente desde módulos de negocio. Siempre a
través de `config.py` con Pydantic Settings.

## Cliente de Azure AI Foundry (LLM + embeddings)

Usa el SDK oficial de `openai` con configuración para Azure:

```python
from openai import AzureOpenAI

def get_openai_client() -> AzureOpenAI:
    return AzureOpenAI(
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
    )
```

**IMPORTANTE**: en las llamadas, el parámetro `model` es el **nombre del
deployment** (no el nombre del modelo base). Esto es una particularidad
de Azure que confunde:

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

## Cliente de Azure AI Search

Usa `azure-search-documents`:

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

## Schema del índice (plantilla)

Todo asistente usa el mismo schema. Centraliza en una función:

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

## Nombres de índice

Regex de Azure AI Search: `^[a-z0-9]([a-z0-9-]*[a-z0-9])?$`, longitud
2-128.

Convención del proyecto: `assistant-{uuid_hex_sin_guiones}`.

```python
def build_index_name(assistant_id: UUID) -> str:
    return f"assistant-{assistant_id.hex}"
```

## Manejo de errores Azure

Los errores de Azure son, por orden de frecuencia:

1. **Rate limit (429)**: `openai.RateLimitError` o
   `azure.core.exceptions.HttpResponseError` con status 429. Reintentar
   con backoff exponencial (3 intentos: 1s, 2s, 4s).

2. **Autenticación (401)**: credencial inválida. No reintentar; loggear
   y propagar como 502 al cliente.

3. **Recurso no encontrado (404)**: para operaciones de índice significa
   que el índice no existe. En CREATE es esperado; en READ/DELETE hay que
   diferenciar caso legítimo de bug.

4. **Timeout**: por defecto 60s, configurable. Si falla, loggear y
   propagar.

Patrón recomendado:

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

## Tests que tocan Azure

Marca con `pytest.mark.integration` y salta si faltan credenciales:

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

Para los tests de aislamiento, usar prefijo `test-` en el índice y
limpiar al final con un `finally`:

```python
def test_isolation():
    index_a = f"test-assistant-a-{uuid4().hex[:8]}"
    index_b = f"test-assistant-b-{uuid4().hex[:8]}"
    try:
        # ... crear índices, subir docs, verificar aislamiento
    finally:
        index_client.delete_index(index_a)
        index_client.delete_index(index_b)
```

## Checklist antes de hacer merge de código Azure

- [ ] Las credenciales se leen desde `settings`, no `os.getenv` directo.
- [ ] El nombre del deployment (no el modelo) se pasa en `model=`.
- [ ] Hay manejo explícito de rate limits.
- [ ] Los tests de integración están marcados y pueden saltarse.
- [ ] Los índices de test tienen prefijo y se limpian.
- [ ] No hay credenciales hardcoded ni en logs.
