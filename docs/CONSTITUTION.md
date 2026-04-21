# CONSTITUTION — Principios no negociables del proyecto

Este documento recoge las reglas que **no se discuten** durante el desarrollo.
Cualquier decisión técnica debe respetar estos principios. Si una propuesta
los viola, la propuesta se rechaza — no al revés.

---

## 1. Aislamiento estructural por asistente

Cada asistente tiene un **índice propio en Azure AI Search** nombrado de forma
determinista a partir de su ID. El aislamiento es **estructural**, no lógico:
no se comparte un índice global con filtros por `assistant_id`.

**Razón**: un bug en un filtro contamina todas las respuestas. Un bug en el
nombrado del índice falla ruidosamente en vez de silenciosamente. El enunciado
exige demostrar aislamiento en la demo; esta decisión lo hace trivial.

**Consecuencia**: crear un asistente implica crear un índice. Borrar un
asistente implica borrar el índice. Estas operaciones son transaccionales con
la fila en SQLite.

## 2. Citas siempre estructuradas

Las respuestas del chat devuelven citas como **objetos JSON estructurados**,
nunca como strings embebidos en el texto. El schema mínimo es:

```json
{
  "document_id": "uuid",
  "document_name": "contrato_2024.pdf",
  "page": 3,
  "chunk_text": "fragmento relevante, máximo 300 caracteres"
}
```

**Razón**: el frontend renderiza las citas como bloques expandibles. Strings
embebidos del tipo `[Doc 1, pág. 3]` son imposibles de renderizar bien y se
rompen en cuanto el LLM decide escribirlos diferente.

## 3. No inventar respuestas

Si la recuperación no devuelve chunks con score suficiente, el asistente
responde explícitamente que **no tiene información** para contestar.
El prompt del sistema incluye esta instrucción y el endpoint devuelve la
respuesta sin citas (array vacío).

La respuesta de "no sé" debe ser **informativa**: qué buscó, por qué no
encontró. No un string genérico.

**Razón**: el enunciado lo exige explícitamente. Además, una alucinación
en la demo invalida todo el proyecto ante el evaluador.

## 4. Persistencia explícita del chat

Toda conversación se guarda en SQLite con `conversation_id`, `assistant_id`,
y los mensajes asociados con rol (`user` | `assistant`), contenido, citas
(si aplica) y timestamp. Al reanudar una conversación, se carga el historial
completo desde BD — nunca se depende de estado en memoria del servidor.

**Razón**: el backend debe poder reiniciarse sin perder conversaciones.
Es un requisito del enunciado y una buena práctica básica.

## 5. Tests mínimos en la lógica core

No se exige cobertura alta, pero **sí** tests sobre:
- Aislamiento: crear dos asistentes, subir docs distintos a cada uno,
  verificar que una query a uno no devuelve chunks del otro.
- Parsing: al menos un test por tipo de documento soportado.
- Construcción del prompt RAG: verificar que incluye instrucciones + historial
  + contexto y que el "no sé" se activa con contexto vacío.

**Razón**: estos son los puntos donde un bug silencioso te cuesta la nota.
Un test que verifique el aislamiento en 10 segundos te ahorra un drama en
la demo.

## 6. Variables de entorno para todo lo configurable

Cero credenciales en el código. Cero URLs hardcoded. Todo vive en `.env`
documentado en `.env.example`. Esto incluye: endpoints de Azure, API keys,
nombre del índice base, parámetros de chunking, modelo LLM a usar.

## 7. Commits incrementales con mensajes convencionales

`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`. Un commit por
tarea coherente. Push diario como mínimo. El histórico del repo es parte
del entregable, no un artefacto.

## 8. El README final se escribe al final

Durante el desarrollo existe un README mínimo y un `PROGRESS.md` que se va
actualizando. El README completo se escribe el Día 6 con perspectiva.
No se mantiene documentación completa en paralelo al desarrollo.
