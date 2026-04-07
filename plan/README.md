# Node Editor Plan

> **STATUS: Implementation Complete** — All GRP and UI steps completed as of 2026-04-08.

---

## Completed Implementation

All 22 implementation steps (GRP-001-00 through UI-001-11) are complete. See `steps/README.md` for the full status.

```
src/features/graph-editor/
├── L1-app/                  # GraphEditorPage: schema loading + orchestration
├── L2-canvas/               # GraphCanvas, NodeShell, GroupShell, Sidebar, Panels
│   ├── edges/               # FloatingEdge, ButtonEdge
│   ├── sidebar/             # Actions, Filters, Creation, View sections
│   ├── panels/              # NodeInspector, EdgeInspector
│   └── hooks/               # Layout, edge inheritance, keyboard shortcuts
└── lib/                     # schemaToGraph, graphToDomain, data-provider
```

---

## Quick Links

- [Implementation Steps](./steps/README.md)
- [Implementation Order](./IMPLEMENTATION_ORDER.md)
- [Architecture](./ARCHITECTURE.md)
- [Architecture Pitfalls](./docs/node-editor/architecture_pitfalls.md)
- [Future Specs](./future/)
- [Legacy](./_legacy/)
plan/
├── L2_graph_viewer/      # ReactFlow, layout, topología
├── L3_internal_nodes/    # Editores, previews, formularios
├── L1_ui_app/           # API, navegación, integración
├── _meta/               # Contratos y arquitectura
└── _legacy/             # Referencia
```
