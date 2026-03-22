# Spec A3 — Base CV Editor (Evidence Bank Global)

**Feature:** `src/features/base-cv/`
**Page:** `src/pages/global/BaseCvEditor.tsx`
**Librerías:** `@xyflow/react` · `@dagrejs/dagre` · `@tanstack/react-query` · `lucide-react`
**Fase:** 9

---

## Migration Notes

**Legacy source:** `apps/review-workbench/src/sandbox/pages/CvGraphEditorPage.tsx` en branch `dev`  
**Legacy components:** extraer CvGraphCanvas, EntryNode, SkillNode del sandbox  
**To migrate:** mover a `features/base-cv/` + aplicar estética Terran Command + conectar via `useCvProfileGraph`

Vista global para gestionar el "arsenal" de experiencias y habilidades maestras — el perfil canónico que el pipeline usa como fuente para generar aplicaciones. El operador puede:
- Ver todos sus entries (experiencias, educación, publicaciones, idiomas) y skills como grafo visual
- Editar el contenido de cualquier entry/skill en el panel lateral
- Marcar entries/skills como `essential` vs opcionales
- Agregar o eliminar entries y skills
- Ver las conexiones `demonstrates` (qué skills demuestran qué entries)

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v1/portfolio/cv-profile-graph` → `CvProfileGraphPayload`
  ```ts
  {
    profile_id, snapshot_version, captured_on,
    entries: CvEntry[],
    skills: CvSkill[],
    demonstrates: CvDemonstratesEdge[]
  }
  ```

**Escritura:**
- `PUT /api/v1/portfolio/cv-profile-graph` → mismo payload

---

## 3. Composición de la UI y Layout

**Layout:** ReactFlow canvas (flex-1) + `<NodeInspector>` derecho (w-80).

```
┌─ LeftNav ─┬──── ReactFlow Canvas (flex-1) ────────┬── Inspector (w-80) ──┐
│           │  [dot-grid] [scanline]                 │ Si nodo seleccionado:│
│           │                                        │   campos editables   │
│           │  [CvEntry nodes] → [CvSkill nodes]    │                      │
│           │  [color por category]                  │ Sin selección:       │
│           │  [essential badge en nodo]             │   ProfileStats       │
│           │                                        │                      │
│           │  [ReactFlow toolbar: zoom/fit/add]     │ [SAVE]               │
└───────────┴────────────────────────────────────────┴──────────────────────┘
```

**Tipos de nodos:**

`CvEntry node`:
```
┌─ [category badge] ─────── [essential ●] ─┐
│  título / institución / fecha             │
│  descripción breve — 1 línea             │
│  ID: P_EXP_005  (mono xs)                │
└───────────────────────────────────────────┘
borde color por categoría:
  experience → primary (cyan)
  education  → outline
  publication→ secondary (amber)
  language   → error/salmon
```

`CvSkill node` (compacto):
```
┌─ [label] ── [level badge] ─┐
│  ID: P_SKL_021  [category] │
└────────────────────────────┘
```

`demonstrates edge` — dashed cyan, animated pulse si `essential=true`

**Componentes Core:**
- `<CvGraphCanvas>` — ReactFlow con dagre layout automático
- `<EntryNode>` / `<SkillNode>` — nodos custom Terran Command
- `<NodeInspector>` — panel con inputs/textareas editables
- `<ProfileStats>` — counts de entries/skills cuando nada está seleccionado

---

## 4. Estilos (Terran Command)

- Canvas: `bg-surface node-connector`
- Nodo seleccionado: `border-primary tactical-glow`
- Edge `demonstrates`: `stroke=#00f2ff stroke-dasharray="6 3"` + `edge-pulse` si essential
- ID del nodo: `font-mono text-[9px] text-on-muted/60`
- Título entry: `font-headline font-semibold text-sm text-on-surface`

**Interacciones:**
- Click en nodo → abre inspector lateral
- `Ctrl+S` → `saveCvProfileGraphPayload` (useMutation + invalidar query)
- `F` → fit-to-screen del canvas
- `Delete` → elimina nodo (confirm dialog)
- Drag nodo → reposiciona (posición solo en estado local)

**Estado Vacío:** icono + `EVIDENCE_BANK_EMPTY — ADD_FIRST_ENTRY`
**Estado Error:** toast amber `SAVE_FAILED` / panel con retry si falla el load

---

## 5. Archivos a crear

```
src/features/base-cv/
  api/
    useCvProfileGraph.ts          useQuery + useMutation
  components/
    CvGraphCanvas.tsx             ReactFlow + dagre layout
    EntryNode.tsx                 custom node Terran Command
    SkillNode.tsx                 custom node compacto
    NodeInspector.tsx             panel lateral con inputs
    ProfileStats.tsx              mini dashboard de counts
src/pages/global/
  BaseCvEditor.tsx                TONTO: hook + render
```

---

## 6. Definition of Done

```
[ ] BaseCvEditor renderiza sin errores con datos del mock cv_profile_graph.json
[ ] Nodos se posicionan con dagre (no amontonados)
[ ] Click en nodo abre NodeInspector con datos del nodo
[ ] Editar un campo en NodeInspector + Ctrl+S → llama useMutation
[ ] useMutation resuelve sin error (mock no-op)
[ ] ProfileStats muestra counts correctos cuando nada está seleccionado
[ ] Edges demonstrated se ven como líneas dashed cyan entre nodos
[ ] Essential entries tienen el borde pulsando
[ ] Sin datos hardcodeados — todo dato proviene del mock/API, nunca de literales en el componente
```

---

## 7. E2E (TestSprite)

**URL:** `/cv`

1. Verificar que el canvas de ReactFlow renderiza con nodos visibles
2. Hacer click en un nodo de entry → verificar que `<NodeInspector>` aparece con el título del nodo
3. Editar el campo de título en el inspector → presionar `Ctrl+S` → verificar que no hay error en consola
4. Click fuera de cualquier nodo → verificar que `<ProfileStats>` vuelve a aparecer

---

## 8. Git Workflow

### Commit al cerrar la fase

```
feat(ui): implement base CV editor (A3)

- CvGraphCanvas with ReactFlow + dagre layout
- EntryNode and SkillNode custom components
- NodeInspector sidebar for editing
- ProfileStats dashboard when nothing selected
- Connected to useCvProfileGraph hook
```

### Changelog entry (changelog.md)

```markdown
## YYYY-MM-DD

- Implemented A3 Base CV Editor: ReactFlow graph with Entry/Skill nodes,
  inspector sidebar, and demonstrates edges visualization.
```

### Checklist update (index_checklist.md)

- [x] A3 Base CV Editor
