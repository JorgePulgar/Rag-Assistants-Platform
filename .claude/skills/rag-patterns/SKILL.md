---
name: rag-patterns
description: Patrones de implementación del pipeline RAG para este proyecto. Úsala cuando trabajes en parsing de documentos, chunking, embeddings, retrieval, construcción del prompt o extracción de citas. No la uses para CRUD de asistentes o lógica de UI.
---

# RAG Patterns — Patrones concretos para este proyecto

## Cuándo activar esta skill

Activa esta skill cuando la tarea toque cualquiera de:
- Parsing de PDF, DOCX, PPTX o texto.
- Chunking de documentos.
- Llamadas a embeddings.
- Subida/borrado de documentos en Azure AI Search.
- Retrieval (búsqueda en Azure AI Search).
- Construcción del prompt RAG.
- Extracción y formateo de citas.
- Cualquier test que involucre el pipeline anterior.

**No** la actives para: CRUD de asistentes/conversaciones sin tocar RAG,
maquetación de UI, endpoints genéricos.

## Patrones obligatorios

### 1. Un índice Azure AI Search por asistente

```python
# Correcto
index_name = f"assistant-{assistant.id.hex}"
search_client.create_index(name=index_name, ...)

# Incorrecto — NUNCA hacer esto
search_client.query(index="global", filter=f"assistant_id eq '{id}'")
```

El aislamiento es **estructural**. Si ves código con filtros por
`assistant_id` sobre un índice compartido, es un bug.

### 2. Chunking con separadores en cascada

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.CHUNK_SIZE,          # 800 por defecto
    chunk_overlap=settings.CHUNK_OVERLAP,    # 150 por defecto
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len,
)
```

Nunca hardcodear los valores. Siempre leer de `settings`.

### 3. Un chunk = una página (PDF/PPTX)

Si un párrafo cruza de página 3 a página 4, produces 2 chunks: uno con
`page=3` (la parte que está en esa página) y otro con `page=4`.

```python
# En el parser de PDF
for page_num, page in enumerate(reader.pages, start=1):
    text = page.extract_text()
    if len(text.strip()) < 20:
        continue  # página vacía
    # chunking solo dentro del texto de esta página
    chunks = splitter.split_text(text)
    for idx, chunk_text in enumerate(chunks):
        yield ParsedChunk(text=chunk_text, page=page_num, section=None)
```

### 4. Embeddings en batches de 16

```python
def embed_chunks(chunks: list[str]) -> list[list[float]]:
    embeddings = []
    for i in range(0, len(chunks), 16):
        batch = chunks[i:i+16]
        response = openai_client.embeddings.create(
            model=settings.AZURE_OPENAI_EMBEDDING_DEPLOYMENT,
            input=batch,
        )
        embeddings.extend([item.embedding for item in response.data])
    return embeddings
```

### 5. Retrieval híbrido con semantic reranking

```python
from azure.search.documents.models import (
    VectorizedQuery,
    QueryType,
)

results = search_client.search(
    search_text=user_query,                          # keyword search
    vector_queries=[VectorizedQuery(
        vector=query_embedding,
        k_nearest_neighbors=10,
        fields="vector",
    )],
    query_type=QueryType.SEMANTIC,
    semantic_configuration_name="default-semantic-config",
    top=settings.RETRIEVAL_TOP_K,
)

filtered = [
    r for r in results
    if r["@search.reranker_score"] >= settings.RETRIEVAL_SCORE_THRESHOLD
]
```

### 6. Camino "no sé" antes de llamar al LLM

```python
def generate_response(assistant, conversation, user_message):
    chunks = retrieve(assistant.search_index, user_message)

    if not chunks:
        return {
            "content": (
                "No he encontrado información relevante en los documentos "
                "de este asistente para responder a tu pregunta. Sugerencia: "
                "reformula la pregunta o sube documentos relacionados al "
                "asistente."
            ),
            "citations": [],
        }

    # ... resto del flujo con LLM
```

**Ahorra coste y evita alucinaciones**. No se llama al LLM si no hay
contexto.

### 7. Formato de citas con `[CITA:chunk_id]`

```python
system_prompt = f"""{assistant.instructions}

REGLAS DE COMPORTAMIENTO:
1. Responde SOLO con información del CONTEXTO.
2. Si no hay información suficiente, responde: "No tengo información..."
3. Cita las fuentes usando [CITA:chunk_id] inline.
..."""
```

El post-procesado extrae los `chunk_id`, los mapea a objetos completos,
y el frontend renderiza como `[1]`, `[2]`, ... clicables.

```python
import re

def post_process(llm_response: str, retrieved_chunks: list[dict]) -> dict:
    chunk_by_id = {c["chunk_id"]: c for c in retrieved_chunks}
    pattern = re.compile(r"\[CITA:([a-f0-9-]+)\]")

    cited_ids_in_order = []
    seen = set()
    for match in pattern.finditer(llm_response):
        cid = match.group(1)
        if cid not in seen and cid in chunk_by_id:
            cited_ids_in_order.append(cid)
            seen.add(cid)

    # Sustituir [CITA:id] por [N]
    content = llm_response
    citations = []
    for i, cid in enumerate(cited_ids_in_order, start=1):
        content = content.replace(f"[CITA:{cid}]", f"[{i}]")
        chunk = chunk_by_id[cid]
        citations.append({
            "document_id": chunk["document_id"],
            "document_name": chunk["document_name"],
            "page": chunk.get("page"),
            "chunk_text": chunk["text"][:300],
        })

    return {"content": content, "citations": citations}
```

### 8. Historial acotado

```python
# Cargar últimos N mensajes (no todos)
history = (
    db.query(Message)
    .filter(Message.conversation_id == conversation.id)
    .order_by(Message.created_at.desc())
    .limit(settings.HISTORY_MAX_MESSAGES)
    .all()
)
history.reverse()  # orden cronológico para el LLM
```

## Anti-patrones (rechaza si los ves)

- **Filtros por `assistant_id` sobre índice compartido**: rompe aislamiento.
- **`[Doc 1, pág. 3]` como string en el texto**: cita no estructurada.
- **Llamar al LLM siempre, incluso con retrieval vacío**: desperdicia
  dinero y arriesga alucinación.
- **Chunking con `chunk_size` hardcoded**: imposible tunear.
- **Cargar todo el historial de la conversación**: infla tokens sin
  beneficio.
- **Parser que ignora errores silenciosamente**: documento queda en
  estado inconsistente.

## Referencias en el repo

- Spec completa: `docs/RAG_SPEC.md`.
- Tests obligatorios: `backend/tests/test_isolation.py`, `test_parsers.py`,
  `test_rag_prompt.py`.
- Constantes: `backend/app/config.py` lee de `.env`.
