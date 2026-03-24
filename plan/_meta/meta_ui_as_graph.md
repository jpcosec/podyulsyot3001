# Meta-UI: La UI como Grafo

> Representar la interfaz misma como un grafo para visualizar y modificar su estructura en **código**, no en runtime.

---

## Propósito

Tener una representación formal de la estructura UI del Node Editor como grafo, para:
- **Visualizar** las regiones y componentes de la UI
- **Documentar** las dependencias entre partes
- **Analizar** el acoplamiento entre componentes
- **Modificar** la estructura via código (no runtime)

> ⚠️ **NO es un sistema de runtime.** Es documentación/visualización estática.

---

## Niveles de Abstracción

| Nivel | Descripción | Ejemplo |
|-------|-------------|---------|
| **View** | Contenedor principal | `NodeEditorView` |
| **Región** | Bloques de layout | Sidebar, Header, Graph |
| **Componente** | Elementos interactivos | Botones, nodos, editores |
| **Externo** | Estado global, schemas | Filtros, Schema, Config |

---

## Estructura JSON

```json
{
  "ui_view_definition": {
    "nodos_externos": {
      "estado_schema": {
        "tipo": "Datos",
        "valor": "schema_v2.json"
      },
      "estado_filtros": {
        "tipo": "Estado",
        "activos": ["Filtro A"]
      }
    },
    "jerarquia_ui": {
      "nivel": 1,
      "tipo_nodo": "View",
      "contiene": [
        {
          "nivel": 2,
          "tipo_nodo": "Lapp_",
          "id": "sidebar",
          "contiene": [
            { "nivel": 3, "tipo_nodo": "Action", "id": "add_node" }
          ]
        },
        {
          "nivel": 2,
          "tipo_nodo": "LGraph_",
          "id": "canvas",
          "conexiones_externas": ["estado_filtros", "estado_schema"],
          "contiene": [
            { "nivel": 3, "tipo_nodo": "Lcontent_", "subtipo": "nodo" }
          ]
        }
      ]
    }
  }
}
```

---

## Mapeo a Arquitectura

| Meta-Nivel | Arquitectura |
|------------|--------------|
| `Lapp_` (región estática) | **L1** - UI/App |
| `LGraph_` (canvas) | **L2** - Graph Viewer |
| `Lcontent_` (contenido) | **L3** - Internal Node |

---

## Docs Relacionados

- `ARCHITECTURE.md` - Modelo de 3 capas
- `_meta/flow_contract.md` - Contratos entre capas
