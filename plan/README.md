# Node Editor Plan

> **START HERE:** Lee primero `ARCHITECTURE.md` para entender el modelo de 3 capas.

---

## Estructura

| Nivel | Descripción | Carpeta |
|-------|-------------|---------|
| **L1** | UI / App (Orquestación) | `L1_ui_app/` |
| **L2** | Graph Viewer (Motor Espacial) | `L2_graph_viewer/` |
| **L3** | Internal Node (Contenido Rico) | `L3_internal_nodes/` |

Ver `ARCHITECTURE.md` para detalles completos.

---

## Quick Links

- [Arquitectura](./ARCHITECTURE.md)
- [Contratos](./_meta/flow_contract.md)
- [Legacy](./_legacy/)

---

## Carpetas

```
plan/
├── L2_graph_viewer/      # ReactFlow, layout, topología
├── L3_internal_nodes/    # Editores, previews, formularios
├── L1_ui_app/           # API, navegación, integración
├── _meta/               # Contratos y arquitectura
└── _legacy/             # Referencia
```
