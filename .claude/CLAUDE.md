# CLAUDE.md — Reglas para Claude Code en este repositorio

Este archivo se lee automáticamente por Claude Code al abrir el proyecto.
Define cómo debes comportarte durante el desarrollo.

## Documentos de contexto obligatorios

**Antes de empezar cualquier tarea**, lee estos archivos en este orden:

1. `docs/CONSTITUTION.md` — principios no negociables.
2. `docs/PROJECT_BRIEF.md` — qué construimos y criterios de aceptación.
3. `docs/ARCHITECTURE.md` — stack, estructura de carpetas, modelo de datos.
4. `docs/CODING_CONVENTIONS.md` — estilo y convenciones.
5. `docs/TASKS.md` — tareas pendientes con dependencias.

Para tareas relacionadas con RAG (ingesta, chunking, prompt, retrieval,
citas) lee adicionalmente:

6. `docs/RAG_SPEC.md` — especificación técnica del pipeline RAG.

## Skills específicas del proyecto

En `.claude/skills/` hay dos skills locales:

- `rag-patterns/SKILL.md` — patrones concretos de implementación RAG.
- `azure-integration/SKILL.md` — convenciones para clientes Azure.

Cárgalas cuando la tarea lo requiera. No las cargues de forma preventiva.

## Reglas de trabajo

### Flujo por tarea
1. Identifica la siguiente tarea pendiente en `docs/TASKS.md` cuyas
   dependencias estén cumplidas.
2. Si hay ambigüedad sobre qué implementar, **pregunta antes de codear**.
   Mejor una pregunta corta que una tarea mal ejecutada.
3. Implementa la tarea completa (no a medias).
4. Ejecuta los tests relevantes si existen.
5. Marca la tarea como `[x]` en `docs/TASKS.md`.
6. Actualiza `docs/PROGRESS.md` con una línea del día si ha terminado la
   sesión (no en cada tarea).
7. Haz commit con mensaje convencional (`feat:`, `fix:`, `refactor:`, etc.).
8. Push al remoto.

### Qué NO hacer nunca
- **No modifiques** `CONSTITUTION.md`, `PROJECT_BRIEF.md`, `RAG_SPEC.md`
  sin aprobación explícita. Son documentos de decisiones tomadas.
- **No añadas features** que no estén en `TASKS.md`.
- **No añadas dependencias** sin justificar por qué no sirve lo existente.
- **No escribas código** sin entender qué vas a escribir. Si el `RAG_SPEC`
  no especifica algo, **pregunta**.
- **No commitees secretos**. Verifica `.env` está en `.gitignore` antes
  de cada commit.
- **No tomes decisiones de arquitectura** sobre la marcha. La arquitectura
  está decidida en `ARCHITECTURE.md`.

### Qué sí hacer siempre
- **Tipos completos** en Python (type hints) y TypeScript (strict).
- **Comentarios en español** cuando expliquen decisiones de negocio.
  Comentarios de código técnico pueden ir en inglés.
- **Mensajes de commit** siguiendo la convención de `CODING_CONVENTIONS.md`.
- **Un commit por cambio coherente**. No agrupes cambios no relacionados.
- **Preguntar** ante cualquier duda material sobre el diseño o alcance.

### Reglas específicas para el RAG core

Estos son los puntos críticos del proyecto. Trabaja con especial cuidado:

1. **Aislamiento por asistente**: un índice Azure AI Search por asistente.
   Nunca una colección única con filtros. Si algún atajo sugiere hacer
   filtros compartidos, **rechaza el atajo**.

2. **Citas estructuradas**: siempre objetos JSON con `document_id`,
   `document_name`, `page`, `chunk_text`. Nunca strings inline del tipo
   `[Doc 1, pág. 3]`.

3. **Comportamiento de "no sé"**: si el retrieval devuelve 0 chunks por
   encima del threshold, **no se llama al LLM**. Se devuelve un mensaje
   hardcoded.

4. **Prompt construido según RAG_SPEC**: system prompt con reglas +
   contexto recuperado + historial + pregunta actual. No inventes otro
   formato.

### Testing

- El test `tests/test_isolation.py` es **crítico**. Cada vez que toques
  ingesta o retrieval, ejecútalo.
- Otros tests: ejecuta al menos los que toquen el módulo modificado.
- No bajes la cobertura existente con un cambio.

## Sobre la comunicación con Jorge

- Jorge es AI Engineer junior con experiencia en Python, Azure y RAG.
- Habla español con Jorge. Los comentarios del código en español también.
- Sé directo. No adules. Si algo está mal, dilo.
- Si Jorge propone algo que viola la `CONSTITUTION.md`, señálalo
  explícitamente en lugar de obedecer.
- Cuando termines una tarea, resume en 2-3 líneas qué hiciste, no más.

## Sobre el README

- El README raíz durante el desarrollo es una versión mínima.
- El README completo se escribe el Día 6 (tarea T055).
- Hasta entonces, `docs/PROGRESS.md` es el registro vivo del proyecto.
