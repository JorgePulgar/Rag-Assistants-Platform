# TASKS — Phase-based Breakdown

Tasks are organised by **phase**, not by calendar day. A phase is a
self-contained unit of work with a concrete goal and a verifiable
checkpoint. Complete phases in order, but at your own pace — you can
finish a phase in one sitting, split it across two, or pause mid-phase
and resume later. The numbering (T001, T002, ...) is stable; references
between tasks stay valid regardless of when each task is done.

**How to use this file**:
- Always work on the next pending task whose dependencies are satisfied.
- Flip `[ ]` to `[x]` in the same commit that completes the task.
- Write one line to `docs/PROGRESS.md` at the end of each working
  session (not per task). Include which phase you advanced and any
  relevant notes.
- Do not add new tasks without Jorge's explicit approval.

---

## Phase 0 — Setup

**Goal**: the repo exists, both stacks boot, Azure resources are ready.

- [x] **T001** — Create the GitHub repo from the browser (manual, Jorge).
- [x] **T002** — Clone the repo locally, drop these documents into
  `/docs`, make the initial commit. ⬅ T001
- [x] **T003** — Azure setup: create Azure AI Foundry resource, deploy
  `gpt-4o-mini` and `text-embedding-3-small`. Create Azure AI Search
  resource (Basic tier or higher, semantic search enabled). Store
  credentials in a local `.env` (manual, Jorge — not Claude Code). ⬅ T001
- [x] **T004** — Backend scaffolding: folder structure, `requirements.txt`,
  FastAPI running on `:8000` with a `/health` endpoint, SQLAlchemy
  configured, SQLite auto-created on startup. ⬅ T002
- [x] **T005** — Frontend scaffolding: Vite + React + TS + Tailwind +
  shadcn init. `npm run dev` serves on `:5173` with a blank page. ⬅ T002
- [x] **T006** — Complete `.gitignore` (venv, node_modules, .env, .db,
  __pycache__, .vscode, .idea, dist, build). ⬅ T002
- [x] **T007** — `.env.example` in backend with every variable documented.
  ⬅ T004

**Phase 0 checkpoint**: backend serves `/health` returning 200, frontend
shows a blank page at `localhost:5173`, Azure resources are created,
`.env` exists locally with real credentials.

---

## Phase 1 — Assistant CRUD

**Goal**: create, list, edit, delete assistants through the API.

- [x] **T008** — SQLAlchemy models: `Assistant`, `Document`,
  `Conversation`, `Message`. Auto-migrate on startup. ⬅ T004
- [x] **T009** — Pydantic schemas for `Assistant` (Create, Update, Read).
  ⬅ T008
- [x] **T010** — Router `api/assistants.py` with the five CRUD endpoints.
  Logic in `services/assistant_service.py`. ⬅ T009
- [x] **T011** — Generate `search_index` name on assistant creation
  (string only; actual Azure index created in Phase 2). ⬅ T010
- [x] **T012** — Basic tests: create, list, update, delete an assistant.
  Using FastAPI's `TestClient`. ⬅ T010
- [x] **T013** — Commit and push.

**Phase 1 checkpoint**: `curl localhost:8000/api/assistants` returns `[]`,
`POST` with a valid body creates an assistant, `GET` lists it,
`PATCH`/`DELETE` work. Tests green.

---

## Phase 2 — Ingestion pipeline

**Goal**: uploading a document to an assistant results in its chunks
being indexed in that assistant's isolated Azure AI Search index, and
retrievable.

- [x] **T014** — Client `clients/azure_openai.py`: embeddings + LLM
  wrapper, reads config from `.env`. ⬅ T007
- [x] **T015** — Client `clients/azure_search.py`: wrapper for index
  creation, document upload, search. ⬅ T007
- [x] **T016** — Parsers: `pdf.py`, `docx.py`, `pptx.py`, `text.py`.
  Each returns `list[ParsedChunk]` per RAG_SPEC. ⬅ T004
- [x] **T017** — Parser tests with one fixture per format in
  `tests/fixtures/`. ⬅ T016
- [x] **T018** — `services/ingestion.py` `index_document` function:
  - resolve parser by extension
  - extract chunks
  - apply `RecursiveCharacterTextSplitter` with settings values
  - call embeddings in batches of 16
  - create the Azure Search index if it does not exist (per-assistant)
  - upload chunks with full metadata
  - update document status in SQLite
  ⬅ T014, T015, T016
