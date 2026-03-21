# UI Fase 1: Minimal JSON Editor (NodeEditor)

## Objetivo

Conectar el `NodeEditor` actual directamente a los archivos JSON generados por el pipeline local. Retrasar la adopcion de Neo4j y bases de datos mas complejas hasta que el pipeline LLM sea estable y el volumen de trabajos realmente lo exija.

## Alcance estricto

### 1. Revision del knowledge tree de extraccion

- **Input:** `data/jobs/<source>/<job_id>/nodes/extract_understand/approved/state.json`
- **Accion UI:** visualizar nodos extraidos, permitir correcciones y agregar nodos faltantes.
- **Output:** guardar una version editada/aprobada del mismo estado de extraccion dentro del flujo local basado en archivos.

### 2. Revision del matching

- **Input:** `data/jobs/<source>/<job_id>/nodes/match/approved/state.json`
- **Accion UI:** mostrar el grafo `Requirement -> Match -> Evidence`, y permitir ajuste de scores, justificaciones y relaciones visibles para revision.
- **Output:** guardar el estado de matching corregido dentro del mismo flujo local de artefactos.

### 3. Revision de redaccion de documentos

- **Input:** artefactos de `data/jobs/<source>/<job_id>/nodes/generate_documents/`
- **Accion UI:** mostrar la propuesta de CV/carta/email o sus deltas y permitir edicion del texto final.
- **Output:** persistir la version final en Markdown/JSON dentro del workspace local del job.

## Reglas de arquitectura

- **Cero Neo4j:** la UI habla con un backend FastAPI ligero que solo hace read/write de archivos dentro de `data/`.
- **Frontend agnostico:** el frontend usa su propio esquema de representacion para pintar nodos y edges; no debe quedar acoplado uno a uno a la forma exacta de los modelos backend.
- **Persistencia explicita:** cargar, editar y guardar tienen que ser acciones claras; nada de magia ni sincronizacion implicita.
- **Sin reescritura del editor:** partir del `NodeEditor` y del sandbox actual, no reiniciar la UI desde cero.

## Reutilizar de la fase sandbox ya hecha

1. On-node editing.
2. Focus mode y `Hide non-neighbors`.
3. Layout determinista.
4. Creacion contextual de relaciones.
5. Save/discard workflow.

## Primer slice de implementacion

1. Endpoint FastAPI para leer el estado de extraccion de un job.
2. Adaptador frontend que convierta ese JSON al esquema del `NodeEditor`.
3. Guardado de vuelta al workspace local.
4. Repetir el mismo patron para matching.
5. Extender despues a `generate_documents`.

## Criterio de exito

Poder revisar y corregir un trabajo completo desde navegador usando solo el sistema de archivos local como persistencia:

1. extraccion
2. match
3. documentos/deltas

Si esto funciona bien, Neo4j deja de ser una dependencia para validar la UX real.
