# Technical Project Summary

Generated: 2026-04-25

---

## 1. Repo Statistics

| Metric | Value |
|--------|-------|
| Total commits | 57 |
| Backend Python LOC | 2 632 |
| Frontend TypeScript / TSX LOC | 1 499 (88 `.ts` + 1 411 `.tsx`) |
| Docs Markdown LOC | 2 157 |
| Test files | 8 |
| Unit tests | 56 |
| Test result | **56 passed, 0 failed, 0 skipped** (27 s) |

---

## 2. Commit History Highlights

Ten most significant commits, grouped by phase.

### Phase 0 — Setup

| Hash | Date | Message |
|------|------|---------|
| `91b9aec` | 2026-04-21 | feat(backend): scaffold FastAPI app with /health, SQLAlchemy, and config (T004, T007) |

### Phase 2 — Ingestion Pipeline

| Hash | Date | Message |
|------|------|---------|
| `0b26828` | 2026-04-22 | feat: document parsers and ingestion pipeline (T016-T018) |
| `461d02e` | 2026-04-22 | feat: documents API, delete cascade, isolation tests (T019-T024) |

### Phase 4 — RAG Chat with Memory and Citations

| Hash | Date | Message |
|------|------|---------|
| `c40e136` | 2026-04-22 | feat(backend): RAG chat with memory and citations (T026-T034) |

### Phase 5 — Frontend

| Hash | Date | Message |
|------|------|---------|
| `03bed88` | 2026-04-22 | feat(frontend): complete Phase 5 — full React SPA (T035b–T047) |

### Phase 4.5 — Bugfixes

| Hash | Date | Message |
|------|------|---------|
| `05eeb4e` | 2026-04-23 | fix(backend): eager index creation and defensive retrieval (T047b) |
| `73f9b17` | 2026-04-23 | feat(backend): query rewriting for referential follow-ups (T047c) |
| `afa4423` | 2026-04-24 | feat(rag): skip retrieval on no-search intent (T047i) |

### Phase 6.5 — Real-Content Fixes

| Hash | Date | Message |
|------|------|---------|
| `8e96221` | 2026-04-25 | fix(rag): B8 — language-independent is_fallback flag replaces frontend IDK string matching |
| `fbe7aa7` | 2026-04-25 | fix(rag): B9 — implicit citations when LLM omits all [CITE:...] markers |

---

## 3. Phase Completion Status

Tasks taken verbatim from `docs/TASKS.md`.

### Phase 0 — Setup

- [x] **T001** — Create the GitHub repo from the browser (manual, Jorge).
- [x] **T002** — Clone the repo locally, drop these documents into `/docs`, make the initial commit.
- [x] **T003** — Azure setup: create Azure AI Foundry resource, deploy `gpt-4o-mini` and `text-embedding-3-small`. Create Azure AI Search resource (Basic tier or higher, semantic search enabled). Store credentials in a local `.env` (manual, Jorge — not Claude Code).
- [x] **T004** — Backend scaffolding: folder structure, `requirements.txt`, FastAPI running on `:8000` with a `/health` endpoint, SQLAlchemy configured, SQLite auto-created on startup.
- [x] **T005** — Frontend scaffolding: Vite + React + TS + Tailwind + shadcn init. `npm run dev` serves on `:5173` with a blank page.
- [x] **T006** — Complete `.gitignore` (venv, node_modules, .env, .db, __pycache__, .vscode, .idea, dist, build).
- [x] **T007** — `.env.example` in backend with every variable documented.

### Phase 1 — Assistant CRUD

- [x] **T008** — SQLAlchemy models: `Assistant`, `Document`, `Conversation`, `Message`. Auto-migrate on startup.
- [x] **T009** — Pydantic schemas for `Assistant` (Create, Update, Read).
- [x] **T010** — Router `api/assistants.py` with the five CRUD endpoints. Logic in `services/assistant_service.py`.
- [x] **T011** — Generate `search_index` name on assistant creation (string only; actual Azure index created in Phase 2).
- [x] **T012** — Basic tests: create, list, update, delete an assistant. Using FastAPI's `TestClient`.
- [x] **T013** — Commit and push.

### Phase 2 — Ingestion Pipeline

