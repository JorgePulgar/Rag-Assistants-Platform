# RAG Assistants Platform

🚧 **En desarrollo** — proyecto full-stack de plataforma de asistentes RAG
con aislamiento por asistente sobre Azure AI Foundry + Azure AI Search.

El README completo con arquitectura y guía de ejecución se publicará al
final del desarrollo. Para seguir el progreso actual, ver
[`docs/PROGRESS.md`](docs/PROGRESS.md).

## Stack

- **Backend**: Python 3.11 + FastAPI + SQLAlchemy + SQLite
- **Frontend**: React 18 + Vite + TypeScript + Tailwind + shadcn/ui
- **IA**: Azure AI Foundry (`gpt-4o-mini`, `text-embedding-3-small`)
- **Vector store**: Azure AI Search (un índice por asistente)

## Documentación técnica

- [`docs/PROJECT_BRIEF.md`](docs/PROJECT_BRIEF.md) — qué construimos y por qué
- [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md) — stack y contratos
- [`docs/RAG_SPEC.md`](docs/RAG_SPEC.md) — especificación del pipeline RAG
- [`docs/CONSTITUTION.md`](docs/CONSTITUTION.md) — principios no negociables
