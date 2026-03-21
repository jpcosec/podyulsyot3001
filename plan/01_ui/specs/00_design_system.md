# Design System: Terran Command Theme

Extraído de los 6 UI samples. Fuente canónica para todos los specs.

---

## Paleta de Colores

Dos variantes en los samples (portfolio/deployment usan v1; match/extraction usan v2). Se unifican en una sola:

```
/* Superficies */
--bg:                  #0c0e10   /* fondo absoluto */
--surface:             #121416   /* superficie base */
--surface-low:         #1a1c1e
--surface-container:   #1e2022
--surface-high:        #282a2c
--surface-highest:     #333537

/* Acento principal — Cyan */
--primary:             #00f2ff   /* accent puro (glow, bordes activos) */
--primary-dim:         #99f7ff   /* variante más suave */
--on-primary:          #00363a

/* Acento secundario — Amber */
--secondary:           #ffaa00   /* deadlines, control panel headers */
--secondary-dim:       #fecb00
--on-secondary:        #452b00

/* Error / Gap */
--error:               #ffb4ab
--error-container:     #93000a

/* Texto */
--text-main:           #e2e2e5   /* on-surface */
--text-muted:          #849495   /* outline */
--text-faint:          #3a494b   /* outline-variant */
```

---

## Tipografías

```
font-headline: Space Grotesk          → headers, nav links, títulos de panel
font-body:     Inter                  → texto corrido, descripciones
font-mono:     JetBrains Mono         → IDs, timestamps, JSON, badges, tags
```

Convención de uso:
- Títulos de app (`PHD_OS // INTEL_REVIEW`): headline, bold, uppercase, tracking-tight
- Labels de sección: mono, uppercase, tracking-widest, text-muted
- Contenido: body regular
- IDs, scores, estados: mono xs/[10px], uppercase

---

## Border Radius

**Cero** — `border-radius: 0px` en todo excepto `border-radius: 9999px` para dots/pills de status.

---

## Efectos Especiales

### Scanline overlay (CRT effect)
```css
.scanline-overlay {
  background:
    linear-gradient(rgba(18,16,16,0) 50%, rgba(0,0,0,0.25) 50%),
    linear-gradient(90deg, rgba(255,0,0,0.03), rgba(0,255,0,0.01), rgba(0,0,255,0.03));
  background-size: 100% 2px, 3px 100%;
  pointer-events: none;
  opacity: 0.2;
}
```

### Tactical glow (cyan — elementos activos)
```css
.tactical-glow {
  box-shadow: 0 0 15px rgba(0, 242, 255, 0.15);
}
```

### Alert glow (amber — deadlines, warnings)
```css
.alert-glow {
  box-shadow: 0 0 15px rgba(255, 170, 0, 0.15);
}
```

### Panel border
```css
.panel-border {
  border: 1px solid rgba(132, 148, 149, 0.2);
}
```

### Dot-grid background (canvas de grafo)
```css
.node-connector {
  background-image: radial-gradient(circle, rgba(0,242,255,0.08) 1px, transparent 1px);
  background-size: 24px 24px;
}
```

### Edge pulse (SVG animated)
```css
@keyframes pulse-flow {
  0%   { stroke-dashoffset: 100; opacity: 0.4; }
  50%  { opacity: 1; }
  100% { stroke-dashoffset: 0; opacity: 0.4; }
}
.edge-pulse { animation: pulse-flow 3s linear infinite; }
```

---

## Layout Shell Global

```
┌─────────────────────────────────────────────────────┐
│  TopBar h-14  [PHD_OS // INTEL_REVIEW]  [nav icons] │
├──────────┬──────────────────────────┬───────────────┤
│ LeftNav  │   Main Canvas            │  RightPanel   │
│  w-64    │   (flex-1)               │  w-80         │
│          │                          │  (contextual) │
│ Portfolio│                          │               │
│ Evidence │                          │               │
│ Sandbox  │                          │               │
│ Settings │                          │               │
└──────────┴──────────────────────────┴───────────────┘
│  StatusBar h-10  (pipeline stage progress)          │
└─────────────────────────────────────────────────────┘
```

- **LeftNav**: siempre visible, `bg-[#0c0e10]/95`, `border-r border-primary/10`
- **TopBar**: `bg-[#0c0e10]`, `border-b border-primary/10`, logo + pipeline nav + icons
- **RightPanel**: contextual por vista — amber header en HITL, cyan en monitoreo
- **StatusBar**: solo visible en vistas de pipeline job, muestra progreso de etapas

---

## Pipeline Nav (TopBar secundario — solo en Job views)

```
SCRAPE → EXTRACT → MATCH → REVIEW → GENERATE → PACKAGE
```

- Etapa activa: `text-primary border-b-2 border-primary shadow-[0_4px_12px_rgba(0,242,255,0.2)]`
- Etapas inactivas: `text-slate-500 hover:text-primary/70`
- Fuente: `font-headline uppercase tracking-widest text-xs`

---

## Semántica de Colores por Estado

| Estado | Color | Uso |
|--------|-------|-----|
| Completado / Match | `--primary` (cyan) | Edge completado, badge verified |
| Pendiente / Neutral | `--text-muted` (grey) | Badge pending, nodo sin resolver |
| HITL requerido / Warning | `--secondary` (amber) | Control Panel, deadline sensor |
| Gap crítico / Error | `--error` (salmon) | Badge gap, nodo sin evidencia |
| En proceso | `--secondary-dim` animate-pulse | Running indicator |

---

## Componentes Atómicos

### Badge de estado
```
[MISSION_CRITICAL]  — bg-secondary/10 text-secondary border border-secondary/30
[VERIFIED]          — bg-primary/10 text-primary border border-primary/30
[PENDING]           — bg-outline/10 text-outline border border-outline/30
[GAP_DETECTED]      — bg-error-container/20 text-error border border-error/30
```

### Pipeline progress bar (segmentado)
```
[■][■][■][□][□]   — cada segmento es h-1.5 w-6
Lleno: bg-primary shadow-[0_0_4px_rgba(0,242,255,0.4)]
Vacío: bg-surface-container border border-outline-variant/30
```

### Evidence card (draggable)
```
┌─ ID: EV-8892  [drag_indicator] ─┐
│  Título del proyecto             │
│  [TAG_1] [TAG_2]                 │
│ ● terminal port (left edge)      │
└──────────────────────────────────┘
bg-surface-container-high border border-primary/10
hover: border-primary/40
```

### Scrollbar custom
```css
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: rgba(0,242,255,0.2); }
::-webkit-scrollbar-thumb:hover { background: rgba(0,242,255,0.4); }
```
