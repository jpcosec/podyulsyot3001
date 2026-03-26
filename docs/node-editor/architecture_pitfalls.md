# Architectural Pitfalls & Critical Patterns

> Documento de lecciones aprendidas durante la revisión arquitectónica del Node Editor.
> 
> **Objetivo:** Evitar que los errores corregidos se repitan en futuras implementaciones.

---

## Overview

Durante la revisión del plan de implementación (`steps/SPEC_GRP_001_*.md`), se detectaron **6 desviaciones críticas** que habrían roto la arquitectura, la sincronización de estado y el rendimiento. Este documento captura esas lecciones.

---

## Pitfall 1: Hardcoding de Dominio en el Registry

### Problema
El archivo `register-defaults.ts` contenía tipos de nodos quemados en el código (`person`, `skill`, `project`, etc.). Esto destruye la naturaleza agnóstica del editor.

### Impacto
- El editor solo funciona para un dominio específico (CVs)
- No se puede reutilizar para otros casos de uso (empleos, proyectos, etc.)
- Violación del principio de separación de responsabilidades

### Solución Correcta
L1 debe cargar el schema JSON dinámicamente y poblar el registry en runtime:

```tsx
// L1: GraphEditorPage.tsx
const { data: schema } = useQuery({ queryKey: ['schema'] });

useEffect(() => {
  schema.node_types.forEach(typeDef => {
    registry.register({
      typeId: typeDef.id,
      label: typeDef.display_name,
      colorToken: typeDef.visual.color_token,
      payloadSchema: buildZodSchema(typeDef.attributes),
      // ...
    });
  });
}, [schema]);

// Después: renderizar L2
return <GraphEditor />;
```

### Cuándo Usar register-defaults.ts
Solo para **testing local** o **SandboxPage**. Nunca en código de producción.

---

## Pitfall 2: Tipos de Payload Opacos

### Problema
`payload: Record<string, unknown>` fuerza casteos inseguros en toda la aplicación:

```ts
// ❌ Código inseguro en toda la app
const name = node.data.payload.name as string;
```

### Impacto
- Errores de tipo en runtime
- Código frágil ante cambios
- Sin autocompletado en IDE

### Solución Correcta
Usar **unión discriminada** basada en `typeId`:

```ts
// types.ts
export type NodePayload =
  | { typeId: 'person'; name: string; role?: string }
  | { typeId: 'skill'; name: string; level?: string }
  | { typeId: 'error'; message: string };

// Ahora TypeScript infiere el tipo correcto
const { payload } = node.data;
if (payload.typeId === 'person') {
  console.log(payload.name); // ✅ type-safe!
}
```

---

## Pitfall 3: Undo/Redo Envenenado por Acciones Visuales

### Problema
Colapsar/expandir grupos注入 eventos en el `undoStack` de Zustand:

```ts
// ❌ Estopollutes el historial semántico
collapseGroup(groupId);
undo(); // Restaura el grupo expandido - confuso!
```

### Impacto
- Historial de deshacer semanticamente incorrecto
- UX confusa para el usuario
- Operations no relacionadas mezcladas

### Solución Correcta
Parámetro `isVisualOnly` en las mutaciones del store:

```ts
// stores/graph-store.ts
updateNode: (nodeId, patch, options?: { isVisualOnly?: boolean }) => {
  if (options?.isVisualOnly) {
    // Solo actualizar estado, no hacer push al undoStack
    set(state => ({ nodes: ... }));
    return;
  }
  // Comportamiento normal: push al undoStack
};

// Hook: usar isVisualOnly
collapseGroup(groupId) {
  updateNode(child.id, { hidden: true }, { isVisualOnly: true });
}
```

---

## Pitfall 4: ELKjs en Main Thread

### Problema
`await elk.layout()` se ejecuta en el hilo principal de React:

```ts
// ❌ Bloquea la UI
const layoutedGraph = await elk.layout(graph);
```

