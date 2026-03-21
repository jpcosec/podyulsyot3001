# Spec: Base CV Editor (Evidence Bank Global)

## 1. Objetivo del Operador
Esta es la vista global donde el operador gestiona su "arsenal" de experiencias y habilidades maestras — el perfil canónico que el pipeline usa como fuente para generar aplicaciones. El operador puede:
- Ver todos sus entries (experiencias, educación, publicaciones, idiomas) y skills como un grafo visual
- Editar el contenido de cualquier entry/skill directamente en el panel lateral
- Marcar entries/skills como `essential` (siempre se incluyen) vs opcionales
- Agregar o eliminar entries y skills
- Ver las conexiones `demonstrates` (qué skills demuestran qué entries)

Unifica y reemplaza el `CvGraphEditor` del sandbox y el sidebar `EvidenceBank` del job view.

---

## 2. Contrato de Datos (API I/O)

**Lectura:**
- `GET /api/v1/portfolio/cv-profile-graph` → `CvProfileGraphPayload`
  ```ts
  {
    profile_id: string,
    snapshot_version: string,
    captured_on: string,
    entries: CvEntry[],          // experiencias, edu, pubs, idiomas
    skills: CvSkill[],           // skills atómicos con nivel
    demonstrates: CvDemonstratesEdge[]  // entry → skill con description_keys
  }
  ```

**Escritura:**
- `PUT /api/v1/portfolio/cv-profile-graph` → mismo payload

---

## 3. Composición de la UI y Layout

**Layout Base:** Canvas ReactFlow (principal) + sidebar derecho (inspector de nodo seleccionado).

```
┌─ LeftNav ─┬────────── ReactFlow Canvas (flex-1) ──────────┬── Inspector ──┐
│           │  [dot-grid] [scanline]                        │  (w-80)       │
│           │                                               │ Si selección: │
│           │  [CvEntry nodes]  ──→  [CvSkill nodes]       │  campos edit  │
│           │                                               │               │
│           │  [color por category]                         │ Sin sel:      │
│           │  [essential badge en nodo]                    │  stats global │
│           │                                               │               │
│           │  [ReactFlow toolbar: zoom/fit/add]            │ [SAVE button] │
└───────────┴───────────────────────────────────────────────┴───────────────┘
```

**Tipos de nodos:**

`CvEntry node`:
```
┌─ [category badge] ──────────────── [essential? ●] ─┐
│  título / institución / fecha                       │
│  [descripción breve — 1 línea]                      │
│  ID: P_EXP_005  (mono xs)                           │
└─────────────────────────────────────────────────────┘
color borde: por categoría
  experience → cyan (--primary)
  education  → outline
  publication→ secondary (amber)
  language   → tertiary/salmon
```

`CvSkill node` (más compacto):
```
┌─ [label] ─────── [level badge] ─┐
│  ID: P_SKL_021  [category]      │
└──────────────────────────────────┘
```

`demonstrates edge`: línea dashed cyan, animated pulse si `essential=true`

**Componentes Core:**
- `<CvGraphCanvas>` — ReactFlow con nodos custom y dagre layout
- `<EntryNode>` / `<SkillNode>` — nodos custom Terran Command styled
- `<NodeInspector>` — panel lateral con form de edición (Slate o inputs simples)
- `<ProfileStats>` — mini dashboard de counts cuando nada está seleccionado

**Componentes a Reciclar/Limpiar:**
- `CvGraphEditorPage.tsx` + `cv-graph/` components del sandbox — limpiar CSS, migrar a nueva paleta
- Eliminar cualquier import de sandbox styles

---

## 4. Estilos y Unificación (Terran Command Theme)

**Paleta:**
- Canvas fondo: `bg-surface` con `node-connector` dot-grid
- Nodo entry seleccionado: `border-primary node-active` glow
- Nodo entry normal: `border-primary/20 node-glow`
- Nodo skill: más pequeño, `border-outline/30`
- Edge `demonstrates`: `stroke=#00f2ff stroke-dasharray="6 3"` con `edge-pulse` si essential

**Tipografía:**
- ID del nodo: `font-mono text-[9px] text-outline/60`
- Título del entry: `font-headline font-semibold text-sm text-on-surface`
- Category badge: `font-mono text-[9px] uppercase tracking-widest`

**Interacciones Clave:**
- Click en nodo → abre inspector lateral con campos editables
- `Ctrl+S` → guarda todo el grafo (`saveCvProfileGraphPayload`)
- `Ctrl+Z` / `Ctrl+Y` → undo/redo (estado local en React)
- `F` → fit-to-screen del canvas
- `Delete` → elimina nodo seleccionado (con confirm dialog)
- Drag nodo → reposiciona (posición solo en estado local, no persiste al backend)

**Estado Vacío:**
- Canvas sin nodos: icono `account_tree` + "EVIDENCE_BANK_EMPTY — ADD_FIRST_ENTRY"

**Estado Error:**
- Fallo en save: toast amber en bottom: "SAVE_FAILED: [error msg]"
- Fallo en load: panel de error con retry button
