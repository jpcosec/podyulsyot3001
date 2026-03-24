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

---

## Nivel 1: UI / APP (El Orquestador)

> Gobierna la pantalla completa. Su trabajo es cargar los datos, leer el esquema de dominio y decidir qué vista se muestra.

### Responsabilidades
- Navegación global (Sidebars, Breadcrumbs, Tabs)
- Obtención de datos (API / Neo4j / Mock local)
- Filtrado de negocio (ej. "Mostrar solo skills técnicos")
- Inyectar datos limpios al Nivel 2

### Componentes Típicos
- `AppShell.tsx`, `JobWorkspaceShell.tsx`
- `MatchControlPanel.tsx`, `EvidenceBankPanel.tsx`
- Páginas orquestadoras (`Match.tsx`, `BaseCvEditor.tsx`)

### Documentación Relacionada
- `04_external_data_and_schema_integration.md` - Integración con APIs y esquemas
- `04a_document_explorer.md` - Explorador de documentos
- `05_validation_and_test_impact_map.md` - Validación y testing

---

## Nivel 2: Graph Viewer (El Motor Espacial)

> Es el lienzo de dibujo. Trata a los nodos como "cajas negras". Solo sabe de coordenadas espaciales, conexiones topológicas y eventos.

### Responsabilidades
- Renderizar `<ReactFlow>` puro
- Dibujar los cascarones de los nodos (bordes, colores, handles)
- Dibujar las aristas (curvas de Bezier, ProxyEdges)
- Ejecutar el motor de Layout matemático (Dagre/ELK)
- Emitir eventos de clic hacia el Nivel 1

### Componentes Típicos
- `<UniversalGraphCanvas>` (refactorizado desde `KnowledgeGraph.tsx`)
- `<UniversalNodeShell>` y `<UniversalGroupShell>`
- `<UniversalEdge>` y `<ProxyEdge>`

### Documentación Relacionada
- `01_graph_foundations.md` - Fundamentos del grafo
- `01a_layout_and_view_presets.md` - Presets de layout
- `01b_node_type_registry_and_modes.md` - Registro de tipos de nodo
- `01c_editor_state_and_history_contract.md` - Estado y historial
- `02_structured_documents_and_subflows.md` - Documentos estructurados
- `02a_tree_mode_and_outline_sync.md` - Modo árbol

---

## Nivel 3: Internal Representation (La "Carne")

> Componentes que viven dentro del nodo. Son agnósticos al grafo; funcionarían en una tabla o modal.

### Responsabilidades
- Mostrar datos enriquecidos o interactivos
- Renderizar vistas colapsables internas
- Manejar estados de edición locales

### Componentes Típicos
- `<IntelligentEditor mode="tag-hover">`
- `<JsonPreview>`, `<MarkdownPreview>`, `<ImagePreview>`
- Filas de atributos y `<RequirementItem>`

### Documentación Relacionada
- `03_rich_content_nodes.md` - Nodos de contenido rico
- `03a_text_annotation_links.md` - Anotaciones de texto
- `03b_markdown_formatted_editor.md` - Editor Markdown
- `03c_json_yaml_views.md` - Vistas JSON/YAML
- `03d_table_editor.md` - Editor de tablas
- `03e_code_display_and_annotation.md` - Código
- `03f_image_annotation.md` - Imágenes

---

## Contratos entre Capas

### Contrato A: L1 → L2 (App → Graph Canvas)

```typescript
interface AppToCanvasProps {
  // Datos
  astNodes: ASTNode[];       // Nodos genéricos
  astEdges: ASTEdge[];       // Conexiones topológicas
  
  // Settings
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

Ver documento completo: `06_flow_contract.md`

---

## Mapa de Documentación por Nivel

```
plan/
├── 00_status_matrix.md           # Estado general
│
├── # === NIVEL 2: Graph Viewer ===
├── 01_graph_foundations.md
├── 01a_layout_and_view_presets.md
├── 01b_node_type_registry_and_modes.md
├── 01c_editor_state_and_history_contract.md
├── 02_structured_documents_and_subflows.md
├── 02a_tree_mode_and_outline_sync.md
│
├── # === NIVEL 3: Internal Node ===
├── 03_rich_content_nodes.md
├── 03a_text_annotation_links.md
├── 03b_markdown_formatted_editor.md
├── 03c_json_yaml_views.md
├── 03d_table_editor.md
├── 03e_code_display_and_annotation.md
├── 03f_image_annotation.md
│
├── # === NIVEL 1: UI / APP ===
├── 04_external_data_and_schema_integration.md
├── 04a_document_explorer.md
│
├── # === Cross-cutting ===
├── 05_validation_and_test_impact_map.md
│
├── # === Meta ===
├── 06_ui_graph_architecture_layers.md
├── 06_flow_contract.md
│
└── AGENT_REVIEWER_ENTRYPOINT.md
```

---

## Orden de Implementación Recomendado

1. **L2 (Graph Viewer)** - Primero porque es el núcleo
   - `01_graph_foundations.md`
   - `01a_layout_and_view_presets.md`
   - `01b_node_type_registry_and_modes.md`

2. **L3 (Internal Node)** - Segundo, una vez estable L2
   - `03_rich_content_nodes.md`
   - `03b_markdown_formatted_editor.md`
   - `03c_json_yaml_views.md`

3. **L1 (UI / APP)** - Tercero, para integrar L2+L3
   - `04_external_data_and_schema_integration.md`
   - `04a_document_explorer.md`

4. **Validación** - Final
   - `05_validation_and_test_impact_map.md`

---

## Referencias

- Documento base: `06_ui_graph_architecture_layers.md`
- Contratos completos: `06_flow_contract.md`
- Estado actual: `00_status_matrix.md`
