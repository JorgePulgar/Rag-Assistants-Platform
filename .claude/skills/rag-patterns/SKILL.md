---
name: rag-patterns
description: Implementation patterns for the RAG pipeline of this project. Use it when working on document parsing, chunking, embeddings, retrieval, prompt construction, or citation extraction. Do not use it for assistant CRUD or UI work.
---

# RAG Patterns — Concrete patterns for this project

## When to activate

Activate this skill when the task touches any of:
- PDF, DOCX, PPTX, or text parsing.
- Document chunking.
- Embedding calls.
- Upload/delete of documents on Azure AI Search.
- Retrieval (search on Azure AI Search).
- RAG prompt construction.
- Citation extraction and formatting.
- Any test involving the pipeline above.

**Do not** activate for: assistant/conversation CRUD without touching
RAG, UI layout, generic endpoints.

## Mandatory patterns

### 1. One Azure AI Search index per assistant

```python
# Correct
index_name = f"assistant-{assistant.id.hex}"
search_client.create_index(name=index_name, ...)

# Wrong — NEVER do this
search_client.query(index="global", filter=f"assistant_id eq '{id}'")
```

Isolation is **structural**. If you see code filtering by `assistant_id`
over a shared index, that is a bug.

### 2. Chunking with cascading separators

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=settings.CHUNK_SIZE,          # default 800
    chunk_overlap=settings.CHUNK_OVERLAP,    # default 150
    separators=["\n\n", "\n", ". ", " ", ""],
    length_function=len,
)
```

Never hardcode these values. Always read from `settings`.

### 3. One chunk = one page (PDF/PPTX)

If a paragraph crosses from page 3 to page 4, produce two chunks: one with
`page=3` (the portion on that page) and another with `page=4`.

```python
# PDF parser
for page_num, page in enumerate(reader.pages, start=1):
    text = page.extract_text()
    if len(text.strip()) < 20:
        continue  # blank page
    # chunking only within the text of this page
    chunks = splitter.split_text(text)
    for idx, chunk_text in enumerate(chunks):
        yield ParsedChunk(text=chunk_text, page=page_num, section=None)
```

### 4. Embeddings in batches of 16

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

### 5. Hybrid retrieval with semantic reranking

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

### 6. "I don't know" path before calling the LLM

```python
def generate_response(assistant, conversation, user_message):
    chunks = retrieve(assistant.search_index, user_message)

    if not chunks:
        return {
            "content": (
                "I did not find relevant information in this assistant's "
                "documents to answer your question. Suggestion: rephrase "
                "the question or upload related documents to this assistant."
            ),
            "citations": [],
        }

    # ... rest of the flow with the LLM
```

**Saves cost and prevents hallucination**. The LLM is not called if there
is no context.

### 7. `[CITE:chunk_id]` citation format

```python
system_prompt = f"""{assistant.instructions}

BEHAVIOUR RULES:
1. Respond ONLY with information from the CONTEXT.
2. If information is missing, answer: "I don't have enough information..."
3. Cite sources using [CITE:chunk_id] inline.
..."""
```

Post-processing extracts the `chunk_id`s, maps them to full objects, and
the frontend renders them as clickable `[1]`, `[2]`, ... pills.

```python
import re

def post_process(llm_response: str, retrieved_chunks: list[dict]) -> dict:
    chunk_by_id = {c["chunk_id"]: c for c in retrieved_chunks}
    pattern = re.compile(r"\[CITE:([a-f0-9-]+)\]")

    cited_ids_in_order = []
    seen = set()
    for match in pattern.finditer(llm_response):
        cid = match.group(1)
        if cid not in seen and cid in chunk_by_id:
            cited_ids_in_order.append(cid)
            seen.add(cid)

    # Replace [CITE:id] with [N]
    content = llm_response
    citations = []
    for i, cid in enumerate(cited_ids_in_order, start=1):
        content = content.replace(f"[CITE:{cid}]", f"[{i}]")
        chunk = chunk_by_id[cid]
        citations.append({
            "document_id": chunk["document_id"],
            "document_name": chunk["document_name"],
            "page": chunk.get("page"),
            "chunk_text": chunk["text"][:300],
        })

    return {"content": content, "citations": citations}
```

### 8. Bounded, persistent history (conversational memory)

Conversational memory is a **core feature** of the project. The assistant
must feel like it remembers prior turns in the same conversation.

Load messages from SQLite and preserve their roles — never drop roles,
never merge turns into the same message.

```python
# Load last N messages, not all — then reverse to chronological order
history = (
    db.query(Message)
    .filter(Message.conversation_id == conversation.id)
    .order_by(Message.created_at.desc())
    .limit(settings.HISTORY_MAX_MESSAGES)
    .all()
)
history.reverse()

# Build the messages array with roles preserved
messages = [{"role": "system", "content": system_prompt}]
for msg in history:
    messages.append({"role": msg.role, "content": msg.content})
# The retrieved context + current question go as the last user message
messages.append({"role": "user", "content": context_block + "\n\n" + user_message})
```

**Why this works across sessions**: SQLite is a file on disk, so the
history survives backend restarts, browser closes, and machine reboots.
No in-memory or session state is used anywhere. A user who returns a
week later should get their conversation back exactly as they left it.

**Do not** retrieve on every historical turn — retrieval runs only
against the *current* user message. The LLM resolves references ("and
the next one?") from the history already present in the prompt.

## Anti-patterns (reject on sight)

- **Filtering by `assistant_id` on a shared index**: breaks isolation.
- **`[Doc 1, p. 3]` as inline string**: unstructured citation.
- **Always calling the LLM, even with empty retrieval**: wastes money and
  risks hallucination.
- **Chunking with hardcoded `chunk_size`**: impossible to tune.
- **Loading the full conversation history**: inflates tokens with no gain.
- **Parser silently swallowing errors**: document ends up in an
  inconsistent state.

## Repository references

- Full spec: `docs/RAG_SPEC.md`.
- Mandatory tests: `backend/tests/test_isolation.py`, `test_parsers.py`,
  `test_rag_prompt.py`.
- Constants: `backend/app/config.py` reads from `.env`.
