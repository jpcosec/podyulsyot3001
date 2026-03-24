# Schema & AST Translation Engine

> Goal: Definir el motor de traducción (`schemaToGraph`) y el lenguaje intermedio (AST / SuperMermaid) que permite al `<UniversalGraphCanvas>` renderizar cualquier tipo de estructura de datos sin conocer la lógica de negocio subyacente.

---

## 1. ¿Cómo funciona el Traductor?

El traductor es una función pura que vive en el Nivel 1 (App/Orquestador):

```
AST = schemaToGraph(RawData, Schema)
```

El proceso de traducción ocurre en 3 fases estrictas:

1. **Node Matching (Identidad):** Recorre el `RawData` y aplica las `match_rule` del Schema.
2. **Topology Resolution (Espacio):** Lee las reglas `render_as` ("node" o "group") y anida los nodos usando `parent_id`.
3. **Edge Resolution (Conexiones):** Busca arrays o referencias y genera los `ASTEdge`.

---

## 2. El Pipeline: Raw Data → Schema → AST

### Fase 1: Datos Crudos (Raw Data)

```json
{
  "jerarquia_vehiculos": {
    "nivel": 1,
    "tipo_nodo": "Vehículos",
    "contiene": [
      {
        "nivel": 2,
        "tipo_nodo": "Aéreos",
        "contiene": [
          {
            "nivel": 3,
            "tipo_nodo": "Helicópteros",
            "atributos": { "modelo": "Rescate" },
            "conexiones_externas": ["ext_motor"]
          }
        ]
      }
    ]
  }
}
```

### Fase 2: El Contrato (Schema D1)

```json
{
  "node_types": [
    {
      "match_rule": { "property": "nivel", "value": 1 },
      "type_name": "CategoriaRaiz",
      "render_as": "group",
      "color_token": "token_grupo_raiz"
    },
    {
      "match_rule": { "property": "nivel", "value": 3 },
      "type_name": "ModeloVehiculo",
      "render_as": "node",
      "color_token": "token_nodo_vehiculo"
    }
  ],
  "edge_types": [
    {
      "relation": "usa_componente",
      "source": "ModeloVehiculo",
      "target_array": "conexiones_externas",
      "color_token": "token_edge_dependencia"
    }
  ]
}
```

### Fase 3: El AST (Lo que recibe el Canvas)

```json
{
  "ast_nodes": [
    {
      "id": "node_vehiculos_raiz",
      "visual_token": "token_grupo_raiz",
      "node_behavior": { "is_subflow": true },
      "payload": { "title": "Vehículos" }
    },
    {
      "id": "node_helicopteros",
      "parent_id": "node_aereos",
      "visual_token": "token_nodo_vehiculo",
      "payload": { "title": "Helicópteros" },
      "attributes": { "modelo": "Rescate" }
    }
  ],
  "ast_edges": [
    {
      "id": "edge_heli_to_motor",
      "source": "node_helicopteros",
      "target": "ext_motor",
      "visual_token": "token_edge_dependencia"
    }
  ]
}
```

---

## 3. Por qué este AST protege la arquitectura

| Característica | Protección |
|----------------|------------|
| `parent_id` | Subflujos automáticos sin calcular X/Y |
| `visual_token` | Colores agnósticos al dominio |
| `attributes` | Datos de dominio empuja al panel lateral |
| `payload` | Contenido opaco para el Canvas |

El Canvas solo ve topología, no conoce "Vehículos" ni "Motor".

---

## Docs Relacionados

- `L2_graph_viewer/graph_foundations.md` - Fundamentos del grafo
- `L1_ui_app/schema_integration.md` - Integración con APIs
- `_meta/flow_contract.md` - Contratos entre capas