- [x] **T019** — Pydantic schemas for `Document`. ⬅ T008
- [x] **T020** — Router `api/documents.py`: upload, list, delete.
  Upload via `UploadFile`, write temp file, call ingestion, remove temp.
  ⬅ T018
- [x] **T021** — Delete endpoint: remove chunks from the Azure Search
  index (filter by `document_id`) and the SQLite row. Deleting an
  assistant cascades to its documents and deletes the whole index. ⬅ T020
- [x] **T022** — Manual check: upload a real PDF to an assistant, verify
  in the Azure Portal that the index exists and contains chunks.
- [x] **T023** — Automatic isolation test (`test_isolation.py`,
  ingestion portion): two assistants, two different documents, verify
  no cross-contamination at the index level. ⬅ T018
- [x] **T024** — Commit and push.

**Phase 2 checkpoint**: uploading a PDF to an assistant correctly indexes
it in its own index, the isolation test passes, the document shows up in
the list endpoint with `status=indexed`.

---

## Phase 3 — Conceptual architecture diagram

**Goal**: a one-page visual diagram of the system that will live in the
repo and be referenced from the README.

- [x] **T025** — Draft the conceptual architecture diagram (Excalidraw
  preferred, Mermaid as fallback). Save source and PNG export to
  `docs/architecture.png` + `docs/architecture.excalidraw` (or `.mmd`).
  Must include:
  - Four boxes: Frontend (React), Backend (FastAPI), SQLite, Azure
    services (group: Foundry LLM, Foundry Embeddings, AI Search).
  - Directed arrows labelled with the operation (e.g. "POST /api/chat",
    "embed(query)", "hybrid search", "chat completion").
  - A numbered overlay (1–8) tracing the chat request flow described in
    `ARCHITECTURE.md` §"Chat request flow".
  - Per-assistant index convention noted next to AI Search
    (`assistant-{id_hex}`).
  Keep it one page, single view. No animations, no multiple frames.

**Phase 3 checkpoint**: `docs/architecture.png` exists and accurately
reflects the current implementation.

---

## Phase 4 — RAG chat with memory and citations

**Goal**: sending a message to an assistant returns an LLM response
grounded in its documents, with structured citations, and the assistant
remembers prior turns of the same conversation.

- [x] **T026** — `services/retrieval.py` `retrieve` function:
  - embed the query
  - hybrid query to Azure Search (keyword + vector + semantic rerank)
  - filter by score threshold
  - return the top_k chunks with full metadata
  ⬅ T014, T015
- [x] **T027** — Pydantic schemas for `Conversation` and `Message`,
  including `citations` JSON shape. ⬅ T008
- [x] **T028** — `services/rag.py` `generate_response` function:
  - load assistant and **last N messages** of the conversation from
    SQLite (this is the memory mechanism)
  - call retrieve for the current user message
  - if retrieve empty → hardcoded "I don't know" response, skip LLM
  - build the prompt per `RAG_SPEC.md`: system instructions + prior
    messages (history, with roles preserved) + retrieved context +
    current user question
  - call the LLM
  - post-process citations: extract `[CITE:chunk_id]`, resolve to
    structured objects
  - return `{content, citations}`
  ⬅ T026, T027
- [x] **T029** — Router `api/chat.py`:
  - `POST /conversations` creates a conversation
  - `GET /assistants/{id}/conversations` lists them
  - `GET /conversations/{id}/messages` returns full history
  - `POST /conversations/{id}/messages` persists the user message,
    calls `generate_response`, persists the assistant message with its
    citations, returns the assistant message
  - `DELETE /conversations/{id}`
  ⬅ T028
- [x] **T030** — Test `test_rag_prompt.py` covering the three RAG_SPEC
  cases: with context, without context, with long history (trim
  verification). ⬅ T028
- [x] **T031** — End-to-end isolation test: ask assistant B about a
  topic from assistant A's documents, verify "I don't know". ⬅ T029
