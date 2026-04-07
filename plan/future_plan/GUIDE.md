# Guía de Navegación

> Cómo leer esta documentación sin perder tiempo.

---

## Regla #1: No leas todo

Esta carpeta tiene ~30 documentos. No necesitas la mayoría. Usa esta guía para ir directo a lo que necesitas.

---

## Puntos de entrada según tu objetivo

### "Quiero entender la arquitectura"

→ **`ARCHITECTURE.md`** — El modelo de 3 capas (L1/L2/L3), contratos TypeScript, Data Down / Events Up, stack tecnológico.

### "Quiero implementar el node editor"

1. **`_meta/blueprint_node_editor.md`** — El blueprint definitivo. Estructura de archivos, stores, registry, contratos, flujo de datos, hooks, CSS, migration mapping. **Empieza aquí.**
2. `ARCHITECTURE.md` → para entender en qué capa vive tu feature
3. `_meta/reactflow_patterns_catalog.md` → código copiable para cada patrón RF

### "Quiero saber qué patrones de ReactFlow usar"

→ **`_meta/reactflow_patterns_catalog.md`** — 20 patrones de los ejemplos oficiales, con código copiable, priorizados por fase.
→ **`_meta/reactflow_inventory.md`** — Qué usamos de RF nativo vs custom, qué nos falta, decisiones de stack.

### "Quiero ver los problemas y riesgos del diseño"

→ **`_meta/architecture_critique.md`** — 14 problemas identificados con prioridad y solución propuesta. Incluye: a11y, runtime validation, XSS, performance, contract testing, lazy loading.

### "Quiero refactorizar KnowledgeGraph.tsx"

→ **`_meta/blueprint_node_editor.md`** (sección "Migration mapping") — Cada sección del God Component (2,949 líneas) → archivo target.
→ **`_meta/session_reactflow_deep_dive.md`** — Decisiones tomadas durante la auditoría de código + ReactFlow.

### "Quiero entender los contratos entre capas"

→ `ARCHITECTURE.md` (sección "Contratos entre Capas") — Versión actualizada.
→ `_meta/06_flow_contract.md` — Versión original (legacy, referencia).

### "Quiero usar un agente para revisar el plan"

→ `_meta/AGENT_REVIEWER_ENTRYPOINT.md` — Prompt de entrada + preguntas de revisión + formato de output.

### "Quiero entender la visión a futuro"

→ `_meta/code_ide_as_graph.md` — El editor como IDE visual estilo Blueprints.
→ `_meta/meta_ui_as_graph.md` — Representar la UI misma como grafo (documentación, no runtime).

---

## Mapa de dependencias

```
ARCHITECTURE.md (modelo mental — L1/L2/L3, contratos, stack)
    │
    ├── _meta/blueprint_node_editor.md (implementación concreta — THE doc)
    │       │
    │       ├── _meta/reactflow_patterns_catalog.md (código copiable para cada feature)
    │       └── _meta/reactflow_inventory.md (qué delegar a RF, qué mantener custom)
    │
    ├── _meta/architecture_critique.md (problemas a resolver durante implementación)
    │
    ├── _meta/session_reactflow_deep_dive.md (contexto de decisiones)
    │
    ├── 01_L1_ui_app/
    │     └── schema_translation.md ← Motor schemaToGraph()
    │
    ├── 02_L2_graph_viewer/
    │     └── graph_foundations.md ← Estado canónico del editor
    │         (habilita: layout_presets, node_types, state_history, subflows)
    │
    └── 03_L3_internal_nodes/
          └── rich_content_nodes.md ← Contrato de nodos ricos
              (habilita: markdown, json, table, code, image editors)
```

---

## Carpetas

| Carpeta | Qué contiene | Cuándo la necesitas |
|---------|-------------|---------------------|
| `01_L1_ui_app/` | Schema engine, integración API, explorer, testing | Implementar fetching, traducción a AST, o páginas orquestadoras |
| `02_L2_graph_viewer/` | Canvas, layout, tipos de nodo, subflows, historial | Implementar ReactFlow, posicionamiento, interacción espacial |
| `03_L3_internal_nodes/` | Editores ricos: markdown, JSON, tablas, código, imágenes | Implementar contenido dentro de los nodos |
| `_meta/` | Blueprint, critique, patrones RF, inventario, contratos, sesiones | Entender el diseño global, tomar decisiones, o iniciar implementación |
| `_legacy/` | Status matrix original y review de diseño pre-reorganización | Solo referencia histórica |

---

## Stack decidido

| Herramienta | Para qué | Doc de referencia |
|-------------|----------|-------------------|
| ReactFlow | Canvas, interacción, viewport | `_meta/reactflow_inventory.md` |
| elkjs | Layout compound (subflows anidados) | `_meta/reactflow_inventory.md` |
| Zustand | State management (selectores atómicos) | `_meta/blueprint_node_editor.md` |
| Zod | Validación runtime de payloads | `_meta/blueprint_node_editor.md` |
| DOMPurify | Sanitización HTML (default deny) | `_meta/architecture_critique.md` |
| shadcn/ui | Sheet, Accordion, AlertDialog, ContextMenu | `_meta/reactflow_inventory.md` |
| xy-theme.css | Tema visual RF con `--xy-*` variables | `_meta/reactflow_inventory.md` |

---

## Decisiones de diseño clave

- **elkjs desde el día 1** (no dagre) — subflows anidados son requisito inmediato
- **Zustand con selectores atómicos** (no React Context) — evita re-renders innecesarios
- **Node Type Registry** — reemplaza CATEGORY_COLORS + NODE_TEMPLATES hardcoded
- **Edge Inheritance** (no ProxyEdge) — edges se reasignan visualmente al colapsar, no se crean/destruyen
- **Render tiers** — contextual zoom con 3 niveles para performance con muchos nodos
- **xy-theme.css** — separación tema visual / estilos de app (patrón oficial RF)
- **Library-first** — RF, elkjs, zustand, shadcn directamente, sin wrappers especulativos
