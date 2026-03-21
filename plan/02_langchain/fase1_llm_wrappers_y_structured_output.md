# LangChain Fase 1: Wrappers y Structured Output

## Objetivo

Resolver la perdida de calidad en extraccion y el drift de esquemas reemplazando el runtime in-house por abstracciones de LangChain, manteniendo la orquestacion determinista intacta.

## Alcance estricto

### 1. Reemplazo del `LLMRuntime`

- Deprecar el wrapper custom actual de Gemini.
- Implementar `ChatGoogleGenerativeAI` desde `langchain-google-genai`.
- Reemplazar la validacion/parsing custom por `.with_structured_output(Schema)` donde tenga sentido.

### 2. Integracion de LangSmith

- Activar trazas exactas de inputs, prompts y outputs.
- Usar esa observabilidad para depurar alucinaciones, campos perdidos y drift de esquema.

### 3. Preservar la disciplina actual

- **NO** tocar `src/graph.py` como parte de esta fase.
- **NO** cambiar el papel de LangGraph como orquestador.
- **NO** reescribir el sistema de prompts locales (`system.md`, `user_template.md`).
- Los prompts actuales deben cargarse y envolverse con `ChatPromptTemplate` o un adaptador equivalente.

### 4. Eliminar offsets inventados por el LLM

- El modelo no debe intentar adivinar `start_offset` ni `end_offset`.
- El LLM devuelve `exact_quote` y el backend/UI calcula offsets reales de forma determinista por busqueda de texto.

## Donde aplicar primero

1. `extract_understand`
2. `match`

No extender esto a todo el pipeline hasta demostrar estabilidad en esos dos nodos.

## Restricciones no negociables

1. LangGraph sigue intacto como capa de orquestacion.
2. La semantica fail-closed no se negocia.
3. Los contratos de artefactos no se rompen.
4. El flujo `--resume` debe seguir funcionando igual.

## Implementacion minima esperada

1. Adaptador LangChain para cargar prompts actuales.
2. Structured output con esquemas existentes o sus sucesores inmediatos.
3. Mapeo claro de excepciones hacia la taxonomia actual de errores.
4. Trazas observables para comparar runtime viejo vs nuevo.

## Criterio de exito

`extract_understand` produce JSONs estables y validos la gran mayoria de las veces, capturando informacion critica como contacto, salario e instituto sin romper el comportamiento determinista del grafo.

Si esta fase sale bien, LangChain queda como wrapper util. Si no, no se justifica una reescritura mayor.
