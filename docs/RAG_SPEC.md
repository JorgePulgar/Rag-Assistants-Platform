# RAG SPEC — Especificación del pipeline de Retrieval-Augmented Generation

Este documento es el **núcleo técnico** del proyecto. Detalla cada decisión
del pipeline RAG con su justificación. Jorge debe entender y defender cada
parámetro — si en la presentación te preguntan "por qué chunk_size 800", la
respuesta está aquí.

---

## Parsing por formato

Se implementa un parser por tipo de archivo. Todos devuelven una lista de
`ParsedChunk`:

```python
class ParsedChunk:
    text: str                    # contenido plano
    page: Optional[int]          # número de página (1-indexed) si aplica
    section: Optional[str]       # título de sección si aplica
```

**PDF (`pypdf`)**: se extrae texto página a página. Se asocia `page` al
número de página. Si una página tiene menos de 20 caracteres útiles se
descarta (suelen ser portadas o páginas en blanco).

**DOCX (`python-docx`)**: se itera por párrafos. No hay concepto nativo de
página, así que `page=None`. Si el documento tiene headings, se propaga el
heading más reciente como `section`.

**PPTX (`python-pptx`)**: se itera por slides. `page` = número de slide
(la gente habla de "diapositiva 3" igual que de "página 3"). Se extrae texto
de shapes y notas del ponente si existen.

**TXT / MD**: lectura directa, UTF-8 con fallback a latin-1. `page=None`.

**Errores**: si un parser falla, el documento queda en `status=failed` con
el mensaje de error guardado. No se aborta la petición — el usuario ve en
la UI que el documento falló y puede reintentarlo.

## Chunking

Se usa `RecursiveCharacterTextSplitter` de `langchain_text_splitters` con
separadores en cascada: `["\n\n", "\n", ". ", " ", ""]`.

**Parámetros**:
- `chunk_size = 800` caracteres.
- `chunk_overlap = 150` caracteres.

**Justificación de `chunk_size=800`**:
- Demasiado pequeño (< 400) pierde contexto local — un párrafo que
  desarrolla una idea se corta y el retrieval devuelve chunks sin coherencia.
- Demasiado grande (> 1500) mete ruido — un chunk de 2000 caracteres
  contiene información relevante **y** irrelevante; el LLM recibe contexto
  de baja señal y empeora la respuesta.
- 800 caracteres ≈ 120-150 tokens ≈ 1-2 párrafos bien formados. Es el punto
  dulce empírico para documentos en español de tipo legal/técnico.

**Justificación de `chunk_overlap=150`** (aprox. 18% del chunk):
- Sin overlap, una frase que cruza el límite se divide y ninguno de los dos
  chunks la contiene completa.
- 15-20% es el rango recomendado en la literatura y en las guías de Azure
  AI Search. Menos del 10% deja cortes feos; más del 25% infla el índice
  sin beneficio.

**Chunking por página (PDF/PPTX)**: cada chunk se asocia a **una sola**
página. Si un párrafo cruza páginas, se trata como dos chunks separados.
Esto es más conservador pero garantiza que la cita apunte a una página
concreta — decir "está en la página 3 o 4" en una cita es peor que tener
dos citas a páginas distintas.

**Metadata preservada por chunk**:
```python
{
  "chunk_id": "uuid",           # generado
  "document_id": "uuid",
  "document_name": "str",
  "page": int | None,
  "section": str | None,
  "text": "str",
  "chunk_index": int            # orden dentro del documento
}
```

## Embeddings

- Modelo: `text-embedding-3-small` (Azure Foundry deployment).
- Dimensiones: 1536.
- Batch size al indexar: 16 chunks por llamada (límite de Foundry cómodo y
  reduce latencia de ingesta).

**Por qué `-small` y no `-large`**:
- `-large` (3072 dim) cuesta ~6× más y aporta ~2% en benchmarks de
  retrieval. Para un MVP es inversión que no se justifica.
- Si en el futuro hay que mejorar calidad, se cambia el deployment y se
  reindexa. Es una variable de entorno, no una decisión de arquitectura.

## Azure AI Search: schema del índice

Cada asistente tiene un índice con este schema:

```python
fields = [
    SimpleField(name="chunk_id", type="Edm.String", key=True),
    SimpleField(name="document_id", type="Edm.String", filterable=True),
    SimpleField(name="document_name", type="Edm.String", retrievable=True),
    SimpleField(name="page", type="Edm.Int32", retrievable=True),
    SimpleField(name="section", type="Edm.String", retrievable=True),
    SearchableField(name="text", type="Edm.String", analyzer_name="es.microsoft"),
    SearchField(
        name="vector",
        type="Collection(Edm.Single)",
        searchable=True,
        vector_search_dimensions=1536,
        vector_search_profile_name="default-profile"
    ),
]
```

**Vector search profile**: HNSW con parámetros por defecto (`m=4`,
`ef_construction=400`). No merece la pena tunear para MVP.

**Semantic ranker**: se activa en las queries. Requiere configuración de
`semantic search` en el servicio — verificar tier del recurso (Basic o
superior).

**Analyzer en español**: `es.microsoft` mejora stemming y tokenización
para documentos en castellano.

## Retrieval

Dado un mensaje del usuario:

