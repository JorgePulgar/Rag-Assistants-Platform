# CODING CONVENTIONS

Reglas de estilo y estructura. Aplica a todo el código del proyecto,
escrito a mano o generado por Claude Code.

## Python

### Formato
- **Black** como formatter (line length 100).
- **isort** para ordenar imports.
- **ruff** como linter (configuración mínima, reglas por defecto).

### Tipos
- **Type hints obligatorios** en todas las funciones públicas (firma completa).
- En funciones privadas (`_prefijo`), los tipos son recomendados pero no
  exigidos.
- Pydantic models para todo lo que cruza el borde HTTP (request/response).
- SQLAlchemy models separados de Pydantic schemas — nunca se mezclan.

### Naming
- `snake_case` para funciones, variables, módulos.
- `PascalCase` para clases.
- `UPPER_SNAKE` para constantes a nivel de módulo.
- Nombres descriptivos; no se abrevia salvo convenciones establecidas
  (`db`, `id`, `ctx`).

### Estructura de módulos
- Un fichero = una responsabilidad.
- Los routers de FastAPI (`api/`) no contienen lógica de negocio —
  delegan a `services/`.
- Los services no saben de HTTP — reciben y devuelven tipos Python puros o
  Pydantic models, nunca `Request`/`Response`.
- Los clients (`clients/`) son wrappers finos sobre SDKs externos; ocultan
  la API del SDK tras una interfaz propia.

## TypeScript / React

### Formato
- **Prettier** con defaults (2 espacios, semicolons, single quotes).
- **ESLint** con `eslint-config-react-app`.

### Tipos
- `strict: true` en `tsconfig.json`.
- Tipos explícitos para props de componentes (`interface Props { ... }`).
- `type` vs `interface`: `interface` para props y objetos públicos,
  `type` para uniones y utilidades.

### Componentes
- Un componente por fichero.
- Componentes funcionales + hooks. No class components.
- Custom hooks empiezan con `use` (regla de React).
- Nombre del fichero = nombre del componente (`AssistantList.tsx` exporta
  `AssistantList`).

### State management
- React state local por defecto.
- Contextos solo para estado verdaderamente global (asistente seleccionado,
  lista de asistentes). **No se usa Redux**.

## Manejo de errores

### Backend
- **Fail fast**: validación temprana con Pydantic. Si algo llega mal, 4xx
  inmediato.
- **Excepciones específicas**: el backend define excepciones propias
  (`AssistantNotFoundError`, `IngestionError`, `RetrievalError`) en
  `app/exceptions.py`.
- **Exception handlers globales** en `main.py`: mapean excepciones de
  dominio a status codes HTTP.
- **Nunca** `except Exception: pass`. Si no se sabe qué hacer con un error,
  se propaga.
- **Errores a Azure**: se capturan, se loggean, y se reenvían como 502 Bad
  Gateway con mensaje genérico al cliente.

### Frontend
- Toasts de error con shadcn `toast` para errores recuperables.
- Error boundaries de React para errores catastróficos (pantalla "algo ha
  ido mal" con botón de recarga).

## Logging

- Backend: `logging` estándar de Python, configurado en `main.py`.
- Nivel por defecto: `INFO`. `DEBUG` se activa con variable de entorno
  `LOG_LEVEL=DEBUG`.
- Formato: `%(asctime)s [%(levelname)s] %(name)s: %(message)s`.
- **Se loggea siempre**:
  - Inicio y fin de ingesta de documento (con chunk_count y duración).
  - Query al retrieval (con top_k real devuelto y scores).
  - Errores de Azure (endpoint, status, mensaje).
- **Nunca se loggea**: API keys, contenido completo de documentos,
  mensajes de usuarios completos (solo los primeros 80 caracteres para
  trazabilidad).

## Tests

- **pytest** en backend.
- Tests en `backend/tests/` con `test_*.py` naming.
- Fixtures en `backend/tests/fixtures/`.
- Un test por caso, nombre descriptivo:
  `test_retrieval_returns_empty_when_no_docs_for_assistant`.
- Los tests críticos están en `CONSTITUTION.md` — son obligatorios.
- No se mockea Azure Search en los tests de aislamiento; se usa una
  instancia real con prefijo de índice `test-`. Si Azure no está
  disponible, esos tests se saltan con `pytest.mark.skipif`.

## Commits

Convención `tipo(ámbito?): mensaje`:

- `feat(backend): add assistant CRUD endpoints`
- `fix(rag): handle empty retrieval result`
- `refactor(frontend): extract MessageBubble from ChatView`
- `docs: update README with setup instructions`
- `test(isolation): add cross-assistant retrieval test`
- `chore: bump dependencies`

Un commit = un cambio coherente. **No se agrupan** cambios sin relación en
el mismo commit.

## Comentarios

- Docstrings en toda función pública (`"""Breve descripción. Args: ...
  Returns: ..."""`).
- Comentarios inline solo para **el por qué**, no para **el qué**.
  - Malo: `# incrementa i en 1`
  - Bueno: `# se suma 1 porque Azure Search indexa páginas desde 1, no 0`
- Comentarios `# TODO:` solo con justificación y (si aplica) issue/ticket.
  No se dejan `# FIXME` sin dueño.

## Dependencias

- Backend: `requirements.txt` + `requirements-dev.txt`.
- Frontend: `package.json` con versiones pinned (no `^` ni `~`).
- No se añade una dependencia nueva sin justificar por qué no sirve lo que
  ya está. Cada dependencia es superficie de ataque y mantenimiento.

## Secretos

- Cero secretos en el código. Cero en commits (verificar con
  `git diff --cached` antes de commitear).
- `.env` en `.gitignore`.
- `.env.example` con todos los nombres de variables y comentarios sobre
  qué va en cada una (sin valores reales).
