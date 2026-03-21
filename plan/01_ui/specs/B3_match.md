# Spec: Match (HITL B)

## 1. Objetivo del Operador
El LLM emparejó los requerimientos del job con la evidencia del perfil. El operador debe:
- Ver el grafo de conexiones (requerimientos ↔ evidencias) con scores y reasoning
- Identificar gaps críticos (score 0.0 — sin evidencia) y matches débiles
- Aprobar matches correctos, forzar conexiones manuales no detectadas por el LLM
- Descartar conexiones alucinadas o incorrectas
- Proporcionar feedback textual si pide regeneración
- Tomar la decisión final: approve / request_regeneration / reject

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v1/jobs/:source/:jobId/view1` → `ViewOnePayload`
  ```ts
  {
    source, job_id,
    nodes: GraphNode[],    // { id, label, kind: "requirement" | "profile" }
    edges: GraphEdge[]     // { source, target, label, score, reasoning, evidence_id }
  }
  ```

**Escritura:**
- `PUT /api/v1/jobs/:source/:jobId/editor/match/state` → guarda decisión de match

---

## 3. Composición de la UI y Layout

**Layout Base:** 3 paneles — Left sidebar (Evidence Bank draggable) + Main ReactFlow canvas + Right Control Panel.

```
┌─ LeftNav ─┬── Evidence Bank (w-64) ──┬──── Match Graph (flex-1) ────┬── Control Panel (w-80) ─┐
│           │ [ASSETS_REPOSITORY]      │  [dot-grid canvas]           │ [PHASE: MATCH_EVIDENCE] │
│           │                          │  [scanline overlay]          │                         │
│           │ Evidence cards           │                              │ Tabs:                   │
│           │ (draggables):            │  Requirement nodes (left)    │  Technical / Stage      │
│           │                          │  Profile nodes (right)       │                         │
│           │ [ID: P_EXP_006]          │  Edges con score badge       │ Si nodo/edge            │
│           │  EEG Stress Detection    │                              │ seleccionado:           │
│           │  [EEG] [PYTORCH]         │  Score tooltip en edge:      │  JSON readout           │
│           │                          │  "95% MATCH_LOCKED"          │                         │
│           │ [drag_indicator ↕]       │                              │ [COMMIT MATCH BUNDLE]   │
│           │                          │  [ReactFlow toolbar]         │ [REQUEST REGEN]         │
│           │ [COMMIT MATCH BUNDLE]    │                              │ [REJECT]                │
└───────────┴──────────────────────────┴──────────────────────────────┴─────────────────────────┘
```

**Nodos en el grafo:**

`RequirementNode`:
```
┌─ [priority badge] ──────────── [status icon] ─[connection port]─┐
│  label (texto del requerimiento)                                 │
│  score: 0.0 / 0.5 / 0.9 / 1.0  (barra de progreso)            │
│  UNRESOLVED / RESOLVED / GAP                                     │
└──────────────────────────────────────────────────────────────────┘
```

Color del borde izquierdo por estado:
```
score >= 0.7 → border-l-4 border-primary   [VERIFIED]
score 0.3-0.6 → border-l-4 border-secondary  [PARTIAL]
score < 0.3  → border-l-4 border-error     [GAP]
```

`ProfileNode` (evidencia):
```
┌─ [ID] ────────────── [●connection port] ─┐
│  título corto                             │
│  [category badge]                         │
└───────────────────────────────────────────┘
```

**Edges:**
- Matched: `stroke=#00f2ff` dashed animated (`edge-pulse`), score tooltip badge en midpoint
- Manual (forzado por operador): `stroke=#fecb00` dashed — diferenciado del LLM
- Gap (sin edge): nodo requirement con indicator rojo, sin edge

**Componentes Core:**
- `<MatchGraphCanvas>` — ReactFlow con dagre layout (reqs izquierda, profile derecha)
- `<RequirementNode>` / `<ProfileNode>` — custom nodes Terran Command
- `<EdgeScoreBadge>` — foreignObject en midpoint del edge con score
- `<EvidenceBankPanel>` — left sidebar de cards draggables
- `<MatchControlPanel>` — right sidebar amber con JSON readout + decision buttons

**Componentes a Reciclar/Limpiar:**
- `ViewOneGraphExplorer.tsx` + `GraphCanvas.tsx` — base a rediseñar con los nuevos nodos custom
- Eliminar dagre re-import duplicado

---

## 4. Estilos y Unificación (Terran Command Theme)

**Paleta:**
- Canvas: `bg-surface node-connector` dot-grid
- Evidence Bank sidebar: `bg-[#0c0e10]/95 border-r border-primary/10`
- Control Panel: `bg-[#0c0e10] border-l border-secondary/20`
- Control Panel header: `text-secondary font-headline`
- Edge verified: `#00f2ff` con `edge-pulse`
- Edge manual: `#fecb00` con `edge-pulse`
- HUD táctico (top-left canvas): fondo `bg-background/80` con texto `>> SCANNING...`

**Tipografía:**
- Score en edge: `font-mono font-black text-[9px] text-on-primary`
- Reasoning (hover tooltip o en control panel): `font-body text-xs text-on-surface-variant`

**Interacciones Clave:**
- Click en nodo → lo selecciona, actualiza JSON readout en control panel
- Click en edge → muestra reasoning en control panel
- Drag de evidence card a requirement node → crea edge manual
- `Ctrl+S` → guarda estado del match
- `Ctrl+Enter` → abre modal de decisión final (approve/regen/reject)
- `Delete` en edge seleccionado → elimina conexión

**Modal de decisión:**
```
┌── COMMIT MATCH DECISION ─────────────────────────┐
│ [● APPROVE]   Advance to Generate Documents      │
│ [↺ REGEN]     Feedback textarea → re-run LLM     │
│ [✗ REJECT]    Archive job, mark as rejected      │
└──────────────────────────────────────────────────┘
```

**Estado Vacío:**
- Sin matches: todos los nodos requirement con border-error, sin edges

**Estado Error:**
- LLM match falló: banner amber `MATCH_GENERATION_FAILED`
