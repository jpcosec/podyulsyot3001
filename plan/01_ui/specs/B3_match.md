# Spec B3 — Match (HITL B)

**Feature:** `src/features/job-pipeline/`
**Page:** `src/pages/job/Match.tsx`
**Librerías:** `@xyflow/react` · `@dagrejs/dagre` · `@dnd-kit/core` · `@tanstack/react-query` · `lucide-react`
**Fase:** 5

---

## Migration Notes

**Legacy source:** `apps/review-workbench/src/views/ViewOneGraphExplorer.tsx` en branch `dev`  
**Legacy reference:** extraer shape del JSON de `view_match_*.json` y `evidence_bank.json` fixtures  
**To migrate:** mover lógica a `features/job-pipeline/` + aplicar ReactFlow + conectar via `useMatchState`

El LLM emparejó requerimientos del job con evidencia del perfil. El operador debe:
- Ver el grafo de conexiones (requerimientos ↔ evidencias) con scores y reasoning
- Identificar gaps críticos (score 0.0) y matches débiles
- Aprobar matches correctos, forzar conexiones manuales no detectadas
- Descartar conexiones alucinadas
- Proporcionar feedback si pide regeneración
- Tomar la decisión final: approve / request_regeneration / reject

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v2/query/jobs/:source/:job_id/views/match` → `ViewPayload<'match'>`
  ```ts
  {
    view: 'match', source, job_id,
    data: {
      nodes: GraphNode[],    // { id, label, kind: "requirement" | "profile" }
      edges: GraphEdge[]     // { source, target, label, score, reasoning, evidence_id }
    }
  }
  ```
- `GET /api/v2/query/jobs/:source/:job_id/evidence-bank` → `EvidenceBankPayload`

**Escritura:**
- `PUT /api/v2/commands/jobs/:source/:job_id/state/match` — guarda correcciones al grafo
- `POST /api/v2/commands/jobs/:source/:job_id/gates/review_match/decide` — cierra el gate HITL
  ```ts
  { decision: 'approve' | 'request_regeneration' | 'reject', feedback?: string[] }
  ```
- `POST /api/v2/commands/jobs/:source/:job_id/run` → `{ resume_from_hitl: true }` — reanuda LangGraph

---

## 3. Composición de la UI y Layout

**Layout:** 3 paneles — Evidence Bank (left, w-64) + ReactFlow canvas (flex-1) + Control Panel (right, w-80).

```
┌── Evidence Bank ──┬──── Match Graph (flex-1) ────┬── Control Panel ──┐
│ [ASSETS_REPO]     │  [dot-grid] [scanline]        │ [PHASE: MATCH]    │
│                   │                               │                   │
│ Evidence cards    │  Requirement nodes (left)     │ Si selección:     │
│ (draggables):     │  Profile nodes (right)        │   JSON readout    │
│ [P_EXP_006]       │  Edges: score badge midpoint  │                   │
│  EEG Detection    │                               │ [COMMIT MATCH]    │
│  [EEG][PYTORCH]   │  Edge tooltip: "95% LOCKED"   │ [REQUEST REGEN]   │
│ [⋮ drag]          │                               │ [REJECT]          │
└───────────────────┴───────────────────────────────┴───────────────────┘
```

**Tipos de nodo:**

`RequirementNode`:
```
┌─ [priority badge] ──── [status icon] ─[port]─┐
│  label (texto del requerimiento)              │
│  score: ████░░ (progress bar)                 │
│  UNRESOLVED / RESOLVED / GAP                  │
└───────────────────────────────────────────────┘
borde izquierdo:
  score >= 0.7 → border-l-4 border-primary   [VERIFIED]
  score 0.3–0.6 → border-l-4 border-secondary [PARTIAL]
  score < 0.3  → border-l-4 border-error     [GAP]
```

`ProfileNode` (compacto):
```
┌─ [ID] ──── [●port] ─┐
│  título corto        │
│  [category badge]    │
└──────────────────────┘
```

**Edges:**
- LLM match: `stroke=#00f2ff` dashed animated, score badge en midpoint
- Manual (operador): `stroke=#fecb00` dashed — diferenciado del LLM
- Gap: requirement node con border-error, sin edge

**Componentes Core:**
- `<MatchGraphCanvas>` — ReactFlow con dagre layout (reqs izq, profile der)
- `<RequirementNode>` / `<ProfileNode>` — custom nodes
- `<EdgeScoreBadge>` — foreignObject en midpoint con score
- `<EvidenceBankPanel>` — left sidebar de cards draggables (dnd-kit)
- `<MatchControlPanel>` — right panel amber, JSON readout + decision buttons
- `<MatchDecisionModal>` — modal con opciones approve / regen / reject

---

## 4. Estilos (Terran Command)

