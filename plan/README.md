# Node Editor Plan

> **START HERE:** Lee primero `ARCHITECTURE.md` para entender el modelo de 3 capas.

Este directorio contiene la planificación del editor de grafos como un grafo de dependencias, no como una lista plana.

---

## Estructura de Documentación

El sistema se organiza en **3 niveles de arquitectura**:

| Nivel | Descripción | Docs Clave |
|-------|-------------|------------|
| **L1** | UI / App (Orquestación) | `04_*.md`, `ARCHITECTURE.md` |
| **L2** | Graph Viewer (Motor Espacial) | `01_*.md`, `02_*.md` |
| **L3** | Internal Node (Contenido Rico) | `03_*.md` |

Ver `ARCHITECTURE.md` para el mapa completo y explicación detallada.

---

## Quick Links

- [Arquitectura Completa](./ARCHITECTURE.md)
- [Contratos entre Capas](./06_flow_contract.md)
- [Capas UI y Graph](./06_ui_graph_architecture_layers.md)
- [Estado Actual](./00_status_matrix.md)

---

## Dependencias entre Docs

```
00_status_matrix
    │
    ├─► 01_graph_foundations (L2)
    │       ├─► 01a_layout_and_view_presets
    │       ├─► 01b_node_type_registry_and_modes
    │       └─► 01c_editor_state_and_history_contract
    │
    ├─► 02_structured_documents_and_subflows (L2)
    │       └─► 02a_tree_mode_and_outline_sync
    │
    ├─► 03_rich_content_nodes (L3)
    │       ├─► 03a_text_annotation_links
    │       ├─► 03b_markdown_formatted_editor
    │       ├─► 03c_json_yaml_views
    │       ├─► 03d_table_editor
    │       ├─► 03e_code_display_and_annotation
    │       └─► 03f_image_annotation
    │
    └─► 04_external_data_and_schema_integration (L1)
            ├─► 04a_document_explorer
            └─► 05_validation_and_test_impact_map
```

---

## build Order

1. **L2 primero** - Graph Viewer (el núcleo del sistema)
2. **L3 segundo** - Internal Node (una vez L2 estable)
3. **L3tercero** - UI/App (para integrar todo)
4. **Validación** - Testing y validación

Ver `ARCHITECTURE.md` para detalles completos.
