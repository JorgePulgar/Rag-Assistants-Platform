# TASKS — Desglose diario con dependencias

Cada tarea es atómica y mergeable. Las tareas se marcan `[ ]` pendientes,
`[x]` completadas. Las dependencias se indican con `⬅ Txxx`.

## Día 1 — Martes 21 abril — Scaffolding y CRUD asistentes

**Objetivo**: repositorio funcional, ambos stacks arrancan, endpoints
básicos de asistentes funcionando contra SQLite.

- [ ] **T001** — Crear repo en GitHub desde el navegador (a mano, Jorge).
- [ ] **T002** — Clonar repo localmente, copiar estos documentos a `/docs`,
  primer commit. ⬅ T001
- [ ] **T003** — Setup Azure: crear recurso Azure AI Foundry, desplegar
  `gpt-4o-mini` y `text-embedding-3-small`. Crear recurso Azure AI Search
  (tier Basic o superior). Guardar credenciales en `.env` local (a mano,
  Jorge — no lo hace Claude Code). ⬅ T001
- [ ] **T004** — Scaffolding backend: estructura de carpetas, `requirements.txt`,
  FastAPI arrancando en `:8000` con endpoint `/health`, SQLAlchemy
  configurado, SQLite creado automáticamente. ⬅ T002
- [ ] **T005** — Scaffolding frontend: Vite + React + TS + Tailwind +
  shadcn init. `npm run dev` arranca en `:5173` con página vacía. ⬅ T002
- [ ] **T006** — `.gitignore` completo (venv, node_modules, .env, .db,
  __pycache__, .vscode, .idea, dist, build). ⬅ T002
- [ ] **T007** — `.env.example` en backend con todas las variables
  documentadas. ⬅ T004
- [ ] **T008** — Modelos SQLAlchemy: `Assistant`, `Document`,
  `Conversation`, `Message`. Migración automática al arranque. ⬅ T004
- [ ] **T009** — Pydantic schemas para `Assistant` (Create, Update, Read).
  ⬅ T008
- [ ] **T010** — Router `api/assistants.py` con los 5 endpoints CRUD.
  Lógica en `services/assistant_service.py`. ⬅ T009
- [ ] **T011** — Generación de `search_index` al crear asistente
  (solo el nombre; el índice real se crea en T018 del Día 2).
  ⬅ T010
- [ ] **T012** — Tests básicos: crear, listar, actualizar, borrar
  asistente. Con `TestClient` de FastAPI. ⬅ T010
- [ ] **T013** — Commit y push final del día con mensaje descriptivo.

**Checkpoint Día 1**: `curl localhost:8000/api/assistants` devuelve `[]`,
`POST` con body válido crea un asistente, `GET` lo lista.

---

## Día 2 — Miércoles 22 abril — Ingesta y vectorización

**Objetivo**: subir un PDF a un asistente queda indexado en Azure AI Search
en el índice del asistente y recuperable.

- [ ] **T014** — Client `clients/azure_openai.py`: wrapper para embeddings
  y LLM, lee config de `.env`. ⬅ T007
- [ ] **T015** — Client `clients/azure_search.py`: wrapper para crear
  índice, subir documentos, buscar. ⬅ T007
- [ ] **T016** — Parsers: `pdf.py`, `docx.py`, `pptx.py`, `text.py`.
  Cada uno devuelve `list[ParsedChunk]`. ⬅ T004
- [ ] **T017** — Tests de parsers con 1 fixture por formato. ⬅ T016
- [ ] **T018** — `services/ingestion.py`: función `index_document`:
  - resuelve parser por extensión
  - extrae chunks
  - aplica `RecursiveCharacterTextSplitter`
  - llama a embeddings en batches de 16
  - crea índice Azure Search si no existe
  - sube chunks con metadata
  - actualiza estado del documento en SQLite
  ⬅ T014, T015, T016
- [ ] **T019** — Modelo `Document` en SQLAlchemy ya estaba; añadir
  Pydantic schemas. ⬅ T008
- [ ] **T020** — Router `api/documents.py`: subir, listar, borrar.
  Subida con `UploadFile`, guarda archivo temporal, llama a ingestion,
  borra temporal. ⬅ T018
