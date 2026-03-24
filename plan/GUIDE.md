# Guía de Navegación

> Cómo leer esta documentación sin perder tiempo.

---

## Regla #1: No leas todo

Esta carpeta tiene ~25 documentos. No necesitas la mayoría. Usa esta guía para ir directo a lo que necesitas.

---

## Puntos de entrada según tu objetivo

### "Quiero entender la arquitectura"

1. **`ARCHITECTURE.md`** — El modelo de 3 capas (L1/L2/L3), los contratos TypeScript, y la regla Data Down / Events Up. Es el documento más importante.

### "Quiero implementar algo"

1. `ARCHITECTURE.md` → identifica en qué capa vive tu feature
2. Ve al doc específico en `01_L1_ui_app/`, `02_L2_graph_viewer/`, o `03_L3_internal_nodes/`
3. `_meta/implementation_example.md` → código real de las 3 capas trabajando juntas

### "Quiero refactorizar KnowledgeGraph.tsx"

→ `_meta/refactor_knowledgegraph.md` — Migración paso a paso del God Component a 3 archivos.

### "Quiero entender los contratos entre capas"

→ `_meta/06_flow_contract.md` — Contrato A (L1→L2) y Contrato B (L2→L3), con el ciclo de vida completo de una edición.

### "Quiero usar un agente para revisar el plan"

→ `_meta/AGENT_REVIEWER_ENTRYPOINT.md` — Prompt de entrada + preguntas de revisión + formato de output.

### "Quiero entender la visión a futuro"

→ `_meta/code_ide_as_graph.md` — El editor como IDE visual estilo Blueprints.
→ `_meta/meta_ui_as_graph.md` — Representar la UI misma como grafo (documentación, no runtime).

---

## Mapa de dependencias entre docs

```
ARCHITECTURE.md (modelo mental)
    │
    ├── _meta/06_flow_contract.md (contratos formales)
    ├── _meta/implementation_example.md (código concreto)
    │
    ├── 01_L1_ui_app/
    │     └── schema_translation.md ← Motor schemaToGraph()
    │         (depende de: flow_contract)
    │
    ├── 02_L2_graph_viewer/
    │     └── graph_foundations.md ← Estado canónico del editor
    │         (habilita: layout_presets, node_types, state_history)
    │
    └── 03_L3_internal_nodes/
          └── rich_content_nodes.md ← Contrato de nodos ricos
              (habilita: markdown, json, table, code, image editors)
```

Cada doc L2/L3 tiene secciones `Depends On` y `Enables` — úsalas para saber qué leer antes.

---

## Carpetas

| Carpeta | Qué contiene | Cuándo la necesitas |
|---------|-------------|---------------------|
| `01_L1_ui_app/` | Schema engine, integración API, explorer, testing | Implementar fetching, traducción a AST, o páginas orquestadoras |
| `02_L2_graph_viewer/` | Canvas, layout, tipos de nodo, subflows, historial | Implementar ReactFlow, posicionamiento, interacción espacial |
| `03_L3_internal_nodes/` | Editores ricos: markdown, JSON, tablas, código, imágenes | Implementar contenido dentro de los nodos |
| `_meta/` | Contratos, arquitectura visual, refactor, ejemplos | Entender el diseño global o iniciar refactorizaciones |
| `_legacy/` | Status matrix original y review de diseño pre-reorganización | Solo referencia histórica — decisiones ya incorporadas en los docs actuales |

---

## Status de implementación por área

Derivado de `_legacy/00_status_matrix.md` y los docs individuales:

| Área | Status |
|------|--------|
| Graph canvas + interacción | **Parcial** — existe en sandbox |
| Layout/posicionamiento | **Parcial** — sin presets ni motor compartido |
| Tipos de nodo + registry | **Parcial** — custom nodes sin registro formal |
| Rich content nodes | **Missing** — sin contrato unificado |
| Markdown editor | **Parcial** — solo textarea |
| JSON/YAML, Tablas, Código, Imágenes | **Missing** |
| Schema-driven rendering | **Parcial** — concepto definido, sin implementación |
| Subflows / documentos anidados | **Parcial** — solo en CV graph |
| Persistencia | **Fragmentada** — sandbox local vs CV API |

---

## Decisiones de diseño clave

Documentadas en `_legacy/2026-03-20-ui-plan-review-design.md`:

- **elkjs desde el inicio** (no dagre)
- **Library-first** — React Flow, elkjs, zustand, FlexLayout, RJSF directamente, sin wrappers especulativos
- **Representation Schema** — YAML/JSON por proyecto que mapea estructura a comportamiento visual
- **CSS theming** — Obsidian-style con `data-*` attributes, tokens MD3
- **Extension model** — `registry.register()` para todo tipo de extensión
