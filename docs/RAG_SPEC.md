# RAG SPEC — Retrieval-Augmented Generation Pipeline Specification

This document is the **technical core** of the project. It describes every
RAG pipeline decision with its rationale. Jorge should understand and
defend every parameter — if, during the presentation, someone asks "why
chunk_size 800", the answer lives here.

---

## Parsing per format

One parser per file type. All of them return a list of `ParsedChunk`:

```python
class ParsedChunk:
    text: str                    # plain content
    page: Optional[int]          # 1-indexed page number if applicable
    section: Optional[str]       # section title if applicable
```

**PDF (`pypdf`)**: text is extracted page by page. `page` is set to the
page number. Pages with fewer than 20 useful characters are discarded
(typically covers or blank pages).

**DOCX (`python-docx`)**: we iterate over paragraphs. There is no native
page concept, so `page=None`. If the document has headings, the most
recent heading is propagated as `section`.

**PPTX (`python-pptx`)**: we iterate over slides. `page` = slide number
(people naturally talk about "slide 3" the same way they do about
"page 3"). We extract text from shapes and speaker notes when present.

**TXT / MD**: direct read, UTF-8 with latin-1 fallback. `page=None`.

**Errors**: if a parser fails, the document is left in `status=failed`
with the error message stored. We do not abort the request — the user
sees the failure in the UI and can retry.

## Chunking

We use `RecursiveCharacterTextSplitter` from `langchain_text_splitters`
with cascading separators: `["\n\n", "\n", ". ", " ", ""]`.

**Parameters**:
- `chunk_size = 800` characters.
- `chunk_overlap = 150` characters.

**Rationale for `chunk_size=800`**:
- Too small (< 400) loses local context — a paragraph developing one idea
  gets cut, and retrieval returns incoherent chunks.
- Too large (> 1500) adds noise — a 2000-character chunk contains
  relevant *and* irrelevant information; the LLM receives low-signal
  context and the answer suffers.
- 800 characters ≈ 120–150 tokens ≈ 1–2 well-formed paragraphs. It is the
  empirical sweet spot for Spanish-language legal and technical documents.

**Rationale for `chunk_overlap=150`** (roughly 18% of the chunk):
- Without overlap, a sentence crossing the boundary is split and neither
  chunk contains it whole.
- The 15–20% range is recommended both in the literature and in the Azure
  AI Search guides. Below 10% leaves ugly cuts; above 25% inflates the
  index without benefit.

**Page-scoped chunking (PDF/PPTX)**: each chunk is tied to **exactly one**
page. If a paragraph crosses from page 3 to page 4, we produce two
separate chunks. This is more conservative, but it guarantees each citation
points to a single page — saying "see page 3 or 4" in a citation is worse
than showing two citations to distinct pages.

**Per-chunk metadata**:
```python
{
  "chunk_id": "uuid",           # generated
  "document_id": "uuid",
  "document_name": "str",
  "page": int | None,
  "section": str | None,
  "text": "str",
  "chunk_index": int            # position within the document
}
```

## Embeddings

- Model: `text-embedding-3-small` (Azure Foundry deployment).
- Dimensions: 1536.
- Indexing batch size: 16 chunks per call (comfortable limit for Foundry
  and reduces ingestion latency).

**Why `-small` and not `-large`**:
- `-large` (3072 dims) costs about 6× more and yields roughly 2% on
  retrieval benchmarks. For an MVP it is not worth it.
- If quality ever needs to improve, we swap the deployment name and
  reindex. It is an environment variable, not an architectural decision.

## Azure AI Search: index schema

Every assistant has an index with this schema:

```python
fields = [
    SimpleField(name="chunk_id", type="Edm.String", key=True),
    SimpleField(name="document_id", type="Edm.String", filterable=True),
    SimpleField(name="document_name", type="Edm.String", retrievable=True),
    SimpleField(name="page", type="Edm.Int32", retrievable=True),
    SimpleField(name="section", type="Edm.String", retrievable=True),
    SearchableField(name="text", type="Edm.String", analyzer_name="es.microsoft"),
    SearchField(
        name="vector",
        type="Collection(Edm.Single)",
        searchable=True,
        vector_search_dimensions=1536,
        vector_search_profile_name="default-profile"
    ),
]
```

**Vector search profile**: HNSW with default parameters (`m=4`,
`ef_construction=400`). Tuning for an MVP is not worth the effort.

**Semantic ranker**: enabled on queries. Requires `semantic search` to be
configured on the service — verify the resource tier (Basic or higher).

**Spanish analyzer**: `es.microsoft` improves stemming and tokenisation
for Spanish-language documents. This is deliberate because we expect demo
content in Spanish. For an English-only corpus we would switch to
`en.microsoft`.

## Query rewriting (for conversational queries)

**Problem it solves**: the user's current message is often not
semantically self-contained. In a 3-turn conversation, turn 3 might be
"tell me more about point 2 from your previous answer". The raw
embedding of that sentence has zero topical signal — retrieval returns
irrelevant chunks, the LLM receives wrong context, and the answer goes
off-topic even though the conversation history is loaded correctly.

