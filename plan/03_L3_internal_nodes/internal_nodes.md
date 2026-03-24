# L3: Internal Nodes

> Contenido de los nodos. Componentes agnósticos al grafo - funcionarían en tablas o modales.

---

## Componentes

| Componente | contentType | Descripción |
|-----------|-------------|-------------|
| `InternalNodeRouter` | — | Switch que renderiza según contentType |
| `IntelligentEditor` | markdown, tags | Editor de texto con tags |
| `JsonPreview` | json | Visor de JSON highlighteado |
| `PropertyList` | property_list | Lista key-value |
| `ImagePreview` | image | Visor de imágenes |
| `CodeBlock` | code | Bloque de código |
| `EmptyNode` | empty | Placeholder para grupos |

---

## Responsabilidades

- **Renderizar contenido** - Según contentType del payload
- **Edición local** - onChange, validación interna
- **Interacción usuario** - Hover, click, focus
- **Emitir eventos** - onContentMutate cuando cambia
- **NO conoce grafo** - No sabe su posición, nodos vecinos, o padre

---

## Contrato L2 → L3

```typescript
interface L2ToL3Props {
  nodeId: string;
  isFocused: boolean;
  payload: NodePayload;
}

type NodePayload =
  | { contentType: 'markdown'; content: string }
  | { contentType: 'tags'; tags: TagItem[] }
  | { contentType: 'json'; data: JsonValue }
  | { contentType: 'property_list'; properties: Record<string, string> }
  | { contentType: 'image'; src: string }
  | { contentType: 'empty'; };
```

---

## Contrato L3 → L2

```typescript
interface L3ToL2Events {
  onContentMutate: (nodeId: string, newPayload: any) => void;
  onRequestFocus: (nodeId: string) => void;
}
```

---

## InternalNodeRouter

```tsx
export function InternalNodeRouter({ payload, nodeId }) {
  switch (payload.contentType) {
    case 'markdown':
      return <IntelligentEditor content={payload.content} />;
    case 'tags':
      return <TagEditor tags={payload.tags} />;
    case 'json':
      return <JsonPreview data={payload.data} />;
    case 'property_list':
      return <PropertyList properties={payload.properties} />;
    case 'empty':
    default:
      return <EmptyNode />;
  }
}
```

---

## Modos de IntelligentEditor

| Modo | Usado en | Comportamiento |
|------|----------|----------------|
| `fold` | A2 Data Explorer | Solo lectura, sin tags |
| `tag-hover` | B2 Extract | Tags hoverable, click pinnea |
| `diff` | B4 Generate Docs | Comparación versión old/new |

---

## Dependencias

- Foundation atoms - Tag, Badge, Icon
- NO ReactFlow - No sabe que vive en un grafo
- Podría usarse en SplitPane, Modal, Table indistintamente
