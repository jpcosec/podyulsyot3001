# Node Editor Architecture

> **Modelo de 3 Capas** - La guía definitiva para entender y desarrollar el editor de grafos.

---

## Las 3 Capas (Resumen)

| Nivel | Nombre | Responsabilidad | Ejemplo |
|-------|--------|-----------------|---------|
| **L1** | **UI / APP** | Orquestación, navegación, fetching, lógica de dominio | `AppShell`, `Match.tsx`, fetching de Neo4j |
| **L2** | **Graph Viewer** | Renderizado ReactFlow, layout matemático, topología | `KnowledgeGraph`, `UniversalGraphCanvas` |
| **L3** | **Internal Node** | Contenido rico, editores, formularios | `IntelligentEditor`, `JsonPreview` |

**Regla de Oro:** Un nivel no puede saltarse a otro ni conocer la lógica del otro.

### El Contrato (Data Down, Events Up)

- **Data Down:** La información fluye de afuera hacia adentro.
  - L1 traduce datos crudos a **AST** y se lo pasa a L2
  - L2 extrae el **payload** y se lo pasa a L3
  
- **Events Up:** Las intenciones fluyen de adentro hacia afuera.
  - L3 emite `onContentMutate` (el usuario cambió contenido)
  - L2 atrapa el evento, actualiza el AST y dispara `onTopologyMutate`
  - L1 atrapa el nuevo AST y lo guarda en disco

---

## Nivel 1: UI / APP (El Orquestador)

> Gobierna la pantalla completa. Su trabajo es cargar los datos, leer el esquema de dominio y decidir qué vista se muestra.

### Responsabilidades
- Navegación global (Sidebars, Breadcrumbs, Tabs)
- Obtención de datos (API / Neo4j / Mock local)
- Filtrado de negocio (ej. "Mostrar solo skills técnicos")
- Inyectar datos limpios al Nivel 2

### Docs
- `L1_ui_app/schema_translation.md` - Motor de traducción Schema→AST
- `L1_ui_app/schema_integration.md` - Integración con APIs
- `L1_ui_app/document_explorer.md` - Explorador
- `L1_ui_app/validation_testing.md` - Testing

---

## Nivel 2: Graph Viewer (El Motor Espacial)

> Es el lienzo de dibujo. Trata a los nodos como "cajas negras". Solo sabe de coordenadas espaciales, conexiones topológicas y eventos.

### Responsabilidades
- Renderizar `<ReactFlow>` puro
- Dibujar los cascarones de los nodos (bordes, colores, handles)
- Dibujar las aristas (curvas de Bezier, ProxyEdges)
- Ejecutar el motor de Layout matemático (Dagre/ELK)
- Emitir eventos de clic hacia el Nivel 1

### Docs
- `L2_graph_viewer/graph_foundations.md`
- `L2_graph_viewer/layout_presets.md`
- `L2_graph_viewer/node_types.md`
- `L2_graph_viewer/state_history.md`
- `L2_graph_viewer/subflows.md`
- `L2_graph_viewer/tree_mode.md`

---

## Nivel 3: Internal Representation (La "Carne")

> Componentes que viven dentro del nodo. Son agnósticos al grafo; funcionarían en una tabla o modal.

### Responsabilidades
- Mostrar datos enriquecidos o interactivos
- Renderizar vistas colapsables internas
- Manejar estados de edición locales

### Docs
- `L3_internal_nodes/rich_content_nodes.md`
- `L3_internal_nodes/text_annotation.md`
- `L3_internal_nodes/markdown_editor.md`
- `L3_internal_nodes/json_yaml_views.md`
- `L3_internal_nodes/table_editor.md`
- `L3_internal_nodes/code_annotation.md`
- `L3_internal_nodes/image_annotation.md`

---

## Contratos entre Capas

### Contrato A: L1 → L2 (App → Graph Canvas)

```typescript
interface AppToCanvasProps {
  astNodes: ASTNode[];
  astEdges: ASTEdge[];
  themeTokens: Record<string, StyleToken>;
  isReadOnly: boolean;
  layoutEngine: 'dagre' | 'manual';
}

interface CanvasToAppEvents {
  onSelectionChange: (nodeIds: string[], edgeIds: string[]) => void;
  onTopologyMutate: (newAST: AST) => void;
  onRequestSave: (finalAST: AST) => void;
}
```

### Contrato B: L2 → L3 (Graph Canvas → Node)

```typescript
interface CanvasToNodeProps {
  nodeId: string;
  isFocused: boolean;
  payload: Record<string, any>;
  contentType: 'markdown' | 'tag-editor' | 'image';
}

interface NodeToCanvasEvents {
  onContentMutate: (nodeId: string, newPayload: any) => void;
  onRequestCameraFocus: (nodeId: string) => void;
  onRequestSubflowToggle: (nodeId: string) => void;
}
```

Ver: `_meta/flow_contract.md`

---

## Estructura de Archivos

```
plan/
├── README.md
├── GUIDE.md
├── ARCHITECTURE.md                    # Este archivo
│
├── 01_L1_ui_app/                     # Orquestación
│   ├── schema_translation.md
│   ├── schema_integration.md
│   ├── document_explorer.md
│   └── validation_testing.md
│
├── 02_L2_graph_viewer/               # Motor Espacial
│   ├── graph_foundations.md
│   ├── layout_presets.md
│   ├── node_types.md
│   ├── state_history.md
│   ├── subflows.md
│   └── tree_mode.md
│
├── 03_L3_internal_nodes/             # Contenido Rico
│   ├── rich_content_nodes.md
│   ├── text_annotation.md
│   ├── markdown_editor.md
│   ├── json_yaml_views.md
│   ├── table_editor.md
│   ├── code_annotation.md
│   └── image_annotation.md
│
├── _meta/                            # Arquitectura
│   ├── flow_contract.md
│   ├── ui_graph_architecture_layers.md
│   └── AGENT_REVIEWER_ENTRYPOINT.md
│
└── _legacy/                          # Referencia
    ├── 00_status_matrix.md
    └── 2026-03-20-ui-plan-review-design.md
```

---

## Orden de Implementación

1. **L2 (Graph Viewer)** - El núcleo
2. **L3 (Internal Node)** - Una vez L2 estable
3. **L1 (UI / APP)** - Para integrar todo

---

## Referencias

- `_meta/flow_contract.md` - Contratos completos
- `_meta/ui_graph_architecture_layers.md` - Capas visuales