- [ ] **T021** — Endpoint de borrado: elimina chunks del índice Azure Search
  (filter by `document_id`) y la fila de SQLite. ⬅ T020
- [ ] **T022** — Test manual: subir un PDF real a un asistente, verificar
  en Azure Portal que el índice existe y tiene chunks.
- [ ] **T023** — Test automático de aislamiento (`test_isolation.py`,
  versión ingesta solamente). ⬅ T018
- [ ] **T024** — Commit y push.

**Checkpoint Día 2**: subir un PDF a un asistente lo indexa correctamente
en su índice propio, y el test de aislamiento pasa.

---

## Día 3 — Jueves 23 abril — Chat con RAG y citas

**Objetivo**: enviar un mensaje a un asistente devuelve una respuesta del
LLM con citas estructuradas, fundamentada en los docs del asistente.

- [ ] **T025** — `services/retrieval.py`: función `retrieve`:
  - genera embedding de la query
  - query híbrida a Azure Search (keyword + vector + semantic rerank)
  - filtra por score threshold
  - devuelve top_k chunks con metadata completa
  ⬅ T014, T015
- [ ] **T026** — `services/rag.py`: función `generate_response`:
  - carga asistente e historial de conversación
  - llama a retrieve
  - si retrieve vacío → respuesta hardcoded "no sé"
  - construye prompt según RAG_SPEC
  - llama al LLM
  - post-procesa citas: extrae `[CITA:chunk_id]`, resuelve a objetos
  - devuelve `{content, citations}`
  ⬅ T025
- [ ] **T027** — Modelos `Conversation` y `Message` en SQLAlchemy ya
  existen; añadir schemas y validaciones. ⬅ T008
- [ ] **T028** — Router `api/chat.py`:
  - `POST /conversations` crea conversación
  - `GET /assistants/{id}/conversations` lista
  - `GET /conversations/{id}/messages` historial
  - `POST /conversations/{id}/messages` envía mensaje, llama a RAG,
    guarda user+assistant messages, devuelve assistant message
  - `DELETE /conversations/{id}`
  ⬅ T026, T027
- [ ] **T029** — Test `test_rag_prompt.py` con los 3 casos del RAG_SPEC. ⬅ T026
- [ ] **T030** — Test de aislamiento end-to-end: pregunta al asistente B
  sobre un tema del asistente A y verifica que responde "no sé". ⬅ T028
- [ ] **T031** — Commit y push.

**Checkpoint Día 3**: `curl` al endpoint de chat con un asistente que
tiene documentos devuelve una respuesta coherente con citas; con un
asistente sin documentos devuelve el mensaje de "no sé".

---

## Día 4 — Viernes 24 abril — Frontend

**Objetivo**: UI funcional con las 3 vistas conectadas al backend.

- [ ] **T032** — Cliente API en `frontend/src/api/client.ts` con axios
  configurado. Tipos TS espejando los Pydantic schemas. ⬅ T005
- [ ] **T033** — Layout principal: sidebar con lista de asistentes +
  área principal. ⬅ T032
- [ ] **T034** — Vista lista de asistentes: card por asistente, botón
  "Nuevo", botones editar/borrar por card. ⬅ T033
- [ ] **T035** — Formulario crear/editar asistente en Dialog de shadcn,
  con campos nombre, instrucciones, descripción. Validación básica. ⬅ T034
- [ ] **T036** — Vista detalle de asistente: info + lista de documentos +
  uploader. ⬅ T034
- [ ] **T037** — Uploader de documentos: input file + botón subir +
  progreso + lista con botón borrar por documento. ⬅ T036
- [ ] **T038** — Vista de chat: selector de conversación (o "nueva"),
  historial de mensajes, input de mensaje, botón enviar. ⬅ T033
- [ ] **T039** — Componente `MessageBubble` con diferencia visual
  user/assistant. ⬅ T038
- [ ] **T040** — Componente `CitationBlock`: pill `[1]`, `[2]` en el texto
  + panel expandible al hacer click con nombre del doc, página, snippet. ⬅ T038
- [ ] **T041** — Manejo de estado "cargando" mientras el LLM responde
  (skeleton o spinner en la burbuja del assistant). ⬅ T038
- [ ] **T042** — Toasts de error con shadcn cuando falla cualquier
  request. ⬅ T032
