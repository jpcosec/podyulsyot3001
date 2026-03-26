# Other Projects Analysis - Node Graph Editors

**Fecha:** 2026-03-26
**Estado:** En progreso

---

## Propósito

Documentar hallazgos de proyectos similares que usan editores de grafos basados en nodos para informar decisiones de arquitectura.

---

## 1. chaiNNer

**Repo:** https://github.com/chaiNNer/chaiNNer
**Tipo:** Aplicación de escritorio (Electron + Python backend)
**Framework UI:** React (sin ReactFlow, pero similar concepto)

### Arquitectura

- **Frontend:** React con API de grafos custom
- **Backend:** Python con calculation engine
- **Layout:** Calculado en backend Python, enviado al frontend
- **Nodos:** Definidos en Python, serializados a JSON para frontend

### Decisiones clave

1. **Sin wrapper complejo**: Usan ReactFlow directamente, sin capa de abstracción sobre ReactFlow
2. **Nodos simples**: `nodeTypes` es un objeto simple, no generado dinámicamente
3. **Parent/child nativo**: Usan `extent: 'parent'` de ReactFlow para grupos
4. **Layout en backend**: Python calcula posiciones usando networkx, no ELK

### Código relevante

```python
# En backend - calculo de layout
import networkx as nx

def layout_nodes(graph: nx.DiGraph) -> dict:
    # Usar graphviz o networkx para layout
    pos = nx.nx_agraph.graphviz_layout(graph, prog='dot')
    return pos
```

```javascript
// Frontend - nodeTypes simple
import { notes } from './nodes';

const nodeTypes = {
  ...notes,
  // Sin generación dinámica
};

<ReactFlow nodeTypes={nodeTypes} ... />
```

### Extraído para nuestro proyecto

- ✅ No sobre-ingenierizar el wrapper de ReactFlow
- ✅ Usar dagre o networkx para layout (si hay backend Python)
- ✅ Usar `extent: 'parent'` para grupos nativos
- ✅ Mantener nodeTypes estable (no recrear en cada render)

---

## 2. Dify

**Repo:** https://github.com/langgenius/dify
**Tipo:** SaaS (Next.js + Python backend)
**Framework UI:** Custom canvas (sin ReactFlow)

### Arquitectura

- **Frontend:** Custom SVG-based canvas (no ReactFlow)
- **Backend:** Python FastAPI
- **Nodos:** Componentes React renderizados en posiciones fixed

### Decisiones clave

1. **Canvas custom**: No usan ReactFlow, implementan su propio canvas SVG
2. **Alto mantenimiento**: Mucho código para funcionalidades que ReactFlow provee
3. **Interactivity:** Drag/drop, zooming implementado manualmente

### Crítica

- ❌ Canvas custom requiere reimplementar muchas funcionalidades
- ❌ Mayor superficie de bugs
- ❌ Difícil de mantener

### Extraído para nuestro proyecto

- ✅ NO implementar canvas custom - usar ReactFlow
- ✅ Evitar el error de Dify de reimplementar lo que ya existe

---

## 3. agentok

**Repo:** https://github.com/dustland/agentok

---

## 4. Arroyo

**Repo:** https://github.com/ArroyoSystems/arroyo

---

## 5. ameliorate

**Repo:** https://github.com/amelioro/ameliorate

---

## 6. simple-ai

**Repo:** https://github.com/Alwurts/simple-ai

---

## 7. prismaliser

**Repo:** https://github.com/Ovyerus/prismaliser

---

## 8. json-sea

**Repo:** https://github.com/altenull/json-sea

---

## Síntesis de Hallazgos

| Proyecto | Framework Grafo | Layout | Complexidad |
|----------|-----------------|--------|-------------|
| chaiNNer | ReactFlow | Backend (Python) | Baja |
| Dify | Custom SVG | Desconocido | Alta ❌ |
| agentok | ? | ? | ? |
| Arroyo | ? | ? | ? |
| ameliorate | ? | ? | ? |
| simple-ai | ? | ? | ? |
| prismaliser | ? | ? | ? |
| json-sea | ? | ? | ? |

### Recomendaciones generales

1. **Usar ReactFlow** - No reinventar el canvas
2. **dagre para layout** - Más simple que ELK, sin worker issues
3. **nodeTypes estable** - No recrear en cada render
4. **Extent nativo** - Usar `extent: 'parent'` para grupos

---

## Tags para seguimiento

- `ANALYSIS: chaiNNer` ✅
- `ANALYSIS: Dify` ✅
- `ANALYSIS: agentok` ⏳
- `ANALYSIS: Arroyo` ⏳
- `ANALYSIS: ameliorate` ⏳
- `ANALYSIS: simple-ai` ⏳
- `ANALYSIS: prismaliser` ⏳
- `ANALYSIS: json-sea` ⏳