**When it runs**: always, except on the first message of a conversation
(no history → the user's message is the query as-is).

**How it works**:

1. Collect the last N history messages (we use 4 — two user/assistant
   pairs — to keep prompt size bounded).
2. Make a cheap LLM call to `gpt-4o-mini` with this system prompt:

```
You rewrite follow-up questions into standalone search queries.

Given a conversation history and the user's current message, produce a
single sentence that captures what the user is asking about, including
enough topical context from prior turns to be meaningful on its own.

Rules:
- Output ONLY the rewritten query. No explanation, no quotes, no prefix.
- If the user's message is already self-contained (introduces a new
  topic), return it unchanged.
- Keep the user's language (Spanish queries stay in Spanish).
- Preserve specific proper nouns, numbers, and technical terms from the
  history.
- Target length: 10–30 words.
```

3. Use the rewritten query as input to the retrieval step (embedding +
   Azure Search). The **original** user message is still the one stored
   in the database and shown in the UI — rewriting is an internal
   retrieval concern.

**Example**:

```
History:
  user:      "What does section 2 of your documents say?"
  assistant: "Section 2 covers two topics: (1) Procedimiento de apremio,
              and (2) Régimen exterior de la Unión."

Current user message: "Tell me more about point 2"

Rewritten query: "Régimen exterior de la Unión: empresarios no
  establecidos en la Comunidad que prestan servicios"
```

**Cost**: one extra LLM call per user message when there is history.
With `gpt-4o-mini` this adds ~300–600 ms of latency and a few hundred
tokens — negligible for the UX gain. Configurable via
`QUERY_REWRITING_ENABLED=true` in `.env` in case it ever needs to be
disabled for debugging.

**Logging**: when rewriting fires, log both the original and the
rewritten query at INFO level so the behaviour is auditable.

## Index lifecycle

Per `CONSTITUTION.md` §1, **creating an assistant implies creating its
Azure AI Search index**. The operations are transactional with the
SQLite row:

- On `POST /api/assistants` → create SQLite row + create Azure Search
  index. If index creation fails, the SQLite row must be rolled back.
- On `DELETE /api/assistants/{id}` → delete Azure Search index + delete
  SQLite row.

This is NOT a lazy operation. The index exists from the moment the
assistant exists, even before any document is uploaded. Rationale:
the alternative (lazy creation on first document upload) breaks the
"I don't know" behaviour — a query against a non-existent index raises
`ResourceNotFoundError` instead of returning empty results, which
surfaces to the user as a generic 500 error.

**Empty index behaviour**: an index with no documents is a perfectly
valid state. A retrieval query against an empty index returns zero
results, which triggers the hardcoded "I don't know" response path as
designed.

## Retrieval

Given a user message:

1. **Query rewriting** (if there is conversation history): produce a
   standalone search query per the §"Query rewriting" section above.
   Otherwise the query is the user's raw message.
2. Generate the query embedding (`text-embedding-3-small`).
3. Hybrid query against Azure AI Search:
   - Keyword search over `text` (Spanish analyzer).
   - Vector search over `vector` (k_nearest_neighbors=10).
   - Reciprocal Rank Fusion + semantic reranking.
4. Take the top 5 results.
5. Drop any result with `@search.reranker_score < 1.5` (Azure semantic
   reranker uses a 0–4 scale). This threshold is tuned empirically
   against real documents; 1.5 is a conservative starting point.

**Error handling**: if Azure AI Search returns `ResourceNotFoundError`
for an index that should exist (per the lifecycle above, it always
should), log the error and treat the retrieval as empty. Do not
propagate the error — user-facing failures for retrieval issues are
not acceptable.

**If after filtering zero chunks remain**: the "I don't know" path fires —
we do not call the LLM (saving cost) and return a hardcoded response
informing the user.

## Prompt construction

The prompt has three clear sections:

### System prompt

```
{assistant_instructions}

BEHAVIOUR RULES:
1. CONTEXT IS KING: Respond using ONLY information present in the CONTEXT section or in the conversation HISTORY. Absolutely no external or general knowledge. When the user asks to elaborate, expand, rephrase, or summarise something already covered in the conversation, you may build on what you previously said using the same CONTEXT — this is not "adding new information", it is presenting the same information differently. If neither the CONTEXT nor the HISTORY support the request, apply Rule 2.
2. STRICT FALLBACK: If the information is not in the context, respond EXACTLY with:
   "I don't have enough information in my documents to answer this question. What I looked for: [brief summary]. Suggestion: [suggest a different keyword or angle to search]." 
   Do not use outside knowledge to generate the suggestion.
3. CITATION FORMAT: You MUST cite sources immediately after the relevant claim, before the period. 
   - Format strictly as [CITE:chunk_id].
   - Do NOT combine citations. (WRONG: [CITE:id1, id2]. RIGHT: [CITE:id1][CITE:id2]).
   - Never hallucinate chunk IDs — only cite IDs actually present in the CONTEXT.
4. CONTRADICTIONS: If chunks contain conflicting information, objectively state both versions, citing the respective sources for each. Do not attempt to guess which one is correct.
5. TONE & STYLE: Be concise, direct, and professional. Do not repeat the user's question or use filler introductions.
6. LANGUAGE: Always respond in the same language as the user's prompt, even if the CONTEXT documents are in a different language.
```

### Retrieved context

Injected as a `user` message (decision: `user` rather than `system`,
because empirically it works better with GPT-4-family models):

```
RETRIEVED CONTEXT:

[CITE:chunk_id_1]
Document: contract_2024.pdf | Page: 3
Content: Clause 3 establishes that...

[CITE:chunk_id_2]
Document: legal_annex.pdf | Page: 7
Content: In case of breach...

USER QUESTION: {current_message}
```

### History — conversational memory

**This is a core feature, not decoration.** The assistant must behave as
if it remembers the conversation. Concretely:

- On every user message, the backend loads the last
  `HISTORY_MAX_MESSAGES=10` messages of the conversation from SQLite
  (5 user/assistant pairs).
- Those messages are injected as previous entries in the OpenAI
  `messages` array, preserving their original roles. The retrieved
  context and the current question form the last `user` message.
- Because messages live in SQLite (a file on disk), memory survives
  backend restarts, browser closures, and machine reboots. No in-memory
  or session state is used.
- Follow-up questions like "and what about the next section?" or
  "elaborate on that" work naturally because the previous turns are in
  the prompt.

**Why cap at 10**: longer history does not meaningfully improve answers
and consumes tokens. If during the demo the LLM loses context from much
older messages within the same thread, raise `HISTORY_MAX_MESSAGES` to 20.

**Design note on retrieval + memory interaction**: retrieval does NOT
run over the full history. Instead, the current user message is first
**rewritten into a standalone query** using the query rewriting step
(see §"Query rewriting"), and that rewritten query is what is embedded
and sent to Azure Search. This resolves referential follow-ups ("tell
me more about point 2") without the cost of embedding every historical
turn. The full history is still injected into the LLM's prompt as
messages — so the model has both the enriched retrieval context and
the conversational flow.

**History note**: this is a revision of an earlier design that passed
the raw user message to retrieval. That earlier design failed on
referential follow-ups (see Phase 4.5 bugfix notes in `TASKS.md`).

## Response post-processing

The LLM returns text with inline `[CITE:chunk_id]` markers. The backend:

1. Extracts all mentioned `chunk_id`s.
2. For each, looks up the full object (document_id, document_name, page,
   snippet of 300 chars) from the retrieval result.
3. Replaces `[CITE:chunk_id]` markers with sequential `[1]`, `[2]`, ...
4. Returns to the client:
   - `content`: text with inline `[1]`, `[2]`, ... markers.
   - `citations`: ordered array of citation objects.

The frontend renders each `[n]` as a clickable pill that expands the
corresponding citation object.

## "I don't know" behaviour

Triggered in two places:

1. **Empty retrieval** (pre-LLM): the LLM is never called. We return a
   hardcoded message: "I did not find relevant information in this
   assistant's documents to answer your question."

2. **Retrieval with results but the LLM decides it cannot answer**
   (post-LLM): the LLM follows rule 2 of the system prompt and returns
   the pre-formatted text.

In both cases, `citations=[]`.

## Critical tests

### `test_isolation.py`
```
1. Create assistant A with index A.
2. Create assistant B with index B.
3. Upload "legal.pdf" to A.
4. Upload "cooking.pdf" to B.
5. Query "contract clause" against assistant B.
6. Assert: B's retrieval returns zero chunks from A.
7. Query "contract clause" against assistant A.
8. Assert: A's retrieval returns chunks from legal.pdf.
```

### `test_parsers.py`
- One fixture file per format in `tests/fixtures/`.
- Verify the parser returns at least one `ParsedChunk` with non-empty
  text.
- Verify the PDF parser sets `page` correctly.

### `test_rag_prompt.py`
- With context: verify the prompt includes all three sections.
- Without context: verify the LLM is NOT called and the hardcoded message
  is returned.
- With long history: verify trimming to `HISTORY_MAX_MESSAGES`.

## Parameters that are hyperparameters (not constants)

Everything below lives in `.env` and can be tuned without touching code:

| Parameter                   | Default | Sensible range  |
|-----------------------------|---------|-----------------|
| `CHUNK_SIZE`                | 800     | 500 – 1200      |
| `CHUNK_OVERLAP`             | 150     | 80 – 250        |
| `RETRIEVAL_TOP_K`           | 5       | 3 – 10          |
| `RETRIEVAL_SCORE_THRESHOLD` | 1.5     | 1.0 – 2.5       |
| `HISTORY_MAX_MESSAGES`      | 10      | 4 – 20          |
| `QUERY_REWRITING_ENABLED`   | true    | true / false    |
| `QUERY_REWRITING_HISTORY_N` | 4       | 2 – 8           |
