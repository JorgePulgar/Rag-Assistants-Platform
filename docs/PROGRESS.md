# PROGRESS — Development log

This file records project progress across working sessions. Each entry
summarises what was done and which phase advanced. Claude Code appends
one line at the end of each session.

Project phases are defined in `docs/TASKS.md`. At any moment, the
"current phase" is the earliest one with pending tasks.

---

## Session 0 — Planning

- Stack decision: FastAPI + React/Vite + Azure Foundry + Azure AI Search.
- Context documents created (`CONSTITUTION`, `PROJECT_BRIEF`,
  `ARCHITECTURE`, `RAG_SPEC`, `CODING_CONVENTIONS`, `TASKS`).
- Local skills created (`rag-patterns`, `azure-integration`).
- `CLAUDE.md` created for Claude Code.
- Repository initialised with the base structure.
- Decision: task file organised by **phases**, not calendar days, to
  accommodate variable daily availability.
- Decision: conversational memory is a core feature, documented
  explicitly in `CONSTITUTION.md` (principle 4) and `RAG_SPEC.md`
  (History section).

**Next**: Phase 0 — Setup (T001–T007).

---

<!-- Append one line per session below: "Session N — <date>: advanced Phase X, completed TXXX..TYYY, notes" -->

Session 1 — 2026-04-21: advanced Phase 0, completed T004–T007; notable: pydantic-core 2.46.3 required for Python 3.14 wheel support (pinned); Tailwind v3 chosen over v4 for shadcn/ui compatibility.
Session 2 — 2026-04-22: completed Phase 1 (T008–T013); notable: sqlalchemy bumped to 2.0.49 (2.0.36 broke on Python 3.14 Union typing); 11 CRUD tests green.
Session 3 — 2026-04-21: completed Phase 2 (T014–T024); notable: chunk_index field added to Azure AI Search schema to fix 400 error on upload; integration tests hit real Azure and both pass; 27 unit tests green.
Session 4 — 2026-04-22: completed Phase 3 (T025); Mermaid flowchart diagram created as docs/architecture.mmd; Excalidraw skipped per Jorge's instruction; all 8 chat-flow steps labelled; per-assistant index convention annotated on AI Search node.
Session 5 — 2026-04-22: completed Phase 4 (T026–T034); retrieval.py, rag.py, chat_service.py, api/chat.py implemented; notable: user message persisted after generate_response to prevent double-inclusion in LLM history; 30 unit tests green; T031 retrieval isolation test added to test_isolation.py; T032/T033 verified manually via HTTP smoke test.
Session 6 — 2026-04-22: completed Phase 5 (T035b–T047); full React SPA implemented; notable: next-themes for theme management (installed by shadcn sonner); shadcn CLI created files in literal @/ folder — moved to src/components/ui/; state-based routing in App.tsx (no react-router needed for 3 views); citation pills parse [N] markers in LLM content and open Radix Popover on click; ThinkingBubble with staggered animate-pulse dots; sonner toasts on every API failure.
Session 7 — 2026-04-23: completed Phase 4.5 (T047a–T047g); Bug 1 fixed (eager index creation, transactional with SQLite row); Bug 2 fixed (LLM-based query rewriting for referential follow-ups, feature-flagged); 33 unit tests green. Retrospective audit: T023 — pass (test_isolation.py, integration); T030 — pass (test_rag_prompt.py, 3 unit tests; test_with_context updated to stub rewriter after T047c changed call flow); T031 — pass (test_isolation.py::test_retrieval_service_does_not_cross_index_boundary, integration); T032 — rewritten (test_conversational_memory.py::test_query_rewriting_resolves_referential_followup); T033 — added (test_conversational_memory.py::test_conversation_persists_across_sessions).
Session 8 — 2026-04-24: completed Phase 4.5 follow-up (T047i–T047m); no-search intent skips retrieval for chit-chat (rewritten==original AND ≤10 words); frontend warning style scoped to known I-don't-know prefixes instead of citations.length===0; _post_process regex made case-insensitive (LLM upper-cases UUIDs); 4 new citation unit tests + 1 elaboration regression test; 38 unit tests green.
Session 9 — 2026-04-25: completed Phase 6 (T051–T056); chat edge-case tests committed (422 on empty/oversized message, 404 on deleted-assistant conversation); "Start new conversation" loading state added; delete dialog shows exact document + conversation counts; visual polish pass (label htmlFor, consecutive-message mt-1 spacing); _post_process fallback strips unresolved [CITE:id] literals with INFO log; 47 unit tests green. T048b pending Jorge's authorisation.
Session 10 — 2026-04-25: completed Phase 6.5 (T057a–T057c); B8 fixed via is_fallback backend flag replacing frontend IDK_PREFIXES string matching (apply_column_migrations handles existing app.db); B9 fixed via implicit citations fallback in _post_process (top-3 chunks surfaced as implicit=True when LLM omits all markers, cleared if is_fallback to avoid contradiction); RAG_SPEC.md §"Response post-processing" updated; 56 unit tests green.
Session 11 — 2026-04-25: completed Phase 7 (T057–T060, T065); final PROGRESS.md snapshot written; architecture diagram updated to include query_rewriter step and no-search-intent path; PNG re-exported; full English README.md written; Spanish courtesy README.es.md written; final commit tagged v1.0.

---

