# Phase 6 Bug Audit — T048

Code-review audit conducted before live test sessions.

## B1 — No file size limit before reading into memory
**File**: `backend/app/api/documents.py`, `upload_document`
`content = await file.read()` reads the entire upload into process memory with no size guard.
A file > 10 MB is accepted silently; the parser may fail eventually but the full content was
already buffered, risking memory pressure or timeout.
**Fix (T050)**: check `len(content) > 10 MB` after read; return HTTP 413 and skip document creation.

## B2 — Empty message content accepted
**File**: `backend/app/schemas/chat.py`, `MessageCreate`
`content: str` has no minimum-length validator.
An empty string passes Pydantic, calls the query rewriter with empty text, and embeds it.
**Fix (T051)**: `Field(min_length=1)`.

## B3 — Very long message content not bounded
**File**: `backend/app/schemas/chat.py`, `MessageCreate`
No maximum-length validator on `content`.
A multi-megabyte message would be embedded and sent to the LLM, likely exceeding the Azure
context window and surfacing an unhandled `openai.BadRequestError` → HTTP 500.
**Fix (T051)**: `Field(max_length=20_000)`.

## B4 — Hallucinated [CITE:...] markers not stripped from final content
**File**: `backend/app/services/rag.py`, `_post_process`
If the LLM cites a `chunk_id` not present in the retrieved results, the marker remains as
literal `[CITE:some-id]` text in the content returned to the client and rendered in the UI.
**Fix (T055b)**: after the per-ID replacement pass, strip any remaining `[CITE:…]` patterns.

## B5 — "Start new conversation" button has no loading indicator
**File**: `frontend/src/pages/AssistantDetailPage.tsx`, `handleStartNewConversation`
The async call has no in-flight indicator; double-clicking creates duplicate conversations.
**Fix (T052)**: disable button and show spinner while the request is in flight.

## B6 — Delete-assistant confirmation body omits conversation count
**File**: `frontend/src/pages/AssistantDetailPage.tsx`, delete dialog
Dialog body reads "all conversations" rather than the actual count.
FRONTEND_SPEC microcopy: "This will delete X documents and Y conversations. This cannot be undone."
**Fix (T054)**: use `conversations.length` in the dialog body.

## B7 — User and assistant messages share the same timestamp
**File**: `backend/app/services/chat_service.py`, `send_message`
`now` is captured once after `generate_response` returns; both the user message and the
assistant message are persisted with identical `created_at` values.
`get_messages` sorts by `created_at asc`; when timestamps are equal the order is
implementation-defined and the assistant message could appear before the user message.
**Fix (T049)**: give the assistant message a timestamp 1 ms after the user message.

---

## T048b — Real-content E2E run (2026-04-25)

Smoke script: `scripts/smoke/t048b_e2e.py`
Documents: `Documentacion_LLM_Completa.docx` (DOCX → Assistant 1),
           `RAG_Documentation.pptx` (PPTX → Assistant 2)
Run: 68 checks — 67 pass, 1 false-positive (explained below), 0 real failures.

### Script false-positive note
The isolation check flagged the RAG Expert's response to a question about
Transformers/LLM training as a "bug" because the Spanish IDK string
("No tengo suficiente información en mis documentos…") didn't match the
English detection patterns in the script. The isolation IS working
correctly — the assistant cannot answer questions outside its document
set. The false positive is in the detection logic of the smoke script,
not in the application.

## B8 — Non-English IDK responses do not receive the warning style in the UI
**File**: `frontend/src/components/MessageBubble.tsx`, `IDK_PREFIXES`
**Found**: T048b real-content run (2026-04-25)

When the user writes in a non-English language, Language Rule 6 ("Always respond
in the same language as the user's prompt") causes the LLM to translate the
Rule-2 STRICT FALLBACK response. Example observed in the smoke run:

> "No tengo suficiente información en mis documentos para responder esta pregunta.
>  Lo que busqué: …"

The `IDK_PREFIXES` array contains only the two English prefix strings:
- `"I did not find relevant information…"` (hardcoded `_NO_CONTEXT_RESPONSE`)
- `"I don't have enough information…"` (LLM Rule-2 in English)

Neither matches the Spanish translation, so `isIdk` is `false` and the amber
`AlertCircle` warning style is never applied.

Note: the hardcoded `_NO_CONTEXT_RESPONSE` is always English (it bypasses the LLM
entirely), so it is always styled correctly. Only the LLM-generated Rule-2 path
is affected for non-English prompts.

**Impact**: medium — the assistant still returns correct content; only the amber
warning indicator is missing, so the user does not know the answer came from the
"I don't know" path.

**Fix proposal**: Detect the "I don't know" state on the backend instead of via
string matching on the frontend. Options:
  (a) Add a boolean `is_fallback` field to `SendMessageResponse` / `MessageRead`
      set to `true` whenever `_NO_CONTEXT_RESPONSE` or Rule-2 is returned.
  (b) Check `citations === empty AND content is non-empty AND the LLM was called`
      (requires a flag from the service layer).
  Simplest: option (a) — backend sets the flag, frontend renders warning style
  when `message.is_fallback === true`, removing all language-dependent string
  matching.

## B9 — LLM omits citation markers for PPTX-derived context
**File**: `backend/app/services/rag.py` (prompt / LLM non-determinism)
**Found**: T048b real-content run (2026-04-25)

In Flow B (RAG Expert, PPTX document), Turn B1 ("¿Qué es RAG y cuáles son sus
componentes principales?"):
- Retrieval returned chunks above the 1.2 score threshold (confirmed by the
  substantive response — if retrieval had returned empty, the hardcoded English
  response would have been returned instead).
- The LLM was called with a context block containing the PPTX chunks.
- The LLM generated a correct, coherent answer about RAG (in Spanish, following
  Language Rule 6).
- **But the LLM used zero `[CITE:chunk_id]` markers**, producing 0 citations in
  the final response.

In contrast, Flow A (LLM Expert, DOCX document) Turn A1 produced 4 correctly
structured citations.

PPTX slides produce shorter, more generic chunks (titles, bullet-point fragments)
compared to DOCX paragraphs. The LLM appears to treat such chunks as implicit
background rather than citable sources, silently breaking Citation Rule 3
("You MUST cite sources immediately after the relevant claim").

**Impact**: medium — the user receives correct content but no clickable citation
pills, violating the transparency guarantee of the RAG pipeline.

**Fix proposal**: Strengthen Citation Rule 3 in the system prompt to make
non-citation a more explicit violation, and/or add a post-processing check:
if chunks were retrieved and `citations == []` after `_post_process`, log a
WARNING and optionally append a synthetic "Sources consulted: …" footer.
This will not force the LLM to cite retroactively, but will surface the
anomaly for monitoring and alert the user that sources exist.
