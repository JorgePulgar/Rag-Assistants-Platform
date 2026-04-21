# PROJECT BRIEF — RAG Assistants Platform

## What we are building

A full-stack application that lets users create multiple conversational
assistants, each with its own system instructions and its own isolated
document base. The user chats with an assistant and receives answers that
are grounded **exclusively** in that assistant's documents, with structured
citations.

## Why (the problem)

Teams adopting generative AI internally need specialised assistants (legal,
technical, onboarding, support, etc.) without mixing knowledge between
domains. Generic chatbots hallucinate; well-isolated RAG assistants answer
with traceability.

## Academic deliverable

This project is a university assignment with a 7-day delivery window.
The required deliverables are:

1. Public GitHub repository with complete, runnable code.
2. Technical README with architecture, design decisions, and setup guide.
3. Demo video, 3–5 minutes long.

## Core functionality (mandatory)

### Assistant CRUD
- Create, list, update, delete.
- Minimum fields: `name`, `instructions` (system prompt), `description`
  (optional).

### Documents per assistant
- Upload, list, delete documents attached to a specific assistant.
- Required formats: PDF, DOCX, PPTX, TXT, MD.
- OCR is not required (documented as a known limitation).

### Ingestion and vectorisation
- Text extraction from the document.
- Chunking with justified parameters.
- Embedding generation.
- Storage in a per-assistant Azure AI Search index.

### Isolated RAG chat
- Select assistant, send message, receive response.
- Flow: retrieve from the assistant's index → build prompt with instructions
  + history + context → generate with the LLM → return response with
  structured citations.
- Explicit "I don't know" behaviour when evidence is insufficient.

### Chat persistence and conversational memory
- Conversation history is stored in SQLite.
- The assistant remembers what was said **within the same conversation**:
  every LLM call includes the last N messages as prior context, so
  follow-up questions work naturally ("and what about the next clause?"
  refers back to the previously discussed one).
- Previous conversations can be resumed after closing the browser, the
  backend, or the whole machine. The full thread is reloaded from SQLite.
- Users can start a new conversation at any time; each conversation is a
  separate thread with its own memory.
- **Not included**: cross-conversation memory (assistant remembering facts
  about the user across different conversations). This is an explicit
  non-goal for the MVP.

### Full-stack application
- React frontend with UI for the three modules (assistants, documents,
  chat).
- FastAPI backend with a REST API.

### UI language

The UI is in English. Assistant names, instructions, document content, and
chat messages stay in whatever language the user writes them in — that is
data, not UI. The demo video is recorded in Spanish (narration) but the
interface displayed on screen is English throughout.

## Out of scope (explicitly)

The following are not part of the MVP and are **not implemented** unless
Day 7 (buffer) has spare time:

- User authentication / multi-tenancy.
- Response streaming (SSE).
- OCR of scanned images.
- Production deployment.
- Sharing assistants between users.
- Document versioning.
- Chat history search.

Any proposal to add something out of scope during development is rejected
by default. The Day 7 buffer is for **bugs**, not scope creep.

## Acceptance criteria

The project is considered complete when, in the recorded demo, the
following can be shown:

1. Create two assistants with distinct instructions (e.g. "Legal Expert"
   and "Cooking Assistant").
2. Upload at least two distinct documents to each assistant.
3. Chat with the first assistant and receive answers with accurate
   citations to its documents.
4. Switch to the second assistant, ask the same topical question from
   the first, and verify it answers "I don't have information" (isolation).
5. Close the browser, reopen, select the first assistant's conversation,
   and continue where it left off.
6. See citations rendered as expandable blocks with document name, page
   (when applicable), and the relevant snippet.

## Audience

**Primary**: the course evaluator. They want the brief satisfied with
technical quality and clear documentation.

**Secondary**: AI Engineer recruiters browsing the repo afterwards. They
want signals of technical judgement (justified decisions, minimal testing,
clean architecture, coherent commit history).

We do not optimise for any commercial audience in this iteration.
