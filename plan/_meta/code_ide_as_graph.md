# Code IDE: El Editor de Código como Grafo

> Usar el Node Editor para visualizar y editar el código fuente de la aplicación misma.

---

## La Visión

Construir un IDE visual estilo "Unreal Engine Blueprints" pero para código React:
- **Visualizar** dependencias entre archivos como flechas
- **Colapsar** carpetas como grupos
- **Editar** código haciendo doble clic en nodos
- **Guardar** directamente al disco

---

## Mapeo a las 3 Capas

| Capa | Rol en Code IDE | Ejemplo |
|------|-----------------|---------|
| **L1** | File System + AST Parser | Lee archivos, guarda cambios |
| **L2** | Architecture Viewer | Dibuja grafo de dependencias |
| **L3** | File Editor (Monaco/CodeMirror) | Edita .tsx, .json, etc. |

---

## Nivel 1: App (El IDE / Workspace)

**Responsabilidades:**
- Leer el File System (`fs.readFile`)
- Parsear código a AST (TypeScript compiler API)
- Guardar cambios (`fs.writeFile`)
- Rutas de archivos → posiciones en el grafo

**Schema:** `source_code.schema.json`

```json
{
  "node_types": [
    { "match_rule": { "property": "type", "value": "directory" },
      "type_name": "Folder", "render_as": "group" },
    { "match_rule": { "property": "extension", "value": ".tsx" },
      "type_name": "ReactComponent", "render_as": "node" },
    { "match_rule": { "property": "extension", "value": ".ts" },
      "type_name": "TypeScriptLogic", "render_as": "node" }
  ],
  "edge_types": [
    { "relation": "import", "target_array": "imports" }
  ]
}
```

---

## Nivel 2: Graph Canvas (Architecture Viewer)

**Responsabilidades:**
- Renderizar carpeta como **Grupo** (collapsible)
- Renderizar archivo como **Nodo**
- Dibujar **aristas** basadas en imports
- Posiciones X/Y basadas en estructura de carpetas

---

## Nivel 3: Internal Node (File Editor)

**Responsabilidades:**
- Renderizar editor según extensión:
  - `.tsx` → Monaco Editor (syntax highlighting)
  - `.json` → Form visual o editor
  - `.md` → Preview
- Emitir `onContentMutate` al editar
- Capturar Ctrl+S → `onRequestSave`

---

## El Flujo de Edición

```
Usuario edita código en nodo (L3)
        ↓
onContentMutate(newCode) → Canvas actualiza AST (L2)
        ↓
Ctrl+S → onRequestSave(AST)
        ↓
L1 busca archivo por path → fs.writeFile()
```

---

## Ejemplo: Visualizar `features/job-pipeline/`

```
┌─ features/job-pipeline (grupo) ─────────────────┐
│  ┌─ Match.tsx ────────┐    ┌─ schemaToGraph.ts┐
│  │ imports ────────►───│───►│                  │
│  └────────────────────┘    └───────────────────┘
└─────────────────────────────────────────────────┘
        ↓ (doble clic)
┌─ Monaco Editor嵌入 ────────────────────────────┐
│ export function MatchPage() { ... }           │
└───────────────────────────────────────────────┘
```

---

## Beneficios

- **Visualizar arquitectura** de un vistazo
- **Entender dependencias** entre módulos
- **Editar código** sin salir del grafo
- **Mismo canvas** que para Jobs/CVs

---

## Docs Relacionados

- `ARCHITECTURE.md` - Modelo de 3 capas
- `_meta/implementation_example.md` - Ejemplo de implementación
- `L2_graph_viewer/graph_foundations.md` - Fundamentos del grafo
