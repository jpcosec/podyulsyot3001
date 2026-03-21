
LangChain Fase 1: Wrappers y Structured Output
Objetivo
Resolver la perdida de calidad en la extraccion y el drift de los esquemas reemplazando el runtime in-house por abstracciones de LangChain, manteniendo la orquestacion determinista intacta.

Alcance Estricto
Reemplazo del LLMRuntime:

Deprecar el wrapper custom de Gemini.

Implementar ChatGoogleGenerativeAI de langchain-google-genai.

Reemplazar la validacion custom por .with_structured_output(Schema). Esto delega el manejo de reintentos y parseo JSON al framework.

Integracion de LangSmith (Observabilidad):

Enchufar LangSmith para tener trazas exactas de que entra y que sale de los prompts de extraccion. Sin esto, depurar alucinaciones es dar palos de ciego.

Preservar la Disciplina Actual:

NO se toca src/graph.py (LangGraph sigue siendo el orquestador maestro).

NO se cambian los archivos de prompt locales (system.md, user_template.md). Se cargan y se wrappean en ChatPromptTemplate.

Eliminacion del offset LLM (TextSpan real):

Eliminar el intento de que el LLM adivine el start_offset / end_offset.

El LLM solo debe devolver el exact_quote (string). La UI o el backend calcularan la posicion determinista real para RecogitoJS usando busqueda de texto.

Criterio de Exito
El nodo extract_understand produce JSONs estables y validos el 99% de las veces, capturando la info critica sin que LangGraph pierda su comportamiento de fail-closed.