- Canvas: `bg-surface node-connector`
- Evidence Bank: `bg-background/95 border-r border-primary/10`
- Control Panel: `bg-background border-l border-secondary/20`
- Edge verified: `#00f2ff` + `edge-pulse`
- Edge manual: `#fecb00` + `edge-pulse`
- Score badge: `font-mono font-black text-[9px]`

**Interacciones:**
- Click en nodo → selecciona, actualiza JSON readout en control panel
- Click en edge → muestra reasoning en control panel
- Drag de evidence card a requirement node → crea edge manual
- `Ctrl+S` → guarda estado del match
- `Ctrl+Enter` → abre `<MatchDecisionModal>`
- `Delete` en edge seleccionado → elimina conexión

**Estado Vacío:** todos los nodos con border-error, sin edges
**Estado Error:** banner amber `MATCH_GENERATION_FAILED`

---

## 5. Archivos a crear

```
src/features/job-pipeline/
  api/
    useMatchState.ts              useQuery(['view', 'match', source, jobId])
    useMatchSave.ts              useMutation → PUT /commands/.../state/match
    useMatchDecide.ts            useMutation → POST /commands/.../gates/:gate/decide
    useJobRun.ts                 useMutation → POST /commands/.../run
  components/
    MatchGraphCanvas.tsx          ReactFlow + dagre + custom nodes/edges
    RequirementNode.tsx           custom node con score bar
    ProfileNode.tsx               custom node compacto
    EdgeScoreBadge.tsx            foreignObject midpoint badge
    EvidenceBankPanel.tsx         left sidebar dnd-kit draggables
    MatchControlPanel.tsx         right panel con JSON readout
    MatchDecisionModal.tsx        modal approve/regen/reject
src/pages/job/
  Match.tsx                       TONTO: useParams + hooks + render
```
src/features/job-pipeline/
  api/
    useViewMatch.ts               useQuery(['view', 'match', source, jobId])
    useEditorState.ts             useMutation → PUT /commands/.../state/match
    useGateDecide.ts              useMutation → POST /commands/.../gates/:gate/decide
    useJobRun.ts                  useMutation → POST /commands/.../run
  components/
    MatchGraphCanvas.tsx          ReactFlow + dagre + custom nodes/edges
    RequirementNode.tsx           custom node con score bar
    ProfileNode.tsx               custom node compacto
    EdgeScoreBadge.tsx            foreignObject midpoint badge
    EvidenceBankPanel.tsx         left sidebar dnd-kit draggables
    MatchControlPanel.tsx         right panel con JSON readout
    MatchDecisionModal.tsx        modal approve/regen/reject
src/pages/job/
  Match.tsx                       TONTO: useParams + hooks + render
```

---

## 6. Definition of Done

```
[ ] Match renderiza con los 3 paneles para job 201397 (14 reqs del mock)
[ ] Nodos se posicionan con dagre (reqs izq, profile der)
[ ] Edges del LLM se muestran como líneas dashed cyan con badge de score
[ ] Click en nodo → MatchControlPanel muestra JSON del nodo
[ ] Click en edge → MatchControlPanel muestra reasoning
[ ] Drag de EvidenceBankPanel a un RequirementNode → crea edge manual (fecb00)
[ ] Delete en edge → elimina conexión del grafo
[ ] Ctrl+Enter → MatchDecisionModal aparece con 3 opciones
[ ] "APPROVE" en modal ejecuta useMutation sin error
[ ] Sin datos hardcodeados — todo dato proviene del mock/API, nunca de literales en el componente
```

---

## 7. E2E (TestSprite)

**URL:** `/jobs/tu_berlin/201397/match`

1. Verificar que `<MatchGraphCanvas>` renderiza con nodos visibles (reqs a la izquierda)
2. Verificar que los edges tienen badges de score sobre las líneas
3. Click en un nodo `RequirementNode` → verificar que `<MatchControlPanel>` muestra el JSON
4. Presionar `Ctrl+Enter` → verificar que `<MatchDecisionModal>` aparece
5. Click en "APPROVE" → verificar que el modal se cierra y useMutation fue llamado

---

## 8. Git Workflow

### Commit al cerrar la fase

```
feat(ui): implement match view (B3)

- MatchGraphCanvas with ReactFlow, dagre layout, and custom nodes
- RequirementNode with score bar and status indicators
- ProfileNode compact display
- EdgeScoreBadge on graph edges
- EvidenceBankPanel with dnd-kit draggables
- MatchControlPanel with JSON readout
- MatchDecisionModal with approve/regen/reject options
- Connected to useMatchState, useMatchSave, useMatchDecide hooks
```

### Changelog entry (changelog.md)

```markdown
## YYYY-MM-DD

- Implemented B3 Match: ReactFlow graph with requirement/profile nodes,
  edge score badges, evidence bank drag-and-drop, and decision modal.
```

### Checklist update (index_checklist.md)

- [x] B3 Match
