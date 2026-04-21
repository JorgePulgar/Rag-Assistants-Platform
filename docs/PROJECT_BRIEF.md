# PROJECT BRIEF — Plataforma de Asistentes RAG

## Qué construimos

Una aplicación full-stack que permite crear múltiples asistentes
conversacionales, cada uno con sus propias instrucciones y su propia base
documental aislada. El usuario chatea con un asistente y recibe respuestas
fundamentadas **exclusivamente** en los documentos de ese asistente, con
citas estructuradas.

## Por qué (problema que resuelve)

Los equipos que adoptan IA generativa internamente necesitan asistentes
especializados (legal, técnico, onboarding, soporte, etc.) sin mezclar
conocimientos entre dominios. Los chatbots genéricos alucinan; los asistentes
RAG bien aislados responden con trazabilidad.

## Entregable académico

Este proyecto es una práctica universitaria con entrega en 7 días.
Los entregables exigidos por el enunciado son:

1. Repositorio público de GitHub con código completo y ejecutable.
2. README técnico con arquitectura, decisiones y guía de ejecución.
3. Vídeo demo de 3–5 minutos.

## Funcionalidades core (obligatorias)

### CRUD de asistentes
- Crear, listar, editar, eliminar.
- Campos mínimos: `nombre`, `instrucciones` (system prompt), `descripción`
  (opcional).

### Documentos por asistente
- Subir, listar, eliminar documentos asociados a un asistente concreto.
- Formatos obligatorios: PDF, DOCX, PPTX, TXT, MD.
- OCR no requerido (se documenta como limitación).

### Ingesta y vectorización
- Extracción de texto del documento.
- Chunking con parámetros justificados.
- Generación de embeddings.
- Almacenamiento en un índice de Azure AI Search **por asistente**.

### Chat con RAG aislado
- Seleccionar asistente, enviar mensaje, recibir respuesta.
- Flujo: recuperación del índice del asistente → construcción de prompt con
  instrucciones + historial + contexto → generación con LLM → respuesta con
  citas estructuradas.
- Comportamiento explícito de "no sé" cuando no hay evidencia suficiente.

### Persistencia del chat
- Guardar historial de conversación en SQLite.
- Reanudar conversación previa.
- Iniciar conversación nueva.

### Aplicación full-stack
- Frontend React con interfaz para los tres módulos (asistentes, documentos,
  chat).
- Backend FastAPI con API REST.

## Fuera de alcance (explícitamente)

No forma parte del MVP y **no se implementa** salvo que sobre tiempo en el
Día 7 (buffer):

- Autenticación de usuarios / multi-tenancy.
- Streaming de respuestas (SSE).
- OCR de imágenes escaneadas.
- Despliegue en producción.
- Compartir asistentes entre usuarios.
- Versionado de documentos.
- Búsqueda dentro del historial de chats.

Cualquier propuesta de añadir algo fuera de alcance durante el desarrollo
se rechaza por defecto. El buffer del Día 7 es para **bugs**, no para scope
creep.

## Criterios de aceptación

El proyecto se considera completo cuando, en la demo grabada, se puede:

1. Crear dos asistentes con instrucciones distintas (ej: "Experto Legal" y
   "Asistente de Cocina").
2. Subir al menos 2 documentos a cada asistente, distintos entre sí.
3. Chatear con el primer asistente y recibir respuestas con citas
   correctas a sus documentos.
4. Cambiar al segundo asistente, hacer la misma pregunta temática del
   primero, y verificar que responde "no tengo información" (aislamiento).
5. Cerrar el navegador, volver a abrir, seleccionar la conversación del
   primer asistente y continuar donde se dejó.
6. Ver las citas como bloques expandibles con nombre de documento, página
   (si aplica) y fragmento relevante.

## Audiencia del proyecto

**Primaria**: evaluador del curso. Busca que se cumpla el core del enunciado
con calidad técnica y documentación clara.

**Secundaria**: reclutadores de posiciones de AI Engineer que revisen el
repo en el futuro. Buscan señales de criterio técnico (decisiones
justificadas, testing mínimo, arquitectura limpia, commits coherentes).

No se optimiza para ninguna audiencia comercial en esta iteración.
