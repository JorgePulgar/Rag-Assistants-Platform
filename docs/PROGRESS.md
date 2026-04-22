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