- [x] **T014** — Client `clients/azure_openai.py`: embeddings + LLM wrapper, reads config from `.env`.
- [x] **T015** — Client `clients/azure_search.py`: wrapper for index creation, document upload, search.
- [x] **T016** — Parsers: `pdf.py`, `docx.py`, `pptx.py`, `text.py`. Each returns `list[ParsedChunk]` per RAG_SPEC.
- [x] **T017** — Parser tests with one fixture per format in `tests/fixtures/`.
- [x] **T018** — `services/ingestion.py` `index_document` function: resolve parser by extension, extract chunks, apply `RecursiveCharacterTextSplitter` with settings values, call embeddings in batches of 16, create the Azure Search index if it does not exist (per-assistant), upload chunks with full metadata, update document status in SQLite.
- [x] **T019** — Pydantic schemas for `Document`.
- [x] **T020** — Router `api/documents.py`: upload, list, delete. Upload via `UploadFile`, write temp file, call ingestion, remove temp.
- [x] **T021** — Delete endpoint: remove chunks from the Azure Search index (filter by `document_id`) and the SQLite row. Deleting an assistant cascades to its documents and deletes the whole index.
- [x] **T022** — Manual check: upload a real PDF to an assistant, verify in the Azure Portal that the index exists and contains chunks.
- [x] **T023** — Automatic isolation test (`test_isolation.py`, ingestion portion): two assistants, two different documents, verify no cross-contamination at the index level.
- [x] **T024** — Commit and push.

### Phase 3 — Conceptual Architecture Diagram

- [x] **T025** — Draft the conceptual architecture diagram. Save source and PNG export to `docs/architecture.png` + `docs/architecture.mmd`.

### Phase 4 — RAG Chat with Memory and Citations

- [x] **T026** — `services/retrieval.py` `retrieve` function: embed the query, hybrid query to Azure Search (keyword + vector + semantic rerank), filter by score threshold, return the top_k chunks with full metadata.
- [x] **T027** — Pydantic schemas for `Conversation` and `Message`, including `citations` JSON shape.
- [x] **T028** — `services/rag.py` `generate_response` function: load assistant and last N messages, call retrieve, if empty return hardcoded "I don't know" response, build prompt per RAG_SPEC, call LLM, post-process citations, return `{content, citations}`.
- [x] **T029** — Router `api/chat.py`: POST /conversations, GET /assistants/{id}/conversations, GET /conversations/{id}/messages, POST /conversations/{id}/messages, DELETE /conversations/{id}.
- [x] **T030** — Test `test_rag_prompt.py` covering the three RAG_SPEC cases: with context, without context, with long history (trim verification).
- [x] **T031** — End-to-end isolation test: ask assistant B about a topic from assistant A's documents, verify "I don't know".
- [x] **T032** — Memory smoke test: send three sequential messages in one conversation where each references the previous. Verify coherent answers demonstrating memory.
- [x] **T033** — Persistence smoke test: restart the backend process, reload the conversation via `GET /conversations/{id}/messages`, verify the full history is intact.
- [x] **T034** — Commit and push.

### Phase 4.5 — Bugfixes and Test Remediation

- [x] **T047a** — Update `docs/RAG_SPEC.md` with: (1) a new "Query rewriting" section; (2) a new "Index lifecycle" section; (3) updated "Design note" in the History section.
- [x] **T047b** — Bug 1 fix (Option B, architectural): move index creation from `services/ingestion.py` (lazy) to `services/assistant_service.py` create path (eager). Transactional with SQLite row.
- [x] **T047c** — Bug 2 fix: implement query rewriting per RAG_SPEC.md §"Query rewriting". Feature-flagged behind `QUERY_REWRITING_ENABLED=true`.
- [x] **T047d** — Automated test for Bug 1 fix in `backend/tests/test_idk_behaviour.py`.
- [x] **T047e** — Automated test for Bug 2 fix in `backend/tests/test_conversational_memory.py`.
- [x] **T047f** — Retrospective audit of T023, T030, T031, T032, T033.
- [x] **T047g** — Phase 4.5 final commit and push.

### Phase 4.5 — Follow-up Fixes (post-testing)

