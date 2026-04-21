# CLAUDE.md — Rules for Claude Code in this repository

This file is read automatically by Claude Code when the project opens. It
defines how you must behave during development.

## Mandatory context documents

**Before starting any task**, read these files in this order:

1. `docs/CONSTITUTION.md` — non-negotiable principles.
2. `docs/PROJECT_BRIEF.md` — what we build and acceptance criteria.
3. `docs/ARCHITECTURE.md` — stack, folder structure, data model.
4. `docs/CODING_CONVENTIONS.md` — style and conventions.
5. `docs/TASKS.md` — pending tasks with dependencies.

For RAG-related tasks (ingestion, chunking, prompt, retrieval, citations)
additionally read:

6. `docs/RAG_SPEC.md` — technical specification of the RAG pipeline.

## Project-specific skills

Two local skills live under `.claude/skills/`:

- `rag-patterns/SKILL.md` — concrete RAG implementation patterns.
- `azure-integration/SKILL.md` — Azure client conventions.

Load them when the task requires them. Do not load them preemptively.

## Working rules

### Per-task flow
1. Identify the next pending task in `docs/TASKS.md` whose dependencies
   are satisfied. Tasks are organised by **phase**; complete phases in
   order. Do not start Phase N+1 until Phase N's checkpoint passes
   unless Jorge explicitly says otherwise.
2. If there is ambiguity about what to implement, **ask before coding**.
   A short question is better than a wrongly executed task.
3. Implement the task completely (not halfway).
4. Run the relevant tests if they exist.
5. Mark the task as `[x]` in `docs/TASKS.md`.
6. Append one line to `docs/PROGRESS.md` at the end of the session
   indicating which phase advanced and any noteworthy decisions (not
   on every task — once per session).
7. Commit using a conventional message (`feat:`, `fix:`, `refactor:`, etc.).
8. Push to the remote.

### Never
- **Do not modify** `CONSTITUTION.md`, `PROJECT_BRIEF.md`, or `RAG_SPEC.md`
  without explicit approval. They record decisions already made.
- **Do not add features** that are not in `TASKS.md`.
- **Do not add dependencies** without justifying why existing ones do not
  suffice.
- **Do not write code** you do not understand. If `RAG_SPEC` does not
  cover something, **ask**.
- **Do not commit secrets**. Verify `.env` is in `.gitignore` before
  every commit.
- **Do not take architectural decisions** on the fly. Architecture is
  fixed in `ARCHITECTURE.md`.

### Always
- **Full typing** in Python (type hints) and TypeScript (strict).
- **Commit messages** follow `CODING_CONVENTIONS.md`.
- **One commit per coherent change**. Do not group unrelated edits.
- **Ask** on any material doubt about design or scope.

### RAG core rules

These are the critical spots of the project. Work with extra care:

1. **Per-assistant isolation**: one Azure AI Search index per assistant.
   Never a shared index with filters. If any shortcut suggests shared
   filtering, **reject the shortcut**.

2. **Structured citations**: always JSON objects with `document_id`,
   `document_name`, `page`, `chunk_text`. Never inline strings like
   `[Doc 1, p. 3]`.

3. **"I don't know" behaviour**: if retrieval returns zero chunks above
   threshold, **do not call the LLM**. Return a hardcoded message.

4. **Prompt built per RAG_SPEC**: system prompt with rules + retrieved
   context + history + current question. Do not invent alternative
   formats.

5. **Conversational memory is mandatory**: every LLM call includes the
   last `HISTORY_MAX_MESSAGES` messages from the conversation, loaded
   from SQLite with their original roles preserved. Memory survives
   backend restarts because messages live in a file on disk, not in
   process memory. Any code that breaks this guarantee is a bug.

### Testing

- `tests/test_isolation.py` is **critical**. Run it every time you touch
  ingestion or retrieval.
- Other tests: run at least the ones that cover the modified module.
- Do not reduce existing coverage with a change.

## Language

Every artefact in this repository is written in English:

- Code, comments, identifiers.
- UI strings shown to the user.
- Log messages and error messages.
- Commit messages.
- All documentation under `/docs` and skills.
- The main `README.md`.

Exceptions (intentional Spanish content):
- `README.es.md` is a courtesy version for Spanish speakers — it
  summarises the main README and links back to it for technical depth.
- Demo data (assistant names, sample documents, sample chat messages)
  may be in Spanish to showcase multilingual support. That is user data,
  not UI.

## About the README

- The root README during development is the minimal placeholder.
- The full English README is written on Day 6 (task T055).
- The Spanish courtesy README is written on Day 6 (task T056).
- Until then, `docs/PROGRESS.md` is the living project record.