## Final State Snapshot — 2026-04-25

### What was built

A full-stack Retrieval-Augmented Generation (RAG) platform that lets users
create multiple isolated AI assistants, upload documents to them, and chat
with each assistant grounded in its own document set. The assistant
demonstrates three properties required by the project brief:

1. **Structural isolation** — each assistant owns a dedicated Azure AI
   Search index. No shared index, no filter-based isolation.
2. **Persistent conversational memory** — every message is stored in SQLite
   with its role and citations. Memory survives backend restarts, browser
   closures, and reboots.
3. **Grounded answers with structured citations** — responses include
   `[1]`, `[2]` inline markers resolved to structured objects (document
   name, page, chunk excerpt). When no relevant chunks exist, the LLM is
   never called — a hardcoded "I don't know" message is returned.

### Phases completed

| Phase | Goal | Checkpoint |
|-------|------|-----------|
| 0 | Setup — repo, stacks, Azure resources | backend `/health` 200, frontend blank at `:5173` |
| 1 | Assistant CRUD | 5 endpoints, 11 tests green |
| 2 | Ingestion pipeline | PDF/DOCX/PPTX/TXT → chunks → Azure Search, isolation test passes |
| 3 | Architecture diagram | `docs/architecture.mmd` + `docs/architecture.png` |
| 4 | RAG chat with memory + citations | Chat endpoint returns grounded answers with citations; memory survives restart |
| 4.5 | Bugfixes: eager index creation, query rewriting | Both bugs fixed with regression tests; 56 unit tests green |
| 5 | Frontend SPA | Three views (assistants, detail, chat) fully wired |
| 6 | Polish and edge cases | Empty states, destructive confirmations, edge-case error handling |
| 6.5 | Real-content fixes (B8, B9) | `is_fallback` flag; implicit citations for PPTX |
| 7 | Deliverables | README (EN + ES), architecture diagram, v1.0 tag |

### Architecture highlights

- **Backend**: FastAPI + SQLAlchemy + SQLite. Services: `assistant_service`,
  `chat_service`, `document_service`, `ingestion`, `retrieval`, `rag`,
  `query_rewriter`. Azure clients: `azure_openai` (LLM + embeddings),
  `azure_search` (hybrid search with semantic reranking).
- **Frontend**: React 18 + Vite + TypeScript + Tailwind + shadcn/ui.
  State-based routing (no react-router). Citation pills as Radix Popover.
  ThinkingBubble with staggered animate-pulse. Dark/light theme via
  next-themes.
- **Query rewriting**: before retrieval, the user's message is rewritten
  into a standalone search query using the last 4 history messages and a
  dedicated LLM call. No-search intent (chit-chat) skips retrieval
  entirely and goes straight to the LLM with history only.
- **Implicit citations (B9)**: if the LLM returns a grounded answer but
  omits all `[CITE:id]` markers (common with PPTX bullet fragments), the
  backend surfaces the top-3 retrieved chunks as `implicit=True` citations
  so the user retains source traceability.
- **is_fallback (B8)**: the backend sets `is_fallback=True` on the message
  record whenever the "I don't know" path fires. The frontend reads this
  flag (not string-matching) to apply the amber warning style — works
  regardless of response language.

### Test coverage

56 unit tests green across:
- `test_parsers.py` — PDF, DOCX, PPTX, TXT parsers
- `test_isolation.py` — ingestion + retrieval cross-contamination guards
- `test_rag_prompt.py` — RAG prompt construction (3 cases)
- `test_idk_behaviour.py` — empty-index "I don't know" path
- `test_conversational_memory.py` — query rewriting, referential follow-ups,
  cross-session persistence, elaboration, exemplify regression
- `test_citation_processing.py` — post-processing edge cases
- `test_assistants.py`, `test_documents.py`, `test_chat.py` — API layer

### Key configuration parameters (`.env`)

| Parameter | Default | Notes |
|-----------|---------|-------|
| `CHUNK_SIZE` | 800 | Characters per chunk |
| `CHUNK_OVERLAP` | 150 | ~18% overlap |
| `RETRIEVAL_TOP_K` | 8 | Candidates before re-rank |
| `RETRIEVAL_SCORE_THRESHOLD` | 1.2 | Azure semantic reranker 0–4 scale |
| `HISTORY_MAX_MESSAGES` | 10 | 5 user/assistant pairs |
| `QUERY_REWRITING_ENABLED` | true | Feature flag; disable for debugging |
| `QUERY_REWRITING_HISTORY_N` | 4 | Last N messages fed to rewriter |

### Known limitations (documented in README)

- No authentication or multi-user isolation — a single user owns all
  assistants. Any user with access to the running instance can see all data.
- No cross-conversation memory — the assistant does not remember facts from
  previous separate conversations with the same user.
- No OCR — scanned PDFs (image-only) are not supported. Documents must have
  extractable text.
- Ingestion is synchronous — large files (> 1 MB) can take 10–30 seconds;
  the HTTP request blocks during this time.
- Azure AI Search `es.microsoft` analyzer is optimised for Spanish. English
  documents work but may have marginally lower retrieval quality; to change,
  update the analyzer field in `azure_search.py` and re-index.
- No streaming — the LLM response is returned in one block after completion.
- No document versioning — deleting and re-uploading a document changes its
  chunk IDs, which breaks references in old conversation messages.
