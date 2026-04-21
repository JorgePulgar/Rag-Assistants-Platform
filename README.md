# RAG Assistants Platform

🚧 **Under development** — full-stack RAG assistants platform with
per-assistant isolation on top of Azure AI Foundry + Azure AI Search.

The full README with architecture and setup guide will be published at the
end of development. For current progress, see
[`docs/PROGRESS.md`](docs/PROGRESS.md).

## Stack

- **Backend**: Python 3.11 + FastAPI + SQLAlchemy + SQLite
- **Frontend**: React 18 + Vite + TypeScript + Tailwind + shadcn/ui
- **AI**: Azure AI Foundry (`gpt-4o-mini`, `text-embedding-3-small`)
- **Vector store**: Azure AI Search (one index per assistant)

## Technical documentation

- [`docs/PROJECT_BRIEF.md`](docs/PROJECT_BRIEF.md) — what we build and why
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — stack and contracts
- [`docs/RAG_SPEC.md`](docs/RAG_SPEC.md) — RAG pipeline specification
- [`docs/CONSTITUTION.md`](docs/CONSTITUTION.md) — non-negotiable principles
