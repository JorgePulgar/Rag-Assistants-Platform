# Plataforma de Asistentes RAG

Plataforma completa de Generación Aumentada por Recuperación (RAG) que permite crear múltiples asistentes de IA aislados, cada uno con su propia base de documentos, memoria conversacional persistente y citas estructuradas.

Desarrollado como proyecto universitario en 7 días sobre **Azure AI Foundry** y **Azure AI Search**, con backend en **FastAPI** y frontend en **React**.

> Para la documentación técnica completa (arquitectura, decisiones de diseño, guía de instalación), consulta el [README en inglés](README.md).

---

## Qué hace

- **Crea asistentes** — cada uno con nombre, instrucciones personalizadas y base de conocimiento aislada.
- **Sube documentos** — PDF, DOCX, PPTX, TXT y MD se procesan, dividen en fragmentos, se vectorizan y se almacenan en un índice propio por asistente en Azure AI Search.
- **Chat con citas** — cada respuesta se basa en los documentos del asistente. Las marcas `[1]`, `[2]` enlazan a tarjetas expandibles con el nombre del documento, la página y el fragmento relevante.
- **Memoria persistente** — las conversaciones se guardan en SQLite. Cierra la pestaña, reinicia el servidor, apaga el equipo — la conversación continúa exactamente donde la dejaste.
- **"No lo sé" por diseño** — si la búsqueda no devuelve fragmentos relevantes, el LLM nunca es invocado. Se devuelve un mensaje informativo predefinido.

---

## Pila tecnológica

| Capa | Tecnología |
|------|-----------|
| Frontend | React 18 + Vite + TypeScript + Tailwind + shadcn/ui |
| Backend | FastAPI + SQLAlchemy + SQLite |
| Embeddings | Azure AI Foundry — `text-embedding-3-small` (1536 dims) |
| LLM | Azure AI Foundry — `gpt-4o-mini` |
| Búsqueda vectorial | Azure AI Search — un índice por asistente |

---

## Decisiones de diseño destacadas

### Aislamiento estructural por índice

Cada asistente tiene su propio índice en Azure AI Search (`assistant-{id_hex}`). No existe un índice compartido con filtros — el aislamiento es estructural. Un bug en un filtro contamina todas las respuestas en silencio; un bug en el nombre del índice falla de forma ruidosa. Ver `CONSTITUTION.md` §1.

### Reescritura de consultas con LLM

Antes de buscar, una llamada adicional a `gpt-4o-mini` reescribe el mensaje del usuario en una consulta independiente, resolviendo referencias como "dime más sobre el punto 2". Sin esto, esa frase se vectoriza sin señal temática y la búsqueda devuelve fragmentos irrelevantes. Ver `RAG_SPEC.md` §"Query rewriting".

### Comportamiento "no lo sé"

Si la recuperación no supera el umbral de puntuación del re-ranker semántico, el LLM no es llamado. La respuesta informativa predefinida es devuelta directamente. Esto hace que la alucinación sea arquitectónicamente imposible en el camino de recuperación vacía. Ver `CONSTITUTION.md` §3.

### Memoria conversacional en SQLite

Cada mensaje se escribe a SQLite con su rol, contenido y citas. En cada llamada al LLM se cargan los últimos `HISTORY_MAX_MESSAGES=10` mensajes desde la base de datos — sin estado en memoria. La memoria sobrevive reinicios del servidor y cierres del navegador. Ver `CONSTITUTION.md` §4.

---

## Instalación rápida

```bash
# Backend
cd backend
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # macOS / Linux
pip install -r requirements.txt
copy .env.example .env        # rellenar con credenciales Azure
uvicorn app.main:app --reload --port 8000

# Frontend (en otra terminal)
cd frontend
npm install
npm run dev
```

La API estará disponible en `http://localhost:8000` y la interfaz en `http://localhost:5173`.

Para la guía completa de instalación y la lista de variables de entorno, consulta el [README en inglés](README.md#local-setup).

---

## Limitaciones conocidas

- Sin autenticación — cualquier usuario con acceso a la instancia puede ver y modificar todos los datos.
- Sin memoria entre conversaciones — el asistente no recuerda hechos de conversaciones anteriores.
- Sin OCR — los PDFs escaneados (solo imagen) no generan texto indexable.
- Ingesta síncrona — archivos grandes pueden tardar hasta 30 segundos en procesarse.
- Sin streaming — la respuesta del LLM se devuelve completa al finalizar la generación.

---

*Documentación técnica completa en inglés: [README.md](README.md)*