- [x] **T032** — **Memory smoke test** (manual or scripted): send three
  sequential messages in one conversation where each one references the
  previous ("What does the contract say about clause 3?" → "And about
  clause 4?" → "Summarise what we discussed."). Verify the assistant
  answers coherently, demonstrating memory. ⬅ T029
- [x] **T033** — **Persistence smoke test** (manual): restart the
  backend process, reload the conversation via
  `GET /conversations/{id}/messages`, verify the full history is intact.
  ⬅ T029
- [x] **T034** — Commit and push.

**Phase 4 checkpoint**: `curl` to the chat endpoint on an assistant with
documents returns a coherent answer with citations; on an assistant
without documents returns the "I don't know" message; a three-turn
conversation demonstrates memory; backend restart preserves history.

---

## Phase 4.5 — Bugfixes and test remediation

**Goal**: fix two bugs in Phase 4 discovered during Phase 5 usage, and
audit the smoke-test-style tasks from earlier phases for real test
coverage.

**Context**: two bugs were found while exercising the app with real
documents.
1. **Bug 1**: sending a message to an assistant with no documents
   returned 500 "Failed to send message" instead of the hardcoded
   "I don't know" response. Root cause: Azure AI Search index was
   created lazily on first document upload; an assistant without
   documents has no index, and a query against a non-existent index
   raised `ResourceNotFoundError` that propagated as 500. This also
   violated `CONSTITUTION.md` §1 ("creating an assistant implies
   creating its index").
2. **Bug 2**: conversational memory failed on referential follow-ups
   ("tell me more about point 2"). Root cause: retrieval used the raw
   user message as the query, which for short referential phrases has
   no topical signal — Azure returned irrelevant chunks, the LLM
   received wrong context, and the answer went off-topic even though
   the history was loaded into the prompt correctly.

Additionally, the audit below confirmed that T032 was marked `[x]`
without a genuine test covering referential follow-ups — the manual
smoke test used self-contained questions that hid the real failure mode.

**Phase 4.5 blocks the start of Phase 6 polish work. Do NOT proceed
to Phase 6 until Phase 4.5's checkpoint passes.**

- [x] **T047a** — Update `docs/RAG_SPEC.md` with: (1) a new
  "Query rewriting" section describing the LLM-based standalone-query
  generation pattern; (2) a new "Index lifecycle" section clarifying
  that index creation is eager, not lazy, transactional with the
  SQLite row, per `CONSTITUTION.md` §1; (3) updated "Design note" in
  the History section. *(Done by Jorge beforehand — mark `[x]` on
  receipt.)*

- [x] **T047b** — Bug 1 fix (Option B, architectural): move index
  creation from `services/ingestion.py` (lazy, first upload) to
  `services/assistant_service.py` create path (eager). Call
  `azure_search.create_index_if_not_exists()` when the assistant row
  is committed. If index creation fails, roll back the SQLite row
  (transactional). The delete path already removes the index — verify.
  Also: in `services/retrieval.py`, add defensive handling for
  `ResourceNotFoundError` that logs the anomaly and returns `[]`
  (belt-and-braces; this path should no longer trigger under normal
  operation but protects against orphaned state). ⬅ T047a

- [x] **T047c** — Bug 2 fix: implement query rewriting per
  RAG_SPEC.md §"Query rewriting". New function in `services/rag.py`
  (or a new `services/query_rewriter.py`) that, when history exists,
  makes an LLM call to rewrite the user message into a standalone
  search query using the last `QUERY_REWRITING_HISTORY_N=4` history
  messages. The rewritten query is passed to `retrieve()`. The
  original user message is still what is stored in SQLite and shown
  in the UI. Feature-flagged behind `QUERY_REWRITING_ENABLED=true`.
  Log both original and rewritten queries at INFO level. ⬅ T047a

- [x] **T047d** — Automated test for Bug 1 fix in
  `backend/tests/test_idk_behaviour.py`:
  - Create an assistant with no documents.
  - Create a conversation on it.
  - POST a message.
  - Assert: response is 200.
  - Assert: response body contains the hardcoded "I don't have
    information…" string.
  - Assert: `citations` is empty.
  Must produce visible pytest output. No "I tried it manually"
  shortcuts. ⬅ T047b

- [x] **T047e** — Automated test for Bug 2 fix in
  `backend/tests/test_conversational_memory.py`:
  - Set up an assistant with a document containing two distinct topics
    (one test fixture PDF with two clearly separable sections).
  - Turn 1: ask a general question that produces an assistant answer
    listing both topics by number ("(1) topic A, (2) topic B").
  - Turn 2: send "tell me more about point 2".
  - Assert: the rewritten query (captured via log or by exposing a
    test hook on the rewriter) contains keywords from topic B and NOT
    from topic A.
  - Assert: the retrieved chunks for turn 2 are the chunks tagged as
    topic B in the fixture.
  Must produce visible pytest output. ⬅ T047c

- [x] **T047f** — Retrospective audit of T023 (isolation, Phase 2),
  T030 (RAG prompt cases, Phase 4), T031 (E2E isolation, Phase 4),
  T032 (memory smoke test, Phase 4), T033 (persistence smoke test,
  Phase 4). For each:
  1. Inspect the test file (or lack thereof).
  2. Run the test and capture output.
  3. If the task was marked `[x]` without a real automated test, write
     one now.
  4. Document the audit result in `docs/PROGRESS.md` with one line per
     audited task: "T0XX — [pass / rewritten / added]". ⬅ T047b, T047c

- [x] **T047g** — Phase 4.5 final commit and push. Note: per
  `CONSTITUTION.md` §7, T047b through T047f each had their own
  commit. This task is just the final push and PROGRESS.md update.

**Phase 4.5 checkpoint**: both bugs fixed, both regression tests green,
retrospective audit complete and documented in PROGRESS.md, all commits
pushed.

---

### Phase 4.5 — Follow-up fixes (post-testing)
 
**Context**: after Phase 4.5 closed with T047a–T047g, real UI testing
surfaced three remaining issues. These are not new bugs — they are
residual symptoms of the same areas Phase 4.5 touched, and are fixed
in this follow-up batch before moving on to Phase 6. The updated
prompts (both for the RAG and the rewriter) and the skip-retrieval
logic for no-search intent are already specified in the updated
`RAG_SPEC.md` sections §"System prompt" and §"Query rewriting".
 
- [x] **T047h** — Sync system prompts in code with updated
  `RAG_SPEC.md`:
  - Update the RAG system prompt in `services/rag.py` (or wherever
    it lives) to match the new 6-rule version in RAG_SPEC §"System
    prompt", including the elaboration allowance in Rule 1, the
    citation-format rules of Rule 3, and the language rule of Rule 6.
  - Update the rewriter system prompt in
    `services/query_rewriter.py` to match the new expanded version
    in RAG_SPEC §"Query rewriting", including the four examples and
    the NO-SEARCH INTENT rule.
  Do not invent wording; copy the prompts verbatim from the spec.
  *(Done manually by Jorge; marked [x] on acceptance.)*
- [x] **T047i** — Skip retrieval on no-search intent, per RAG_SPEC
  §"Query rewriting" →"No-search intent handling in code". In
  `services/rag.py` (or `services/query_rewriter.py`), after the
  rewriter returns, detect no-search intent using the heuristic in
  the spec (rewritten == original AND short/chit-chat). If detected:
  - Skip the retrieval step entirely.
  - Call the LLM with only the system prompt + history + user
    message (no CONTEXT block).
  - Return the response with `citations=[]`.
  - Log at INFO level that retrieval was skipped due to no-search
    intent.
  ⬅ T047h
- [x] **T047j** — Frontend fix: the amber "warning" style
  (`AlertCircle` icon + neutral-600 text, per `FRONTEND_SPEC.md`
  §"I don't know state") must apply ONLY to the hardcoded
  "I don't have information…" response, not to every assistant
  message. Current behaviour applies it to every assistant bubble.
  Fix: in `MessageBubble` (or the relevant component), detect the
  hardcoded message by exact prefix match on the known string and
  apply the warning style only in that case. All other assistant
  messages use the default assistant style from FRONTEND_SPEC
  §"Assistant message".
- [x] **T047k** — Citation rendering fix: inline `[CITE:chunk_id]`
  markers sometimes render as literal text instead of being replaced
  by `[1]`, `[2]`, ... clickable pills. Diagnose in the backend
  post-processing function (likely in `services/rag.py`) — inspect
  the regex used to extract chunk IDs and verify it handles the
  actual chunk_id format (UUID with dashes, or whatever format is
  produced by the ingestion pipeline). Add a unit test covering at
  least three cases: single citation, multiple consecutive citations
  (`[CITE:id1][CITE:id2]`), and citation at end of sentence. On the
  frontend side, verify `CitationBlock` correctly renders `[1]`
  pills from the `citations` array. ⬅ T047h
- [x] **T047l** — Automated regression test for the elaboration case
  that was failing (Rule 1 fix). In
  `backend/tests/test_conversational_memory.py` or a new file, add
  a test that:
  - Sets up an assistant with a document containing explainable
    content.
  - Turn 1: asks a question that elicits a structured answer.
  - Turn 2: asks "can you expand more on that last part?" (or
    equivalent Spanish phrasing).
  - Asserts: the assistant response is NOT the hardcoded "I don't
    know" string AND contains more than a trivial character count
    (e.g., > 100 chars).
  Must produce visible pytest output. ⬅ T047h
- [X] **T047n** — Automated regression test for the "exemplify" case
  (Rule 7 EXEMPLIFY mode). In the same test file as T047l, add a
  test that:
  - Sets up an assistant with a document explaining some concept with
    at least one example.
  - Turn 1: asks about the concept. Verify the assistant answers with
    the document's example.
  - Turn 2: asks "can you give me more examples?" (or equivalent
    Spanish phrasing).
  - Asserts: the assistant response is NOT the hardcoded "I don't
    know" string AND contains at least one example distinct from the
    one given in turn 1 (simple check: different keywords or entities
    appear).
  This test guards against regression to the pre-Phase-4.5-followup
  behaviour where "more examples" triggered the fallback path.
  Must produce visible pytest output. ⬅ T047h
- [X] **T047m** — Follow-up commits and push. Each of T047h–T047n
  gets its own commit per CONSTITUTION §7. This task is just the
  final push and a PROGRESS.md line summarising the follow-up batch.

**Phase 4.5 final checkpoint** (supersedes the previous one): both
original bugs fixed, all three follow-up issues fixed, prompts in code
match the spec, regression tests green for elaboration and
conversational memory, frontend applies warning style only to the
hardcoded message, citations render as pills consistently.

---

## Phase 5 — Frontend

**Goal**: functional UI with the three views wired to the backend.
 
> **Before starting Phase 5**, read `docs/FRONTEND_SPEC.md`. It is the
> authoritative source for layout, colour palette, typography, component
> styling, and microcopy. Every task in this phase must comply with it.
> If something is not specified there, ask Jorge before improvising.
 
- [x] **T035** — *(Optional, 45–60 min)* Quick wireframe pass for the
  three views (assistant list, assistant detail, chat) in Excalidraw or
  on paper. Decide layout only: sidebar position, citation block
  placement, document uploader placement. If skipped, rely on
  `FRONTEND_SPEC.md` defaults.
- [x] **T035b** — Theme setup per `FRONTEND_SPEC.md`: Tailwind config
  with `darkMode: 'class'`, `ThemeProvider` at root with system
  preference default and `localStorage` override, theme toggle button
  in the header (Sun/Moon icons from lucide). Load Inter from Google
  Fonts. ⬅ T005
- [x] **T036** — API client in `frontend/src/api/client.ts` with axios.
  TS types mirroring the Pydantic schemas. ⬅ T005
- [x] **T037** — Main layout: sidebar with assistant list + main area. ⬅ T036
- [x] **T038** — Assistant list view: card per assistant, "New" button,
  edit/delete buttons per card. ⬅ T037
- [x] **T039** — Assistant create/edit form inside a shadcn Dialog
  (name, instructions, description). Basic validation. ⬅ T038
- [x] **T040** — Assistant detail view: info + document list + uploader.
  ⬅ T038
- [x] **T041** — Document uploader: file input + upload button +
  progress + list with a delete button per document. ⬅ T040
- [x] **T042** — Chat view: conversation list (per assistant),
  conversation selector, "new conversation" button, message history,
  message input, send button. ⬅ T037
- [x] **T043** — `MessageBubble` component with visual distinction
  between user and assistant. ⬅ T042
- [x] **T044** — `CitationBlock` component: `[1]`, `[2]` inline pills +
  expandable panel on click with document name, page, snippet. ⬅ T042
- [x] **T045** — "Assistant is thinking" loading state in the chat
  (skeleton or spinner in the assistant bubble). ⬅ T042
- [x] **T046** — Error toasts (shadcn) for failed requests. ⬅ T036
- [x] **T047** — Commit and push.

**Phase 5 checkpoint**: full end-to-end flow works from the browser —
create assistant, upload document, start conversation, ask questions,
see citations, start a new conversation, reopen an old one.

---

## Phase 6 — Polish and edge cases
 
**Goal**: robust enough to demo, no obvious bugs, no awkward empty or
error states.
 
- [x] **T048** — Run the full flow three times with real, distinct
  documents. Write every bug found into a short list.
- [x] **T049** — Fix the bugs from T048 (open-ended, N sub-bugs).
- [x] **T050** — Ingestion edge cases: corrupt PDF, empty file,
  unsupported format, file > 10MB. Each case must return a clean error,
  never a 500. ⬅ T018
- [x] **T051** — Chat edge cases: conversation with a deleted assistant,
  empty message, very long message. ⬅ T029
- [x] **T052** — Loading states in the frontend for every async
  operation. ⬅ T036
- [x] **T053** — Empty states: "no assistants yet", "no documents on
  this assistant", "start a conversation". ⬅ T037
- [x] **T054** — Destructive confirmations: "are you sure you want to
  delete this assistant? X documents and Y conversations will be
  deleted". ⬅ T038
- [x] **T055** — Visual polish: coherent palette, spacing, typography.
  One global pass, no perfectionism. ⬅ T037
- [x] **T055b** — Citation pill rendering fix: residual `[CITE:id]`
  literal text sometimes appears immediately before or after the
  rendered `[N]` pill (observed example: `[CITE:12][1]` where `[1]`
  is the correct pill and `[CITE:12]` is leftover literal text).
  Root cause likely: the regex replacement in the backend
  post-processing misses some marker variants (whitespace, casing,
  trailing punctuation, or a chunk_id that was not in the retrieval
  result). Diagnose in `services/rag.py` `_post_process`:
  1. Log every `[CITE:...]` marker found in the LLM response vs.
     every marker successfully replaced — identify which ones are
     slipping through.
  2. Cover the gaps: either extend the regex to catch the missed
     variants, OR strip any remaining `[CITE:...]` literals from the
     final content after the known-id replacement pass (fallback
     cleanup).
  3. Add a unit test with a response containing: a valid citation, a
     citation whose chunk_id is NOT in retrieved chunks (should be
     stripped), and consecutive citations (`[CITE:a][CITE:b]`).
  ⬅ T055
- [x] **T056** — Commit and push.

- [x] **T048b** — `[BLOCKS ON: Jorge upload]` Real end-to-end runs.
  Until this task, T048 was satisfied only via static code review
  (commit `4c8b11c`). Now that the code is in a polished state, run
  the full flow manually with real content:
  1. Jorge uploads 2–3 real PDF/DOCX/PPTX documents to at least
     two assistants.
  2. Run the full flow three times: create assistants, upload docs,
     start conversations, ask questions, follow-ups, switch
     assistants, reload the browser, etc.
  3. Append every newly found bug to `docs/bugs_t048.md` as B8, B9,
     B10, ... — with the same format as B1–B7 (description, where,
     impact, fix proposal).
  4. Mark `[x]` only after Jorge explicitly confirms the runs
     happened. Do NOT auto-mark from a code review.
  Bugs found here trigger follow-up fix tasks (T048b1, T048b2, ...)
  if needed. ⬅ T056
  
**Phase 6 checkpoint**: a user who has never seen the app can use it
without asking questions and without getting stuck.
 
---
 
## Phase 6.5 — Real-content fixes
 
**Goal**: fix two bugs (B8, B9) discovered during the T048b real-content
end-to-end run that did not exist in the static code review of T048.
Both surfaced only when running the full RAG flow with real Spanish
documents and PPTX content.
 
**Phase 6.5 blocks Phase 7 — do NOT start Phase 7 until 6.5 is done.**
 
- [x] **T057a** — B8 fix: language-independent "I don't know" detection.
  The amber warning style (`AlertCircle` icon + neutral-600 text per
  `FRONTEND_SPEC.md` §"I don't know state") currently relies on
  frontend prefix matching against English strings only. When the LLM
  follows Rule 6 and returns the Rule-2 fallback in Spanish, the
  warning style is not applied.
  
  Implementation:
  1. **Backend**: add a boolean `is_fallback` field to
     `MessageRead` and `SendMessageResponse` schemas. Set `True` when
     `_NO_CONTEXT_RESPONSE` is returned (no LLM call) OR when the LLM
     was called but produced an output that opens with the Rule-2
     fallback pattern (detect via a stable substring like "What I
     looked for" / "Lo que busqué" — language-agnostic enough to
     catch both, and any future translations should preserve a
     similar marker).
  2. **Backend persistence**: also store `is_fallback` on the
     `Message` model so reloaded conversations keep the styling.
     Migration handled by SQLAlchemy `create_all` since SQLite has
     no live migrations here.
  3. **Frontend**: in `MessageBubble.tsx`, replace the `IDK_PREFIXES`
     string-matching logic with a check on `message.is_fallback`.
     Remove `IDK_PREFIXES`.
  4. **Test**: add a backend test that sends a Spanish question
     to an assistant with no relevant chunks, asserts the response
     has `is_fallback=true`, and asserts the same after reloading
     via `GET /conversations/{id}/messages`.
  Must produce visible pytest output. ⬅ T056
- [ ] **T057b** — B9 fix: surface citations even when the LLM omits
  them. With short PPTX-derived chunks the LLM sometimes produces a
  correct, grounded answer but no `[CITE:...]` markers, violating
  Citation Rule 3. We cannot force the LLM to cite retroactively, but
  we can surface the sources that fed the response so the user keeps
  the trace.
  
  Implementation:
  1. **Backend**: in `services/rag.py` `_post_process`, after the
     normal citation extraction, if `chunks` is non-empty AND
     `citations` came back empty, log a WARNING with the
     `assistant_id` and `conversation_id`, AND populate `citations`
     with the top retrieved chunks marked as "implicit sources"
     (add a boolean field `implicit: bool` to each citation object;
     `False` for normal citations, `True` for these synthetic ones).
     Limit to the top 3 chunks to avoid noise.
  2. **Frontend**: render implicit citations differently from explicit
     ones — same expandable popover content, but the pill is grouped
     under a small label below the message ("Sources consulted:" /
     similar) instead of inline `[N]` markers. Use a slightly muted
     style (e.g. `text-neutral-500` instead of the blue accent) to
     distinguish them from cited claims.
  3. **Test**: backend test with a mocked LLM response that returns
     no `[CITE:...]` markers; assert the response has
     `citations.length > 0` and every citation has `implicit=true`.
  4. **Spec update**: extend `RAG_SPEC.md` §"Response post-processing"
     to document the implicit-citations fallback.
  Must produce visible pytest output. ⬅ T056
- [ ] **T057c** — Phase 6.5 final commit and push. Each of T057a and
  T057b had its own commit per CONSTITUTION §7. This task is just the
  final push and a one-line `PROGRESS.md` summary.
**Phase 6.5 checkpoint**: B8 and B9 fixed, both regression tests
green, RAG_SPEC updated for implicit citations, frontend styles both
fallback responses (any language) and implicit citations correctly.
 
---
 
## Phase 7 — Deliverables
 
**Goal**: README and final diagram ready for submission.
 
- [ ] **T057** — Final `PROGRESS.md`: snapshot of the project state.
- [ ] **T058** — Review the architecture diagram from T025. If the real
  implementation drifted from the initial draft (new services, renamed
  endpoints, added flows), update the diagram. Re-export PNG. ⬅ T025
- [ ] **T059** — Write the complete English `README.md`:
  - Product description
  - Technology stack
  - Architecture (embed T058 image)
  - Key design decisions (reference CONSTITUTION and RAG_SPEC)
  - Step-by-step local setup (backend + frontend)
  - How the core is satisfied: isolation, persistence + memory, citations,
    "I don't know" behaviour
  - Known limitations (including: no cross-conversation memory, no
    authentication, no OCR, etc.)
  ⬅ T058
- [ ] **T060** — Write the Spanish courtesy `README.es.md`: shorter,
  links back to the English README for technical depth. ⬅ T059
- [ ] **T061** — Prepare two demo assistants with 2–3 documents each
  (e.g. "2024 Tax Expert" with Spanish tax authority guides, "Italian
  Cooking Assistant" with recipe books). Data stays in Spanish; UI is
  in English.
- [ ] **T065** — Final commit tagged `v1.0`.
**Phase 7 checkpoint**: repo and README publishable as-is. Demo video
(recorded separately by Jorge, not tracked as a task) is linked from
the README when available.
 
> **Note**: the demo video (3–5 min) is a required deliverable per the
> project brief, but it is recorded and uploaded manually by Jorge
> outside the task pipeline. It is not T062–T064 anymore — those
> tasks were removed on decision.
 
---
 
## Phase 8 — Optional extras
 
**Goal**: improvements to ship if there is time and energy. Nothing
here is required for the academic deliverable. Each task is
independent and can be tackled in any order. Pick by value vs effort.
 
Effort ratings below are rough: **S** = small (1–2h), **M** = medium
(3–5h), **L** = large (6+h).
 
- [ ] **T066** — *(S, high user value)* Resizable sidebar. The
  left sidebar should be user-resizable by dragging its right edge.
  Constraints: minimum width 200px (so it cannot be collapsed to
  unusable), maximum width equal to current fixed width (280px per
  `FRONTEND_SPEC.md`). Persist the chosen width in `localStorage`
  so it survives reloads. Resize handle visible on hover; use the
  `cursor: col-resize` style. No change to sidebar content or the
  rest of the layout.
- [ ] **T067** — *(M, medium user value)* Document upload
  feedback:
  - Progress indicator during upload: for each file being uploaded,
    show a progress bar or percentage in the document list row.
    Source the progress from the `onUploadProgress` callback of
    axios so it reflects the HTTP request, not the server-side
    parsing.
  - Server-side processing feedback: after the HTTP upload completes,
    the document row transitions to a "Processing…" state with a
    small animated indicator until the backend returns
    `status=indexed`. Poll the documents list endpoint every 2s
    until the status changes.
  - Heavy-file warning: when a user selects a file > 3MB, show an
    inline note before upload: "Large file — processing may take up
    to a minute".
  No backend changes needed if the documents endpoint already
  returns `status` per document.
- [ ] **T068** — *(M, high user value)* Conversation management:
  rename, delete, and export. For each conversation, expose three
  actions:
  - **Rename**: inline edit of the conversation title (both in the
    sidebar/list and from within an open chat). Backend endpoint
    `PATCH /api/conversations/{id}` with a `title` field.
  - **Delete**: confirmation dialog reusing the same pattern as
    T054. Removes the conversation and all its messages.
  - **Export**: download the conversation as a Markdown file
    (`conversation-{title}-{date}.md`) containing the assistant
    name, timestamp, and all messages with roles and citations
    expanded (document name + page + snippet).
  All three actions accessible both from the conversation list (as
  icon + text buttons, same style as the existing "Edit" button on
  assistants) and from inside an open chat (e.g. in the chat header
  strip).
- [ ] **T069** — *(M, medium user value)* Chat tabs in the main
  area. Replace the single-chat main area with a tabbed interface:
  - Each open conversation lives in its own tab at the top of the
    main area (tab bar style similar to VS Code or Chrome).
  - Clicking an assistant in the sidebar opens (or focuses) its
    most recent conversation as a tab.
  - Tabs can be closed individually with an `×` button.
  - Tab state (which tabs are open, which is active) persists in
    `localStorage` across reloads.
  - A new "+" button on the tab bar opens a new conversation for
    the currently selected assistant.
  Does NOT include split panels — that is T070.
- [ ] **T070** — *(L, lower user value)* Split panels with
  drag-and-drop tabs. Extend T069 so that tabs can be dragged to
  the edges of the main area to create split panels, VS Code
  style:
  - Dragging a tab to the right edge of the main area creates a
    vertical split; the tab docks as the only tab of the new
    right panel.
  - Each resulting panel has its own independent tab bar.
  - Tabs can be dragged between panels, re-ordered within a panel,
    or moved back to merge panels (dropping the last tab onto the
    other panel collapses the split).
  - Split configuration persists in `localStorage`.
  - Minimum panel width 300px; smaller than that, the split
    doesn't form on drag.
  This is the most complex extra by a wide margin. Recommended
  libraries: `react-dnd` for drag-and-drop; consider
  `react-resizable-panels` for the split layout itself rather
  than hand-rolling it. ⬅ T069
---

## Rules for Claude Code about this file

- At the start of every session, read this file and work on the next
  pending task whose dependencies are satisfied.
- Flip `[ ]` to `[x]` in the same commit that completes the task.
- Write one line to `docs/PROGRESS.md` at the end of the session,
  indicating which phase you advanced and any noteworthy decisions.
- Do not add new tasks without Jorge's explicit approval.
- If a task turns out to be larger than estimated, split it into
  sub-tasks (T018a, T018b, ...) before starting, not during.
- Phases should be completed in order. Do not start Phase N+1 until
  Phase N's checkpoint passes, unless Jorge explicitly says otherwise.
