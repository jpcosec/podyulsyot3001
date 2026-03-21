
UI Fase 1: Minimal JSON Editor (NodeEditor)
Objetivo
Conectar el NodeEditor actual directamente a los archivos JSON generados por el pipeline local. Retrasar la adopcion de Neo4j y bases de datos complejas hasta que el pipeline LLM sea 100% estable y el volumen de trabajos lo exija.

Alcance Estricto (Los 3 Hitos)
Revision del Knowledge-Tree (Extraccion):

Input: Cargar data/jobs//extract_understand/approved/state.json.

Accion UI: Visualizar nodos extraidos, permitir al usuario corregir errores o agregar nodos faltantes.

Output: Sobrescribir el mismo JSON al guardar.

Revision del Matching:

Input: Cargar data/jobs//match/approved/state.json.

Accion UI: Mostrar el grafo de Requirement -> Match -> Evidence. Permitir al usuario ajustar scores y justificaciones.

Output: Sobrescribir el JSON de match.

Revision de Redaccion (Documentos/Deltas):

Input: Cargar las propuestas de generate_documents/.

Accion UI: Mostrar la propuesta de delta sobre el CV promedio, permitir edicion del texto final.

Output: Guardar la version final del Markdown/JSON.

Reglas de Arquitectura
Cero Neo4j: La UI le habla a un backend FastAPI ligerisimo que solo hace Read File y Write File sobre la carpeta data/.

Esquema de Representacion: El frontend usa su esquema agnostico para pintar los nodos. No acoplar la UI a la forma exacta de los Pydantic models del backend.

Criterio de Exito
Poder revisar y corregir un trabajo completo (Extraccion -> Match -> CV) desde el navegador usando solo el sistema de archivos local como persistencia.
