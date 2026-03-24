1. Mapa de Responsabilidades por Nivel
Nivel 1: app (El Orquestador y Sistema)
Es el cerebro del negocio y de la aplicación. Gobierna el entorno, pero no sabe cómo dibujar un grafo.

Read / Write: Habla con la base de datos (Neo4j, SQL) o API. Lee y escribe en disco.

Appflow & Layout: Maneja la navegación global (rutas, pestañas de pipeline, paneles laterales, sidebars).

Settings: Gestiona el estado global (modo oscuro, permisos de solo lectura, filtros de negocio).

Schema Parsing: Toma los datos crudos y el esquema (match.schema.json) y compila la representación SuperMermaid (AST). Traduce el dominio (CV/Job) a topología abstracta.

Serialización: Cuando se guarda, toma el AST modificado y lo "des-parsea" de vuelta al formato de base de datos.

Nivel 2: graphCanvas (El Motor Espacial)
Es el lienzo interactivo. Gobierna la física y la topología, pero no sabe qué significan los datos que muestra.

Renderización: Implementa <ReactFlow>, los controles de zoom, el minimapa y dibuja las cajas y flechas.

Layout: Aplica matemáticas (Dagre/ELK) para calcular las coordenadas X/Y de cada caja para que no colisionen.

Interacción Espacial: Maneja el drag & drop de nodos, el paneo (panning) y la selección espacial múltiple.

Modificación del Grafo (Topología): Maneja la creación y destrucción de aristas (conectar A con B).

Relations & Subflows: Gestiona la herencia, los grupos anidados (cajas dentro de cajas) y el colapso visual (creando ProxyEdges cuando un grupo se cierra).

Nivel 3: node (La Carne y la Interfaz Interna)
Es el componente de contenido. Gobierna la interfaz de usuario específica, pero no sabe que vive en un grafo.

Representación de Dato: Renderiza editores Markdown, bloques de código, previsualizaciones JSON o imágenes (<IntelligentEditor>).

Modificación de Dato: Maneja el estado volátil local (ej. el estado onChange mientras el usuario teclea en un input).

Micro-interacciones: Abre tooltips locales, expande acordeones de texto, maneja validaciones de formulario internas.

2. Los Contratos de Información (Lo que baja y lo que sube)
Para que el sistema sea a prueba de balas, la comunicación fluye estrictamente a un paso de distancia. app no habla con node; todo pasa a través del embudo de graphCanvas.

Contrato A: Entre app y graphCanvas
⬇️ Lo que BAJA (Data & Props): El AST / SuperMermaid
La app inyecta la topología abstracta al canvas.

TypeScript
interface AppToCanvasProps {
  // Datos
  astNodes: ASTNode[];       // Nodos genéricos (id, tipo visual, payload)
  astEdges: ASTEdge[];       // Conexiones topológicas
  
  // Settings
  themeTokens: Record<string, StyleToken>; // Colores y formas agnósticas
  isReadOnly: boolean;
  layoutEngine: 'dagre' | 'manual';
}
⬆️ Lo que SUBE (Eventos & Callbacks): Intenciones Topológicas
El graphCanvas avisa a la app que el usuario interactuó o alteró la estructura.

TypeScript
interface CanvasToAppEvents {
  onSelectionChange: (nodeIds: string[], edgeIds: string[]) => void; // Para que app actualice el Sidebar
  onTopologyMutate: (newAST: AST) => void; // El usuario conectó/borró algo, se actualiza el SuperMermaid
  onRequestSave: (finalAST: AST) => void;  // El usuario presionó Ctrl+S en el canvas
}
Contrato B: Entre graphCanvas y node
⬇️ Lo que BAJA (Data & Props): El Payload
El graphCanvas recorta el AST y le pasa al node únicamente la carne que le corresponde, inyectándola en un cascarón (NodeShell).

TypeScript
interface CanvasToNodeProps {
  nodeId: string;
  isFocused: boolean;        // Para que el nodo sepa si debe resaltar su UI
  payload: Record<string, any>; // La data cruda: texto markdown, JSON, etc.
  contentType: 'markdown' | 'tag-editor' | 'image'; // Le dice qué componente interno montar
}
⬆️ Lo que SUBE (Eventos & Callbacks): Mutación de Contenido
El node no altera el layout ni guarda en disco. Solo avisa que su "carne" cambió o pide favores de cámara.

TypeScript
interface NodeToCanvasEvents {
  onContentMutate: (nodeId: string, newPayload: any) => void; // El usuario terminó de escribir. Canvas actualiza el AST.
  onRequestCameraFocus: (nodeId: string) => void; // Un botón interno pide hacer zoom a sí mismo.
  onRequestSubflowToggle: (nodeId: string) => void; // El usuario pide expandir/colapsar este contenedor.
}
Resumen del Ciclo de Vida (Ejemplo: Editar un Skill)
app lee Neo4j, parsea el esquema y pasa el SuperMermaid (AST) hacia abajo.

graphCanvas recibe el AST, calcula coordenadas, renderiza 50 cascarones, y le inyecta a uno de ellos el payload { skill: "React" }.

node recibe el payload, renderiza un <input>. El usuario borra "React" y escribe "Vue".

node dispara hacia arriba: onContentMutate(id, { skill: "Vue" }).

graphCanvas recibe el cambio, lo mete en su useGraphHistory() (Undo/Redo), actualiza su copia del AST y dispara hacia arriba: onTopologyMutate(nuevoAST).

app recibe el AST actualizado, activa el botón de "Guardar" en la UI.

El usuario hace clic en Guardar, app toma el AST, lo convierte a Cypher (Neo4j) y lo envía al backend (api/client.ts).

Con esta separación y estos contratos en TypeScript, el equipo (y nosotros al refactorizar) tiene un límite clarísimo. Si un componente importa algo que pertenece al contrato de otra capa, sabemos que hay que extraerlo.