### Impacto
- UI congelada por 1+ segundo con >50 nodos
- Animaciones entrecortadas
- Mala experiencia de usuario

### Solución Correcta
Mover ELK a un **Web Worker**:

```ts
// workers/elk.worker.ts
import ELK from 'elkjs/lib/elk.bundled.js';
const elk = new ELK();

self.onmessage = async (event) => {
  const layoutedGraph = await elk.layout(event.data.graph);
  self.postMessage({ type: 'result', payload: layoutedGraph });
};

// Hook
const layout = () => {
  return new Promise((resolve) => {
    worker.postMessage({ type: 'layout', payload: graph });
    worker.onmessage = (e) => resolve(e.data.payload);
  });
};
```

---

## Pitfall 5: Desincronización de Borrado

### Problema
No se manejan los eventos `onNodesDelete`/`onEdgesDelete` de ReactFlow:

```ts
// ❌ ReactFlow borra internamente, pero Zustand no se entera
<ReactFlow onNodesChange={handleChanges} />
```

### Impacto
- Estado de Zustand desincronizado con UI
- Errores al guardar (nodos "fantasma" en el store)
- Comportamiento errático

### Solución Correcta
Conectar los handlers de eliminación:

```tsx
<ReactFlow
  onNodesDelete={(deletedNodes) => {
    const nodeIds = deletedNodes.map(n => n.id);
    const edgeIds = edges
      .filter(e => nodeIds.includes(e.source) || nodeIds.includes(e.target))
      .map(e => e.id);
    removeElements(nodeIds, edgeIds);
  }}
  onEdgesDelete={(deletedEdges) => {
    removeElements([], deletedEdges.map(e => e.id));
  }}
/>
```

**Importante:** No implementar manejo manual de la tecla Delete en `useKeyboard`. ReactFlow ya lo hace internamente.

---

## Pitfall 6: Dependencia Circular (Registry → L3)

### Problema
`register-defaults.ts` importa `EntityCard` que no existe hasta el Paso 4:

```ts
// ❌ Error de build en Paso 3
import { EntityCard } from '@/components/content/EntityCard';
```

### Impacto
- Build falla si se sigue el plan paso a paso
- No se puede hacer commits incrementales
- Confusión en el equipo

### Solución Correcta
Usar **placeholders** en Paso 3, actualizar en Paso 4:

```ts
// Paso 3: register-defaults.ts
const PlaceholderDetail = (props) => (
  <div className="p-2 border rounded">
    <p>{props.title || 'Untitled'}</p>
  </div>
);
registry.register({ renderers: { detail: PlaceholderDetail } });

// Paso 4: Actualizar después de crear EntityCard
// Volver a register-defaults.ts y cambiar a:
// detail: (props) => <EntityCard {...props} />
```

---

## Checklist de Arquitectura

Antes de hacer commit, verificar:

- [ ] ¿El registry se puebla dinámicamente desde JSON schema?
- [ ] ¿El payload usa unión discriminada, no `Record<string, unknown>`?
- [ ] ¿Las operaciones visuales (collapse/expand) usan `isVisualOnly: true`?
- [ ] ¿ELKjs corre en un Web Worker?
- [ ] ¿Se usan `onNodesDelete`/`onEdgesDelete` de ReactFlow?
- [ ] ¿Los placeholders evitan dependencias circulares?
- [ ] ¿No hay imports de `register-defaults.ts` en código de producción?

---

## Referencias

- Paso 1: `steps/SPEC_GRP_001_step1_stores.md`
- Paso 3: `steps/SPEC_GRP_001_step03_registry.md`
- Paso 5: `steps/SPEC_GRP_001_step05_graph_canvas.md`
- Paso 9: `steps/SPEC_GRP_001_step09_hooks.md`
- Paso 10: `steps/SPEC_GRP_001_step10_l1_page.md`
