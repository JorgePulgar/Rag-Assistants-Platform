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