- [x] **T047h** — Sync system prompts in code with updated `RAG_SPEC.md`.
- [x] **T047i** — Skip retrieval on no-search intent, per RAG_SPEC §"Query rewriting".
- [x] **T047j** — Frontend fix: apply amber warning style ONLY to the hardcoded "I don't know" response.
- [x] **T047k** — Citation rendering fix: diagnose and fix `[CITE:chunk_id]` markers sometimes rendering as literal text.
- [x] **T047l** — Automated regression test for the elaboration case (Rule 1 fix).
- [x] **T047n** — Automated regression test for the "exemplify" case (Rule 7 EXEMPLIFY mode).
- [x] **T047m** — Follow-up commits and push.

### Phase 5 — Frontend

- [x] **T035** — Quick wireframe pass for the three views.
- [x] **T035b** — Theme setup per FRONTEND_SPEC: Tailwind config, ThemeProvider, theme toggle, Inter font.
- [x] **T036** — API client in `frontend/src/api/client.ts` with axios. TS types mirroring Pydantic schemas.
- [x] **T037** — Main layout: sidebar with assistant list + main area.
- [x] **T038** — Assistant list view: card per assistant, "New" button, edit/delete buttons.
- [x] **T039** — Assistant create/edit form inside a shadcn Dialog.
- [x] **T040** — Assistant detail view: info + document list + uploader.
- [x] **T041** — Document uploader: file input + upload button + progress + list with delete.
- [x] **T042** — Chat view: conversation list, selector, new button, message history, input, send.
- [x] **T043** — `MessageBubble` component with visual distinction between user and assistant.
- [x] **T044** — `CitationBlock` component: `[1]`, `[2]` inline pills + expandable panel on click.
- [x] **T045** — "Assistant is thinking" loading state in the chat.
- [x] **T046** — Error toasts (shadcn) for failed requests.
- [x] **T047** — Commit and push.

### Phase 6 — Polish and Edge Cases

- [x] **T048** — Run the full flow three times with real, distinct documents. Write every bug found into a short list.
- [x] **T049** — Fix the bugs from T048 (open-ended, N sub-bugs).
- [x] **T050** — Ingestion edge cases: corrupt PDF, empty file, unsupported format, file > 10MB. Each case must return a clean error, never a 500.
- [x] **T051** — Chat edge cases: conversation with a deleted assistant, empty message, very long message.
- [x] **T052** — Loading states in the frontend for every async operation.
- [x] **T053** — Empty states: "no assistants yet", "no documents on this assistant", "start a conversation".
- [x] **T054** — Destructive confirmations: "are you sure you want to delete this assistant? X documents and Y conversations will be deleted".
- [x] **T055** — Visual polish: coherent palette, spacing, typography.
- [x] **T055b** — Citation pill rendering fix: residual `[CITE:id]` literal text cleanup.
- [x] **T056** — Commit and push.
- [x] **T048b** — Real end-to-end runs with real content (confirmed by Jorge).

### Phase 6.5 — Real-Content Fixes

- [x] **T057a** — B8 fix: language-independent "I don't know" detection via `is_fallback` backend flag.
- [x] **T057b** — B9 fix: surface citations even when the LLM omits them (implicit citations fallback).
- [x] **T057c** — Phase 6.5 final commit and push.

---

## 4. Test Inventory

All tests are in `backend/tests/`. Run with `pytest -v` from `backend/`.

**Result: 56 passed, 0 failed, 0 skipped — 27.01 s**

