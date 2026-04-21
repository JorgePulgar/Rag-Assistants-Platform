# ARCHITECTURE — Stack, estructura y contratos

## Stack tecnológico

### Backend
- **Python 3.11+**
- **FastAPI** — framework web async, validación con Pydantic, OpenAPI automático.
- **SQLAlchemy 2.x** + **SQLite** — persistencia relacional (asistentes, documentos, conversaciones, mensajes).
- **openai** (SDK) — cliente para Azure AI Foundry (compatible OpenAI).
- **azure-search-documents** — cliente oficial de Azure AI Search.
- **pypdf**, **python-docx**, **python-pptx** — parsers por formato.
- **langchain-text-splitters** — solo para `RecursiveCharacterTextSplitter`
  (no usamos el resto del framework).

### Frontend
- **React 18** + **Vite** — SPA con hot reload.
- **Tailwind CSS** — estilado utility-first.
- **shadcn/ui** — componentes base (dialog, input, button, card, toast).
- **lucide-react** — iconos.
- **axios** — cliente HTTP.

### Servicios externos
- **Azure AI Foundry** — despliegues:
  - LLM: `gpt-4o-mini` (desarrollo) / `gpt-4o` (opcional para demo).
  - Embeddings: `text-embedding-3-small` (1536 dim).
- **Azure AI Search** — un índice por asistente.

## Estructura de carpetas

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
│   │   ├── config.py                  # settings desde .env
│   │   ├── db.py                      # engine + session de SQLAlchemy
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
│   │   ├── services/                  # lógica de negocio
│   │   │   ├── ingestion.py           # extract → chunk → embed → upload
│   │   │   ├── retrieval.py           # query AI Search por asistente
│   │   │   ├── rag.py                 # orquestación: retrieval + prompt + LLM
│   │   │   └── parsers/               # un módulo por formato
│   │   │       ├── pdf.py
│   │   │       ├── docx.py
│   │   │       ├── pptx.py
│   │   │       └── text.py
│   │   └── clients/                   # wrappers de clientes externos
│   │       ├── azure_openai.py
│   │       └── azure_search.py
│   ├── tests/
│   │   ├── test_isolation.py          # test crítico
│   │   ├── test_parsers.py
│   │   └── test_rag_prompt.py
│   ├── .env.example
│   ├── requirements.txt
│   └── pyproject.toml
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/                       # funciones axios
│   │   │   └── client.ts
│   │   ├── components/
│   │   │   ├── ui/                    # shadcn generado
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
└── README.md
```

## Modelo de datos

### `assistants`
| Columna         | Tipo          | Notas                                 |
|-----------------|---------------|---------------------------------------|
| `id`            | UUID (str)    | PK, generado en el servidor           |
| `name`          | str(200)      | NOT NULL                              |
| `instructions`  | TEXT          | NOT NULL, system prompt del asistente |
| `description`   | TEXT          | NULL                                  |
| `search_index`  | str(100)      | NOT NULL, UNIQUE — nombre del índice en Azure AI Search |
| `created_at`    | datetime      |                                       |
| `updated_at`    | datetime      |                                       |

Convención de `search_index`: `assistant-{id_hex_sin_guiones}`. Validado por
regex `^[a-z0-9-]{2,128}$` (restricciones de Azure AI Search).

### `documents`
| Columna         | Tipo          | Notas                                       |
|-----------------|---------------|---------------------------------------------|
| `id`            | UUID (str)    | PK                                          |
| `assistant_id`  | UUID (FK)     | NOT NULL, ON DELETE CASCADE                 |
| `filename`      | str(500)      | nombre original                             |
| `mime_type`     | str(100)      |                                             |
| `size_bytes`    | int           |                                             |
| `chunk_count`   | int           | cuántos chunks se generaron                 |
| `status`        | str(20)       | `pending` / `indexed` / `failed`            |
| `error_message` | TEXT          | si `status=failed`                          |
| `uploaded_at`   | datetime      |                                             |

### `conversations`
| Columna         | Tipo          | Notas                                 |
|-----------------|---------------|---------------------------------------|
| `id`            | UUID (str)    | PK                                    |
| `assistant_id`  | UUID (FK)     | NOT NULL, ON DELETE CASCADE           |
| `title`         | str(200)      | autogenerado o editable               |
| `created_at`    | datetime      |                                       |
| `updated_at`    | datetime      | se actualiza en cada mensaje          |

### `messages`
| Columna           | Tipo          | Notas                                               |
|-------------------|---------------|-----------------------------------------------------|
| `id`              | UUID (str)    | PK                                                  |
| `conversation_id` | UUID (FK)     | NOT NULL, ON DELETE CASCADE                         |
| `role`            | str(20)       | `user` / `assistant`                                |
| `content`         | TEXT          | NOT NULL                                            |
| `citations`       | JSON          | array de objetos (solo si `role=assistant`)         |
| `created_at`      | datetime      |                                                     |

## Contratos de API

Todos los endpoints devuelven JSON. Errores usan convención HTTP estándar
con body `{"detail": "mensaje"}`.

### Asistentes

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
  "name": "Experto Legal",
  "instructions": "Eres un abogado especializado...",
  "description": "Responde consultas legales sobre contratos"
}
```

