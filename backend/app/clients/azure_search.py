import logging

from azure.core.credentials import AzureKeyCredential
from azure.core.exceptions import ResourceNotFoundError
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)
from azure.search.documents.models import QueryType, VectorizedQuery

from app.config import settings

logger = logging.getLogger(__name__)


def get_index_client() -> SearchIndexClient:
    return SearchIndexClient(
        endpoint=settings.azure_search_endpoint,
        credential=AzureKeyCredential(settings.azure_search_api_key),
    )


def get_search_client(index_name: str) -> SearchClient:
    return SearchClient(
        endpoint=settings.azure_search_endpoint,
        index_name=index_name,
        credential=AzureKeyCredential(settings.azure_search_api_key),
    )


def build_index_schema(index_name: str) -> SearchIndex:
    return SearchIndex(
        name=index_name,
        fields=[
            SimpleField(name="chunk_id", type=SearchFieldDataType.String, key=True),
            SimpleField(
                name="document_id",
                type=SearchFieldDataType.String,
                filterable=True,
                retrievable=True,
            ),
            SimpleField(name="document_name", type=SearchFieldDataType.String, retrievable=True),
            SimpleField(name="page", type=SearchFieldDataType.Int32, retrievable=True),
            SimpleField(name="section", type=SearchFieldDataType.String, retrievable=True),
            SimpleField(name="chunk_index", type=SearchFieldDataType.Int32, retrievable=True),
            SearchableField(
                name="text",
                type=SearchFieldDataType.String,
                analyzer_name="es.microsoft",
            ),
            SearchField(
                name="vector",
                type=SearchFieldDataType.Collection(SearchFieldDataType.Single),
                searchable=True,
                vector_search_dimensions=1536,
                vector_search_profile_name="default-profile",
            ),
        ],
        vector_search=VectorSearch(
            profiles=[
                VectorSearchProfile(
                    name="default-profile",
                    algorithm_configuration_name="default-hnsw",
                )
            ],
            algorithms=[HnswAlgorithmConfiguration(name="default-hnsw")],
        ),
        semantic_search=SemanticSearch(
            configurations=[
                SemanticConfiguration(
                    name="default-semantic-config",
                    prioritized_fields=SemanticPrioritizedFields(
                        content_fields=[SemanticField(field_name="text")]
                    ),
                )
            ]
        ),
    )


def create_index_if_not_exists(index_name: str) -> None:
    client = get_index_client()
    try:
        client.get_index(index_name)
    except ResourceNotFoundError:
        client.create_index(build_index_schema(index_name))
        logger.info("Created Azure AI Search index: %s", index_name)


def upload_documents(index_name: str, documents: list[dict]) -> None:
    client = get_search_client(index_name)
    batch_size = 100
    for i in range(0, len(documents), batch_size):
        result = client.upload_documents(documents=documents[i : i + batch_size])
        failed = [r for r in result if not r.succeeded]
        if failed:
            logger.error("Failed to upload %d chunk(s) to %s", len(failed), index_name)


def delete_documents_by_document_id(index_name: str, document_id: str) -> None:
    """Remove all chunks belonging to a document from an index."""
    client = get_search_client(index_name)
    results = list(
        client.search(
            search_text="*",
            filter=f"document_id eq '{document_id}'",
            select=["chunk_id"],
            top=1000,
        )
    )
    if results:
        client.delete_documents(documents=[{"chunk_id": r["chunk_id"]} for r in results])
        logger.info(
            "Deleted %d chunk(s) for document %s from %s", len(results), document_id, index_name
        )


def search(
    index_name: str,
    query: str,
    query_embedding: list[float],
    top_k: int,
) -> list[dict]:
    """Hybrid search with semantic reranking. Returns raw result dicts."""
    client = get_search_client(index_name)
    results = client.search(
        search_text=query,
        vector_queries=[
            VectorizedQuery(
                vector=query_embedding,
                k_nearest_neighbors=10,
                fields="vector",
            )
        ],
        query_type=QueryType.SEMANTIC,
        semantic_configuration_name="default-semantic-config",
        top=top_k,
    )
    return list(results)


def delete_index(index_name: str) -> None:
    """Delete an index. Logs and swallows errors so callers are never blocked."""
    client = get_index_client()
    try:
        client.delete_index(index_name)
        logger.info("Deleted Azure AI Search index: %s", index_name)
    except ResourceNotFoundError:
        logger.warning("Index %s not found, skipping deletion", index_name)
    except Exception as exc:  # noqa: BLE001
        logger.error("Failed to delete index %s: %s", index_name, exc)