| File | Covers | Tests |
|------|--------|-------|
| `test_assistants.py` | CRUD endpoints for `/api/assistants` (T012): create, list, update, delete, 404 paths, `search_index` derivation, uniqueness across two assistants. | 11 |
| `test_chat_edge_cases.py` | Chat API edge cases (T051): empty message → 422, whitespace-only → 422, oversized message (> 20 000 chars) → 422, send to conversation of deleted assistant → 404. | 4 |
| `test_conversational_memory.py` | Conversational memory (T047e/T033/T047l): referential follow-up query rewriting resolves correct topic; conversation persists across simulated server restarts; elaboration ("expand on that") does not trigger the "I don't know" path. | 3 |
| `test_idk_behaviour.py` | Bug 1 + Bug 8 regression (T047d/T057a): no-document assistant returns 200 with hardcoded string; empty retrieval sets `is_fallback=True`; Spanish LLM fallback sets `is_fallback=True`; `is_fallback` survives reload via `GET /conversations/{id}/messages`. | 4 |
| `test_ingestion_edge_cases.py` | Ingestion guards (T050): file > 10 MB → 413; empty file → 422; unsupported extension → `status=failed`; corrupt PDF bytes → `status=failed`. | 4 |
| `test_isolation.py` | Azure AI Search index isolation (T023/T031): two assistants use structurally separate indexes; deleting one document removes only its chunks; retrieval for assistant B returns zero chunks from assistant A's index. Marked `@pytest.mark.integration`; requires real Azure credentials; skipped automatically when `AZURE_SEARCH_API_KEY` is unset. | 3 |
| `test_parsers.py` | Format-specific parsers (T017): PDF chunk count, text content, page numbers; DOCX chunk count, text, page=None, section propagation from headings; PPTX chunk count, text, slide-number as page; TXT and MD parsing; empty file; parser resolver; unsupported extension raises. | 15 |
| `test_rag_prompt.py` | RAG prompt construction and post-processing (T030/T047k/T057b): with-context path calls LLM and includes all three prompt sections; without-context path skips LLM and returns hardcoded message; long history is trimmed to `HISTORY_MAX_MESSAGES`; single citation; consecutive citations; citation at end of sentence; case-insensitive chunk IDs; unknown chunk ID stripped; implicit citations when no markers; no implicit when explicit citations exist; explicit citations carry `implicit=False`. | 12 |

---

## 5. Final Repo Structure

Source-controlled files only (`git ls-files`), depth ≤ 3, formatted as tree.

```
rag-assistants/
├── .claude/
│   ├── CLAUDE.md
│   ├── settings.local.json
│   └── skills/
│       ├── azure-integration/SKILL.md
│       └── rag-patterns/SKILL.md
├── .gitattributes
├── .gitignore
├── README.md
├── README.es.md
├── backend/
│   ├── .env.example
│   ├── pyproject.toml
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── exceptions.py
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── assistants.py
│   │   │   ├── chat.py
│   │   │   └── documents.py
│   │   ├── clients/
│   │   │   ├── __init__.py
│   │   │   ├── azure_openai.py
│   │   │   └── azure_search.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── assistant.py
│   │   │   ├── conversation.py
│   │   │   ├── document.py
│   │   │   └── message.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── assistant.py
│   │   │   ├── chat.py
│   │   │   └── document.py
│   │   └── services/
│   │       ├── __init__.py
│   │       ├── assistant_service.py
│   │       ├── chat_service.py
│   │       ├── document_service.py
│   │       ├── ingestion.py
│   │       ├── query_rewriter.py
│   │       ├── rag.py
│   │       ├── retrieval.py
│   │       └── parsers/
│   │           ├── __init__.py
│   │           ├── docx.py
│   │           ├── pdf.py
│   │           ├── pptx.py
│   │           └── text.py
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── fixtures/
│       │   ├── create_fixtures.py
│       │   ├── sample.docx
│       │   ├── sample.md
│       │   ├── sample.pdf
│       │   ├── sample.pptx
│       │   └── sample.txt
│       ├── test_assistants.py
│       ├── test_chat_edge_cases.py
│       ├── test_conversational_memory.py
│       ├── test_idk_behaviour.py
│       ├── test_ingestion_edge_cases.py
│       ├── test_isolation.py
│       ├── test_parsers.py
│       └── test_rag_prompt.py
├── docs/
│   ├── ARCHITECTURE.md
│   ├── CODING_CONVENTIONS.md
│   ├── CONSTITUTION.md
│   ├── FRONTEND_SPEC.md
│   ├── PROGRESS.md
│   ├── PROJECT_BRIEF.md
│   ├── RAG_SPEC.md
│   ├── TASKS.md
│   ├── architecture.mmd
│   ├── architecture.png
│   └── bugs_t048.md
├── frontend/
│   ├── components.json
│   ├── eslint.config.js
│   ├── index.html
│   ├── package.json
│   ├── package-lock.json
│   ├── postcss.config.js
│   ├── tailwind.config.js
│   ├── tsconfig.app.json
│   ├── tsconfig.json
│   ├── tsconfig.node.json
│   ├── vite.config.ts
│   ├── public/
│   │   ├── favicon.svg
│   │   └── icons.svg
│   └── src/
│       ├── App.css
│       ├── App.tsx
│       ├── index.css
│       ├── main.tsx
│       ├── api/
│       │   └── client.ts
│       ├── components/
│       │   ├── AssistantForm.tsx
│       │   ├── AssistantList.tsx
│       │   ├── CitationBlock.tsx
│       │   ├── DocumentUploader.tsx
│       │   ├── Layout.tsx
│       │   ├── MessageBubble.tsx
│       │   └── ui/
│       │       ├── badge.tsx
│       │       ├── button.tsx
│       │       ├── dialog.tsx
│       │       ├── input.tsx
│       │       ├── popover.tsx
│       │       ├── sonner.tsx
│       │       └── textarea.tsx
│       ├── lib/
│       │   ├── types.ts
│       │   └── utils.ts
│       └── pages/
│           ├── AssistantDetailPage.tsx
│           ├── AssistantsPage.tsx
│           └── ChatPage.tsx
└── scripts/
    └── smoke/
        └── t048b_e2e.py
```

