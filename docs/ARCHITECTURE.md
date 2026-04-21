# ARCHITECTURE — Stack, Structure, and Contracts

## Technology stack

### Backend
- **Python 3.11+**
- **FastAPI** — async web framework, Pydantic validation, automatic OpenAPI.
- **SQLAlchemy 2.x** + **SQLite** — relational persistence (assistants,
  documents, conversations, messages).
- **openai** (SDK) — client for Azure AI Foundry (OpenAI-compatible).
- **azure-search-documents** — official Azure AI Search client.
- **pypdf**, **python-docx**, **python-pptx** — format-specific parsers.
- **langchain-text-splitters** — only for `RecursiveCharacterTextSplitter`.
  We do not pull in the rest of the framework.

### Frontend
- **React 18** + **Vite** — SPA with hot reload.
- **TypeScript** — strict mode.
- **Tailwind CSS** — utility-first styling.
- **shadcn/ui** — base components (dialog, input, button, card, toast).
- **lucide-react** — icons.
- **axios** — HTTP client.

### External services
- **Azure AI Foundry** deployments:
  - LLM: `gpt-4o-mini` (development) / `gpt-4o` (optional for demo).
  - Embeddings: `text-embedding-3-small` (1536 dims).
- **Azure AI Search** — one index per assistant.

## Folder structure

```
rag-assistants/
├── .claude/
│   ├── CLAUDE.md
│   └── skills/
│       ├── rag-patterns/
│       │   └── SKILL.md
│       └── azure-integration/
│           └── SKILL.md
├── docs/
│   ├── CONSTITUTION.md
│   ├── PROJECT_BRIEF.md
│   ├── ARCHITECTURE.md
│   ├── RAG_SPEC.md
│   ├── CODING_CONVENTIONS.md
│   ├── TASKS.md
│   └── PROGRESS.md
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI entrypoint
│   │   ├── config.py                  # settings loaded from .env
│   │   ├── db.py                      # SQLAlchemy engine + session
│   │   ├── models/                    # SQLAlchemy models
│   │   │   ├── assistant.py
│   │   │   ├── document.py
│   │   │   ├── conversation.py
│   │   │   └── message.py
│   │   ├── schemas/                   # Pydantic schemas
│   │   │   ├── assistant.py
│   │   │   ├── document.py
│   │   │   └── chat.py
│   │   ├── api/                       # routers
│   │   │   ├── assistants.py
│   │   │   ├── documents.py
│   │   │   └── chat.py
│   │   ├── services/                  # business logic
│   │   │   ├── ingestion.py           # extract → chunk → embed → upload
│   │   │   ├── retrieval.py           # Azure AI Search query per assistant
│   │   │   ├── rag.py                 # orchestration: retrieval + prompt + LLM
│   │   │   └── parsers/               # one module per format
│   │   │       ├── pdf.py
│   │   │       ├── docx.py
│   │   │       ├── pptx.py
│   │   │       └── text.py
│   │   └── clients/                   # external SDK wrappers
│   │       ├── azure_openai.py
│   │       └── azure_search.py
│   ├── tests/
│   │   ├── test_isolation.py          # critical test
│   │   ├── test_parsers.py
│   │   └── test_rag_prompt.py
│   ├── .env.example
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/                       # axios wrappers
│   │   │   └── client.ts
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn-generated
│   │   │   ├── AssistantList.tsx
│   │   │   ├── AssistantForm.tsx
│   │   │   ├── DocumentUploader.tsx
│   │   │   ├── ChatView.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   └── CitationBlock.tsx
│   │   ├── pages/
│   │   │   ├── AssistantsPage.tsx
│   │   │   ├── AssistantDetailPage.tsx
│   │   │   └── ChatPage.tsx
│   │   └── lib/
│   │       └── types.ts
│   ├── index.html
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.ts
├── .gitignore
├── .gitattributes
└── README.md
```

## Data model

### `assistants`
| Column          | Type          | Notes                                          |
|-----------------|---------------|------------------------------------------------|
| `id`            | UUID (str)    | PK, server-generated                           |
| `name`          | str(200)      | NOT NULL                                       |
| `instructions`  | TEXT          | NOT NULL, assistant's system prompt            |
| `description`   | TEXT          | NULL                                           |
| `search_index`  | str(100)      | NOT NULL, UNIQUE — Azure AI Search index name  |
| `created_at`    | datetime      |                                                |
| `updated_at`    | datetime      |                                                |

`search_index` naming convention: `assistant-{id_hex_no_dashes}`. Validated
against regex `^[a-z0-9-]{2,128}$` (Azure AI Search restrictions).