1. Generar embedding del mensaje (`text-embedding-3-small`).
2. Query híbrida a Azure AI Search:
   - Keyword search sobre `text` (con analyzer español).
   - Vector search sobre `vector` (k_nearest_neighbors=10).
   - Reciprocal Rank Fusion + semantic reranking.
3. Tomar top 5 resultados.
4. Filtrar los que tengan `@search.reranker_score < 1.5` (escala 0-4 de
   Azure semantic reranker). Este umbral se ajusta empíricamente el Día 3
   con documentos reales; 1.5 es el punto de partida conservador.

**Si tras filtrar quedan 0 chunks**: se activa el camino de "no sé" — no se
llama al LLM (ahorro de coste) y se devuelve una respuesta hardcodeada
informando al usuario.

## Construcción del prompt

El prompt tiene tres partes claras:

### System prompt

```
{instrucciones_del_asistente}

REGLAS DE COMPORTAMIENTO:
1. Responde SOLO con información presente en los documentos proporcionados
   en el CONTEXTO. No uses conocimiento general.
2. Si la información no está en el contexto, responde exactamente:
   "No tengo información suficiente en mis documentos para responder a esta
   pregunta. Lo que he buscado: [resumen breve]. Sugerencia: [próximo paso
   razonable]."
3. Cita las fuentes usando el formato [CITA:chunk_id] inline, donde chunk_id
   es el identificador del chunk del que proviene la información.
4. Sé conciso y directo. No repitas la pregunta del usuario.
5. Si hay información contradictoria entre chunks, menciona ambas versiones
   con sus citas.
```

### Contexto recuperado

Se inyecta como mensaje de rol `system` o `user` (decisión: **user**, porque
funciona mejor empíricamente con modelos tipo GPT-4):

```
CONTEXTO RECUPERADO:

[CITA:chunk_id_1]
Documento: contrato_2024.pdf | Página: 3
Contenido: La cláusula 3 establece que...

[CITA:chunk_id_2]
Documento: anexo_legal.pdf | Página: 7
Contenido: En caso de incumplimiento...

PREGUNTA DEL USUARIO: {mensaje_actual}
```

### Historial

Se inyectan los últimos `HISTORY_MAX_MESSAGES=10` mensajes de la
conversación (5 pares user/assistant) como mensajes previos en el array
`messages` de la API de OpenAI. El contexto recuperado y la pregunta actual
van como último `user` message.

**Por qué limitar a 10**: más historial no mejora la respuesta y consume
tokens. Si en la demo se nota que el LLM pierde contexto de mensajes muy
anteriores, se sube a 20.

## Post-procesado de respuesta

El LLM devuelve texto con marcas `[CITA:chunk_id]` intercaladas. El backend:

1. Extrae todos los `chunk_id` mencionados.
2. Para cada uno, busca en los resultados del retrieval el objeto completo
   (document_id, document_name, page, snippet de 300 chars).
3. Sustituye las marcas `[CITA:chunk_id]` por índices `[1]`, `[2]`, etc.
4. Devuelve al cliente:
   - `content`: texto con `[1]`, `[2]`, ... inline.
   - `citations`: array ordenado de objetos correspondientes.

El frontend renderiza cada `[n]` como un pill clicable que expande el
objeto de la cita correspondiente.

## Comportamiento de "no sé"

Se activa en dos lugares:

1. **Retrieval vacío** (pre-LLM): no se llama al LLM. Se devuelve
   hardcoded: "No he encontrado información relevante en los documentos de
   este asistente para responder a tu pregunta."

2. **Retrieval con resultados pero LLM no puede responder** (post-LLM):
   el LLM sigue la regla 2 del system prompt y devuelve el texto
   pre-formateado.

En ambos casos, `citations=[]`.

## Tests críticos

### `test_isolation.py`
```
1. Crear asistente A con índice A.
2. Crear asistente B con índice B.
3. Subir documento "legal.pdf" a A.
4. Subir documento "cocina.pdf" a B.
5. Query "cláusula contractual" al asistente B.
6. Assert: el retrieval del B devuelve 0 chunks de A.
7. Query "cláusula contractual" al asistente A.
8. Assert: el retrieval del A devuelve chunks de legal.pdf.
```

### `test_parsers.py`
- Un archivo de fixture por formato en `tests/fixtures/`.
- Verificar que el parser devuelve al menos 1 `ParsedChunk` con texto no
  vacío.
- Verificar que PDF asocia `page` correctamente.

### `test_rag_prompt.py`
- Con contexto: verificar que el prompt incluye las 3 secciones.
- Sin contexto: verificar que NO se llama al LLM y se devuelve el mensaje
  hardcoded.
- Con historial largo: verificar que se truncan a `HISTORY_MAX_MESSAGES`.

## Parámetros que son hiperparámetros (no constantes)

Todo lo siguiente vive en `.env` y puede tunearse sin tocar código:

| Parámetro                   | Default | Rango razonable |
|-----------------------------|---------|-----------------|
| `CHUNK_SIZE`                | 800     | 500 - 1200      |
| `CHUNK_OVERLAP`             | 150     | 80 - 250        |
| `RETRIEVAL_TOP_K`           | 5       | 3 - 10          |
| `RETRIEVAL_SCORE_THRESHOLD` | 1.5     | 1.0 - 2.5       |
| `HISTORY_MAX_MESSAGES`      | 10      | 4 - 20          |