---

## 6. Known Limitations

### From `docs/PROJECT_BRIEF.md` §"Out of scope"

1. **No authentication / multi-tenancy** — a single user owns all assistants. Anyone with access to the running instance can read and modify all data.
2. **No response streaming (SSE)** — LLM responses are returned in one block after generation completes; latency scales with response length.
3. **No OCR** — scanned PDFs (image-only) are not supported; documents must have machine-readable text.
4. **No production deployment** — the application is designed for local development only; no containerisation, reverse proxy, HTTPS, or process manager is configured.
5. **No sharing assistants between users** — assistants are not scoped to user accounts and cannot be shared or permissioned.
6. **No document versioning** — deleting and re-uploading a document changes its chunk IDs, orphaning citation references in old conversation messages.
7. **No chat history search** — there is no full-text or semantic search over past conversations.

### From `docs/RAG_SPEC.md`

8. **No cross-conversation memory** — the assistant does not remember facts about the user across separate conversations. This is an explicit non-goal per `CONSTITUTION.md` §4.
9. **Spanish text analyzer** — the Azure AI Search index uses `es.microsoft` for Spanish stemming. English documents work but may have marginally lower keyword-recall quality. Changing the analyzer requires updating `clients/azure_search.py` and re-indexing all documents.
10. **Synchronous ingestion** — large files block the HTTP request during parsing and embedding. Typical PDFs take 5–15 seconds; files larger than ~3 MB may approach 30 seconds.
11. **Retrieval score threshold is empirical** — `RETRIEVAL_SCORE_THRESHOLD=1.2` was tuned against Spanish legal and technical documents. Different corpora may require recalibration to avoid over-filtering or under-filtering.

### From `docs/bugs_t048.md`

All nine bugs discovered during the Phase 6 audit (B1–B9) have been fixed.

| Bug | Description | Fixed in |
|-----|-------------|---------|
| B1 | No file size limit before reading into memory; large uploads could exhaust process memory | T050 |
| B2 | Empty message content accepted by Pydantic, triggering embedding of empty string | T051 |
| B3 | No maximum message length bound; oversized messages could exceed Azure context window | T051 |
| B4 | Hallucinated `[CITE:id]` markers not stripped; appeared as literal text in the UI | T055b |
| B5 | "Start new conversation" button had no loading indicator; double-click created duplicates | T052 |
| B6 | Delete-assistant dialog omitted conversation count from the confirmation body | T054 |
| B7 | User and assistant messages shared the same `created_at` timestamp; message ordering was undefined | T049 |
| B8 | Non-English "I don't know" responses did not receive the amber warning style in the frontend | T057a |
| B9 | LLM omitted `[CITE:...]` markers on PPTX-derived short chunks, returning zero citations for grounded answers | T057b |

No unfixed bugs remain from the T048 audit.