### `documents`
| Column          | Type          | Notes                                       |
|-----------------|---------------|---------------------------------------------|
| `id`            | UUID (str)    | PK                                          |
| `assistant_id`  | UUID (FK)     | NOT NULL, ON DELETE CASCADE                 |
| `filename`      | str(500)      | original filename                           |
| `mime_type`     | str(100)      |                                             |
| `size_bytes`    | int           |                                             |
| `chunk_count`   | int           | number of chunks generated                  |
| `status`        | str(20)       | `pending` / `indexed` / `failed`            |
| `error_message` | TEXT          | set when `status=failed`                    |
| `uploaded_at`   | datetime      |                                             |

### `conversations`
| Column          | Type          | Notes                                 |
|-----------------|---------------|---------------------------------------|
| `id`            | UUID (str)    | PK                                    |
| `assistant_id`  | UUID (FK)     | NOT NULL, ON DELETE CASCADE           |
| `title`         | str(200)      | autogenerated or editable             |
| `created_at`    | datetime      |                                       |
| `updated_at`    | datetime      | updated on every message              |

### `messages`
| Column            | Type          | Notes                                               |
|-------------------|---------------|-----------------------------------------------------|
| `id`              | UUID (str)    | PK                                                  |
| `conversation_id` | UUID (FK)     | NOT NULL, ON DELETE CASCADE                         |
| `role`            | str(20)       | `user` / `assistant`                                |
| `content`         | TEXT          | NOT NULL                                            |
| `citations`       | JSON          | array of citation objects (only when `role=assistant`) |
| `created_at`      | datetime      |                                                     |

## API contracts

All endpoints return JSON. Errors use standard HTTP conventions with a
`{"detail": "message"}` body.

### Assistants

```
POST   /api/assistants
GET    /api/assistants
GET    /api/assistants/{id}
PATCH  /api/assistants/{id}
DELETE /api/assistants/{id}
```

`POST /api/assistants` body:
```json
{
  "name": "Legal Expert",
  "instructions": "You are a lawyer specialised in...",
  "description": "Answers legal questions about contracts"
}
```

Response 201: created assistant including `id`, `search_index`, `created_at`.

### Documents

```
POST   /api/assistants/{id}/documents      # multipart/form-data
GET    /api/assistants/{id}/documents
DELETE /api/assistants/{id}/documents/{doc_id}
```

`POST` accepts a file in the `file` field. Response 202 with the document
in `pending` state. The client polls, or the server processes synchronously
(decision: **synchronous** for the MVP — on Day 2 we verify timings; if a
large PDF takes more than 30 seconds, we move to a background task using
FastAPI `BackgroundTasks`).

### Chat

```
POST   /api/conversations                                # create a conversation
GET    /api/assistants/{id}/conversations                # list assistant's conversations
GET    /api/conversations/{id}/messages                  # load history
POST   /api/conversations/{id}/messages                  # send a message
DELETE /api/conversations/{id}                           # delete a conversation
```

`POST /api/conversations` body:
```json
{ "assistant_id": "uuid" }
```

`POST /api/conversations/{id}/messages` body:
```json
{ "content": "What does the contract say about clause 3?" }
```

Response 200:
```json
{
  "message": {
    "id": "uuid",
    "role": "assistant",
    "content": "According to the contract, clause 3 states that...",
    "citations": [
      {
        "document_id": "uuid",
        "document_name": "contract_2024.pdf",
        "page": 3,
        "chunk_text": "Clause 3 establishes that..."
      }
    ],
    "created_at": "2026-04-21T10:00:00Z"
  }
}
```

## Chat request flow

1. `POST /api/conversations/{id}/messages` with the user's content.
2. Backend loads: assistant (instructions, `search_index`), conversation
   (previous messages).
3. Backend persists the user message.
4. **Retrieval**: generate the embedding for the user message, query
   Azure AI Search on `search_index` with top_k=5 and semantic reranking
   enabled. Filter chunks below the threshold.
5. **Prompt construction** (see `RAG_SPEC.md`):
   - System: assistant instructions + RAG behaviour rules.
   - History: last N messages from the conversation (see RAG_SPEC).
   - Context block: retrieved chunks with metadata.
   - User: current message.
6. **Generation**: call Azure AI Foundry LLM.
7. **Post-processing**: map citations (the LLM returns chunk IDs; the
   backend resolves them to full objects with document_name, page,
   snippet).
8. Backend persists the assistant message (with citations JSON).
9. Return to the client.

## Environment variables

See `backend/.env.example` for the full list. Minimum:

```
AZURE_OPENAI_ENDPOINT=
AZURE_OPENAI_API_KEY=
AZURE_OPENAI_API_VERSION=2024-10-21
AZURE_OPENAI_LLM_DEPLOYMENT=gpt-4o-mini
AZURE_OPENAI_EMBEDDING_DEPLOYMENT=text-embedding-3-small

AZURE_SEARCH_ENDPOINT=
AZURE_SEARCH_API_KEY=

DATABASE_URL=sqlite:///./app.db

CHUNK_SIZE=800
CHUNK_OVERLAP=150
RETRIEVAL_TOP_K=5
RETRIEVAL_SCORE_THRESHOLD=1.5
HISTORY_MAX_MESSAGES=10
```