Respuesta 201: el asistente creado incluyendo `id`, `search_index`,
`created_at`.

### Documentos

```
POST   /api/assistants/{id}/documents      # multipart/form-data
GET    /api/assistants/{id}/documents
DELETE /api/assistants/{id}/documents/{doc_id}
```

`POST` acepta un archivo en el campo `file`. Respuesta 202 con el documento
en estado `pending`. El cliente hace polling o el servidor procesa síncrono
(decisión: **síncrono** para MVP — el Día 2 confirmamos tiempos; si un PDF
grande pasa de 30s, se mueve a background task con FastAPI `BackgroundTasks`).

### Chat

```
POST   /api/conversations                                # crear conversación
GET    /api/assistants/{id}/conversations                # listar conversaciones del asistente
GET    /api/conversations/{id}/messages                  # cargar historial
POST   /api/conversations/{id}/messages                  # enviar mensaje
DELETE /api/conversations/{id}                           # borrar conversación
```

`POST /api/conversations` body:
```json
{ "assistant_id": "uuid" }
```

`POST /api/conversations/{id}/messages` body:
```json
{ "content": "¿Qué dice el contrato sobre la cláusula 3?" }
```

Respuesta 200:
```json
{
  "message": {
    "id": "uuid",
    "role": "assistant",
    "content": "Según el contrato, la cláusula 3...",
    "citations": [
      {
        "document_id": "uuid",
        "document_name": "contrato_2024.pdf",
        "page": 3,
        "chunk_text": "La cláusula 3 establece que..."
      }
    ],
    "created_at": "2026-04-21T10:00:00Z"
  }
}
```

## Flujo de una petición de chat

1. `POST /api/conversations/{id}/messages` con contenido del usuario.
2. Backend carga: asistente (instrucciones, `search_index`), conversación
   (historial de mensajes previos).
3. Backend guarda el mensaje del usuario en BD.
4. **Retrieval**: genera embedding del mensaje del usuario, consulta
   Azure AI Search sobre `search_index` con top_k=5 y semantic reranking
   activado. Filtra chunks con score < umbral.
5. **Construcción del prompt** (ver `RAG_SPEC.md`):
   - System: instrucciones del asistente + reglas de comportamiento RAG.
   - Historial: últimos N mensajes de la conversación (ver RAG_SPEC).
   - Context block: chunks recuperados con metadata.
   - User: mensaje actual.
6. **Generación**: llamada a Azure AI Foundry LLM.
7. **Post-procesado**: mapea las citas (el LLM devuelve IDs de chunks, el
   backend resuelve a objetos completos con document_name, página, snippet).
8. Backend guarda el mensaje del asistente (con citations JSON) en BD.
9. Responde al cliente.

## Variables de entorno

Ver `backend/.env.example` para la lista completa. Mínimas:

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
RETRIEVAL_SCORE_THRESHOLD=0.5
HISTORY_MAX_MESSAGES=10
```
