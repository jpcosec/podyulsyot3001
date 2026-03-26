# Other Projects Analysis - Node Graph Editors

**Fecha:** 2026-03-26
**Estado:** Completado

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

### Arquitectura

- **Framework:** ReactFlow
- **Layout:** Custom / Dagre
- **Enfoque:** Orquestación de Agentes AI (AG2). Generador de código Python.
- **Complexidad:** Alta

### Análisis

Es un "peso pesado". Al igual que Dify, intenta abstraer la lógica de agentes en nodos. Usa ReactFlow pero su verdadera potencia está en el backend con FastAPI.

### Lección

No intentes imitar su complejidad si solo necesitas visualizar datos; ellos están construyendo un IDE completo.

---

## 4. Arroyo

**Repo:** https://github.com/ArroyoSystems/arroyo

### Arquitectura

- **Framework:** Custom (Rust/TS)
- **Layout:** Distributed DAG
- **Enfoque:** Motor de streaming en Rust. UI para pipelines SQL en tiempo real.
- **Complexidad:** Muy Alta

### Análisis

Es una bestia diferente. No es solo una cara bonita; es un motor de datos en Rust. Su grafo representa operadores de datos reales.

### Lección

Su arquitectura es "Graph-as-Execution-Engine", lo cual es demasiado para nuestro Node Editor a menos que planeemos ejecutar código en tiempo real.

---

## 5. ameliorate

**Repo:** https://github.com/amelioro/ameliorate

### Arquitectura

- **Framework:** ReactFlow
- **Layout:** ReactFlow Internal
- **Enfoque:** Resolución de problemas colaborativa. Stack: Next.js + Zustand.
- **Complexidad:** Media

### Análisis

¡Este es el que más se parece a nuestra filosofía! Usa ReactFlow + Zustand. Es muy "Clean Code".

### Lección

Si quieres ver cómo separar el estado del grafo de la UI de React, mira sus repositorios.

---

## 6. simple-ai

**Repo:** https://github.com/Alwurts/simple-ai

### Arquitectura

- **Framework:** Radix / Tailwind
- **Layout:** N/A (UI Kit)
- **Enfoque:** Componentes de UI para AI (átomos/moléculas). No es un editor per se.
- **Complexidad:** Baja

### Análisis

Son solo "skins" bonitos (shadcn/ui para AI).

### Lección

Úsalos de inspiración para que nuestros nodos no parezcan chatarra imperial.

---

## 7. prismaliser

**Repo:** https://github.com/Ovyerus/prismaliser

### Arquitectura

- **Framework:** ReactFlow
- **Layout:** Custom
- **Enfoque:** Visualizador de esquemas Prisma (ERD). Next.js.
- **Complexidad:** Media

---

## 8. json-sea

**Repo:** https://github.com/altenull/json-sea

### Arquitectura

- **Framework:** Rete.js
- **Layout:** Hierarchical / Worker
- **Enfoque:** Visualizador de JSON para VS Code. Usa un worker para archivos grandes.
- **Complexidad:** Media

### Análisis

Interesante porque usa Rete.js en lugar de ReactFlow. Rete.js es más rígido pero mejor para "Visual Programming". El hecho de que sea una extensión de VS Code nos dice que manejan muy bien el rendimiento con archivos grandes usando Workers.

### Lección

Si necesitas rendimiento máximo con archivos muy grandes, los Workers son la solución (aunque complicate el setup).

---

## Síntesis de Hallazgos

| Proyecto | Framework Grafo | Layout | Complexidad | Enfoque Principal |
|----------|-----------------|--------|-------------|-------------------|
| chaiNNer | ReactFlow | Backend (Python) | Baja | Image processing (Electron) |
| Dify | Custom SVG | Desconocido | Alta ❌ | AI workflow builder (SaaS) |
| agentok | ReactFlow | Custom / Dagre | Alta | Orquestación de Agentes AI |
| Arroyo | Custom (Rust/TS) | Distributed DAG | Muy Alta | Motor de streaming SQL |
| ameliorate | ReactFlow | ReactFlow Internal | Media | Resolución colaborativa de problemas |
| simple-ai | Radix / Tailwind | N/A (UI Kit) | Baja | UI Kit para AI |
| prismaliser | ReactFlow | Custom | Media | Visualizador de esquemas Prisma |
| json-sea | Rete.js | Hierarchical / Worker | Media | Visualizador JSON para VS Code |

### Recomendaciones generales

1. **Usar ReactFlow** - No reinventar el canvas
2. **dagre para layout** - Más simple que ELK, sin worker issues
3. **nodeTypes estable** - No recrear en cada render
4. **Extent nativo** - Usar `extent: 'parent'` para grupos
5. **Seguir el patrón de ameliorate** - ReactFlow + Zustand es la combinación probada

### Conclusiones

Después de analizar todos estos proyectos:

- **ameliorate** es el más parecido a nuestra filosofía (ReactFlow + Zustand)
- **chaiNNer** demuestra que el layout en backend es una opción válida
- Evitar **Dify** y su canvas custom - alto mantenimiento
- Para rendimiento máximo con archivos grandes, json-sea usa Workers (aunque complicate el setup)
- Si solo necesitamos visualizar datos, no imitar la complejidad de agentok

---

## Tags para seguimiento

- `ANALYSIS: chaiNNer` ✅
- `ANALYSIS: Dify` ✅
- `ANALYSIS: agentok` ✅
- `ANALYSIS: Arroyo` ✅
- `ANALYSIS: ameliorate` ✅
- `ANALYSIS: simple-ai` ✅
- `ANALYSIS: prismaliser` ✅
- `ANALYSIS: json-sea` ✅
