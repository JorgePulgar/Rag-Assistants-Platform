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

- [ ] **T025** — Draft the conceptual architecture diagram (Excalidraw
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

- [ ] **T026** — `services/retrieval.py` `retrieve` function:
  - embed the query
  - hybrid query to Azure Search (keyword + vector + semantic rerank)
  - filter by score threshold
  - return the top_k chunks with full metadata
  ⬅ T014, T015
- [ ] **T027** — Pydantic schemas for `Conversation` and `Message`,
  including `citations` JSON shape. ⬅ T008
- [ ] **T028** — `services/rag.py` `generate_response` function:
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
- [ ] **T029** — Router `api/chat.py`:
  - `POST /conversations` creates a conversation
  - `GET /assistants/{id}/conversations` lists them
  - `GET /conversations/{id}/messages` returns full history
  - `POST /conversations/{id}/messages` persists the user message,
    calls `generate_response`, persists the assistant message with its
    citations, returns the assistant message
  - `DELETE /conversations/{id}`
  ⬅ T028
- [ ] **T030** — Test `test_rag_prompt.py` covering the three RAG_SPEC
  cases: with context, without context, with long history (trim
  verification). ⬅ T028
- [ ] **T031** — End-to-end isolation test: ask assistant B about a
  topic from assistant A's documents, verify "I don't know". ⬅ T029
- [ ] **T032** — **Memory smoke test** (manual or scripted): send three
  sequential messages in one conversation where each one references the
  previous ("What does the contract say about clause 3?" → "And about
  clause 4?" → "Summarise what we discussed."). Verify the assistant
  answers coherently, demonstrating memory. ⬅ T029
- [ ] **T033** — **Persistence smoke test** (manual): restart the
  backend process, reload the conversation via
  `GET /conversations/{id}/messages`, verify the full history is intact.
  ⬅ T029
- [ ] **T034** — Commit and push.

**Phase 4 checkpoint**: `curl` to the chat endpoint on an assistant with
documents returns a coherent answer with citations; on an assistant
without documents returns the "I don't know" message; a three-turn
conversation demonstrates memory; backend restart preserves history.

---

## Phase 5 — Frontend

**Goal**: functional UI with the three views wired to the backend.

- [ ] **T035** — *(Optional, 45–60 min)* Quick wireframe pass for the
  three views (assistant list, assistant detail, chat) in Excalidraw or
  on paper. Decide layout only: sidebar position, citation block
  placement, document uploader placement. If skipped, rely on the
  `frontend-design` skill defaults.
- [ ] **T036** — API client in `frontend/src/api/client.ts` with axios.
  TS types mirroring the Pydantic schemas. ⬅ T005
- [ ] **T037** — Main layout: sidebar with assistant list + main area. ⬅ T036
- [ ] **T038** — Assistant list view: card per assistant, "New" button,
  edit/delete buttons per card. ⬅ T037
- [ ] **T039** — Assistant create/edit form inside a shadcn Dialog
  (name, instructions, description). Basic validation. ⬅ T038
- [ ] **T040** — Assistant detail view: info + document list + uploader.
  ⬅ T038
- [ ] **T041** — Document uploader: file input + upload button +
  progress + list with a delete button per document. ⬅ T040
- [ ] **T042** — Chat view: conversation list (per assistant),
  conversation selector, "new conversation" button, message history,
  message input, send button. ⬅ T037
- [ ] **T043** — `MessageBubble` component with visual distinction
  between user and assistant. ⬅ T042
- [ ] **T044** — `CitationBlock` component: `[1]`, `[2]` inline pills +
  expandable panel on click with document name, page, snippet. ⬅ T042
- [ ] **T045** — "Assistant is thinking" loading state in the chat
  (skeleton or spinner in the assistant bubble). ⬅ T042
- [ ] **T046** — Error toasts (shadcn) for failed requests. ⬅ T036
- [ ] **T047** — Commit and push.

**Phase 5 checkpoint**: full end-to-end flow works from the browser —
create assistant, upload document, start conversation, ask questions,
see citations, start a new conversation, reopen an old one.

---

## Phase 6 — Polish and edge cases

**Goal**: robust enough to demo, no obvious bugs, no awkward empty or
error states.

- [ ] **T048** — Run the full flow three times with real, distinct
  documents. Write every bug found into a short list.
- [ ] **T049** — Fix the bugs from T048 (open-ended, N sub-bugs).
- [ ] **T050** — Ingestion edge cases: corrupt PDF, empty file,
  unsupported format, file > 10MB. Each case must return a clean error,
  never a 500. ⬅ T018
- [ ] **T051** — Chat edge cases: conversation with a deleted assistant,
  empty message, very long message. ⬅ T029
- [ ] **T052** — Loading states in the frontend for every async
  operation. ⬅ T036
- [ ] **T053** — Empty states: "no assistants yet", "no documents on
  this assistant", "start a conversation". ⬅ T037
- [ ] **T054** — Destructive confirmations: "are you sure you want to
  delete this assistant? X documents and Y conversations will be
  deleted". ⬅ T038
- [ ] **T055** — Visual polish: coherent palette, spacing, typography.
  One global pass, no perfectionism. ⬅ T037
- [ ] **T056** — Commit and push.

**Phase 6 checkpoint**: a user who has never seen the app can use it
without asking questions and without getting stuck.

---

## Phase 7 — Deliverables

**Goal**: README, final diagram, demo video ready for submission.

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
- [ ] **T062** — Demo video script (5 min max): intro (30s), assistant
  creation (1min), document upload (45s), chat with each assistant
  demonstrating isolation and citations (1.5min), conversational memory
  demo (30s), persistence after reload (45s), wrap-up (30s).
- [ ] **T063** — Record the video with Spanish narration over the
  English UI. Tool: OBS or Loom.
- [ ] **T064** — Upload the video to unlisted YouTube (or Google Drive),
  review the auto-generated English subtitles, link from the README. ⬅ T063
- [ ] **T065** — Final commit tagged `v1.0`.

**Phase 7 checkpoint**: all three deliverables (repo, README, video) are
publishable as-is.

---

## Phase 8 — Buffer (optional)

**Goal**: whatever you have energy and time for. Nothing here is
required.

- [ ] **T066** — Prioritise by impact: any lingering demo bugs >
  polish > extra features.
- [ ] **T067** — Optional extras in order of value: response streaming
  (SSE), better long-context handling via compaction, export
  conversation to file, conversation rename.
- [ ] **T068** — Prepare a short presentation (slides or outline) in
  case you are picked to present in class. This is not recorded and
  not submitted — it is a fallback.

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