- [ ] **T043** — Commit y push.

**Checkpoint Día 4**: flujo completo funcional de punta a punta desde
el navegador.

---

## Día 5 — Sábado 25 abril — Integración, pulido y edge cases

**Objetivo**: proyecto robusto para la demo, sin bugs obvios.

- [ ] **T044** — Probar flujo end-to-end 3 veces con documentos reales
  distintos. Anotar todos los bugs encontrados.
- [ ] **T045** — Arreglar bugs de T044 (tarea abierta, hasta N sub-bugs).
- [ ] **T046** — Manejo de edge cases de ingesta: PDF corrupto,
  archivo vacío, formato no soportado, archivo > 10MB. ⬅ T018
- [ ] **T047** — Manejo de edge cases de chat: conversación sin asistente
  (borrado), mensaje vacío, mensaje muy largo. ⬅ T028
- [ ] **T048** — Loading states en frontend para todas las operaciones
  async. ⬅ T032
- [ ] **T049** — Empty states: "no tienes asistentes", "este asistente no
  tiene documentos", "empieza una conversación". ⬅ T033
- [ ] **T050** — Confirmaciones destructivas: dialog "¿seguro que quieres
  borrar este asistente? se borrarán X documentos y Y conversaciones".
  ⬅ T034
- [ ] **T051** — Pulido visual: paleta coherente, espaciados, tipografía.
  No perfeccionismo — una pasada global. ⬅ T033
- [ ] **T052** — Commit y push.

**Checkpoint Día 5**: un usuario que nunca ha visto la app la usa sin
preguntar nada y no se bloquea.

---

## Día 6 — Domingo 26 abril — Documentación y vídeo

**Objetivo**: entregables no-código completos.

- [ ] **T053** — `PROGRESS.md` final: snapshot del estado del proyecto.
- [ ] **T054** — Diagrama de arquitectura (Excalidraw o Mermaid) exportado
  a `docs/architecture.png`. Incluye: frontend, backend, SQLite, Azure
  OpenAI, Azure AI Search, flecha del flujo de chat.
- [ ] **T055** — README completo:
  - Descripción del producto
  - Stack tecnológico
  - Arquitectura (embeber imagen de T054)
  - Decisiones de diseño clave (referenciar CONSTITUTION y RAG_SPEC)
  - Guía de ejecución local paso a paso (backend + frontend)
  - Cómo se cumple el core (aislamiento, persistencia, citas)
  - Limitaciones conocidas
  ⬅ T054
- [ ] **T056** — Preparar 2 asistentes de demo con 2-3 documentos cada
  uno (ej: "Experto Fiscal 2024" con guías de Hacienda, "Asistente de
  Cocina Italiana" con recetarios).
- [ ] **T057** — Guion del vídeo de demo (5 min máx): intro (30s),
  creación asistentes (1min), subida docs (45s), chat con cada asistente
  demostrando aislamiento (1.5min), persistencia recargando (45s),
  cierre (30s).
- [ ] **T058** — Grabar vídeo. Herramienta: OBS o Loom.
- [ ] **T059** — Subir vídeo a YouTube no listado (o Google Drive) y
  enlazar en README. ⬅ T058
- [ ] **T060** — Commit final con versión etiquetada `v1.0`.

---

## Día 7 — Lunes 27 abril — Buffer

**Objetivo**: lo que se torció.

- [ ] **T061** — Priorizar por impacto: bugs de demo > pulido > features.
- [ ] **T062** — Si todo OK: features extra en orden de valor:
  streaming (SSE), mejor manejo de contexto largo, exportar conversación.
- [ ] **T063** — Preparar presentación (slides breves o guion) para el
  día de exposición. Este **no** se graba: es por si te toca presentar
  en clase.

---

## Reglas para Claude Code sobre este fichero

- Cada sesión, Claude Code lee este fichero y trabaja sobre la tarea
  marcada como siguiente pendiente cuyas dependencias estén resueltas.
- Al completar una tarea: cambia `[ ]` a `[x]` en el commit.
- No añadir tareas nuevas sin aprobación explícita de Jorge.
- Si una tarea es más grande de lo estimado, se parte en sub-tareas
  (T001a, T001b, ...) antes de empezar, no durante.
