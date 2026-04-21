# CONSTITUTION — Non-negotiable Project Principles

This document captures the rules that are **not up for discussion** during
development. Every technical decision must respect these principles. If a
proposal violates them, the proposal is rejected — not the other way around.

---

## 1. Structural isolation per assistant

Each assistant has its own **Azure AI Search index**, named deterministically
from its ID. Isolation is **structural**, not logical: we never share a
global index with `assistant_id` filters.

**Rationale**: a bug in a filter contaminates every answer silently. A bug
in index naming fails loudly instead. The project brief explicitly requires
demonstrating isolation in the demo; this decision makes it trivial.

**Consequence**: creating an assistant implies creating an index. Deleting
an assistant implies deleting the index. These operations are transactional
with the SQLite row.

## 2. Citations are always structured

Chat responses return citations as **structured JSON objects**, never as
inline strings. Minimum schema:

```json
{
  "document_id": "uuid",
  "document_name": "contract_2024.pdf",
  "page": 3,
  "chunk_text": "relevant excerpt, max 300 characters"
}
```

**Rationale**: the frontend renders citations as expandable blocks. Inline
strings like `[Doc 1, p. 3]` cannot be rendered reliably and break as soon
as the LLM decides to phrase them differently.

## 3. Never fabricate answers

If retrieval does not return chunks above the score threshold, the assistant
explicitly replies that it **does not have the information** to answer. The
system prompt enforces this, and the endpoint returns the response with an
empty citation array.

The "I don't know" response must be **informative**: what was searched, why
nothing was found. Not a generic string.

**Rationale**: the brief explicitly requires this behaviour. On top of that,
a hallucination during the demo invalidates the whole project in front of
the evaluator.

## 4. Explicit and persistent conversational memory

Conversational memory is a **core feature** of this project, not a
side-effect. Every conversation stores in SQLite its `conversation_id`,
`assistant_id`, and every message with its role (`user` | `assistant`),
content, citations (when applicable), and timestamp.

**Requirements**:
- When resuming a conversation, the full history is loaded from the
  database — we never rely on in-memory server state.
- The assistant's LLM call always includes the last
  `HISTORY_MAX_MESSAGES` messages as prior context, so the assistant
  genuinely "remembers" what was said earlier in the same conversation.
- Conversations survive backend restarts, browser closes, and machine
  reboots. The only state required is the SQLite file on disk and the
  Azure Search indexes.
- A user can list their previous conversations per assistant, reopen any
  of them, and continue exactly where they left off.

**Explicit non-goal**: we do not implement cross-conversation memory
(the assistant remembering facts about the user across separate
conversations). That is a different system entirely and is out of scope
for this MVP. It is documented as a known limitation in the final README.

**Rationale**: the brief requires persistence explicitly, and a stateless
or in-memory chat would fail acceptance criterion 5 (close the browser,
reopen, continue the same conversation). On top of that, stateful-on-disk
is a basic good practice that signals architectural maturity.

## 5. Minimum tests on core logic

We do not require high coverage, but we **do require** tests for:

- Isolation: create two assistants, upload different documents to each,
  verify that a query to one never retrieves chunks from the other.
- Parsing: at least one test per supported document type.
- RAG prompt construction: verify that the prompt includes instructions +
  history + context, and that the "I don't know" path triggers on empty
  context.

**Rationale**: these are the spots where a silent bug costs you the grade.
An isolation test that runs in ten seconds saves a dramatic moment in the
demo.

## 6. Environment variables for anything configurable

Zero credentials in code. Zero hardcoded URLs. Everything lives in `.env`,
documented in `.env.example`. This includes Azure endpoints, API keys, base
index naming, chunking parameters, and LLM deployment names.

## 7. Incremental commits with conventional messages

`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`. One commit per
coherent task. Push daily at minimum. The repository history is part of
the deliverable, not a by-product.

## 8. The final README is written at the end

During development we keep a minimal README and a live `PROGRESS.md`. The
full README is written on Day 6 with hindsight. We do not maintain full
documentation in parallel with development.
