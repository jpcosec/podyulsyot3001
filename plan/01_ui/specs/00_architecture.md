# Architecture Guide — Atomic Design + Feature-Sliced

Mezcla entre **Diseño Atómico** (UI base) y **Feature-Sliced Design** (lógica de negocio).

---

## Árbol de carpetas target

```
src/
├── api/                        # Capa de red pura (agnóstica a React)
│   ├── client.ts               # Wrapper de fetch (interceptors, auth)
│   └── endpoints.ts            # Definición de URLs (/api/v1/jobs...)
│
├── components/                 # UI global (Diseño Atómico puro, sin lógica de negocio)
│   ├── atoms/                  # Button.tsx, Badge.tsx, Tag.tsx, Spinner.tsx, Kbd.tsx
│   ├── molecules/              # SplitPane.tsx, ControlPanel.tsx, DiagnosticCard.tsx
│   ├── organisms/              # IntelligentEditor.tsx, GraphCanvas.tsx, FileTree.tsx
│   └── layouts/                # AppShell.tsx, JobWorkspaceShell.tsx
│
├── features/                   # Lógica de negocio (el corazón de la app)
│   ├── portfolio/              # A1 — Portfolio Dashboard
│   │   ├── api/                # usePortfolioSummary.ts
│   │   └── components/        # PortfolioTable.tsx, ProgressSegmented.tsx
│   │
│   ├── base-cv/                # A3 — Base CV Editor
│   │   ├── api/                # useCvProfileGraph.ts
│   │   └── components/        # NodeInspectorSidebar.tsx
│   │
│   └── job-pipeline/           # B0–B4 — El flujo del job
│       ├── api/                # useJobTimeline.ts, useExtractState.ts, useMatchState.ts
│       ├── components/         # HitlCtaBanner.tsx, RequirementList.tsx, EvidenceBankSidebar.tsx
│       └── utils/              # helpers de matching, scoring, diff
│
├── pages/                      # Puntos de entrada (rutas) — tontas por diseño
│   ├── global/                 # PortfolioPage.tsx, DataExplorerPage.tsx, CvEditorPage.tsx
│   └── job/                    # JobFlowPage.tsx, ExtractPage.tsx, MatchPage.tsx, DocumentsPage.tsx
│
├── types/                      # Contratos TypeScript (idénticos al backend)
│   ├── api.types.ts            # PortfolioSummary, GraphNode, ViewOnePayload...
│   └── ui.types.ts             # tipos internos de ReactFlow, DnD, editor state
│
├── utils/                      # Helpers globales
│   ├── cn.ts                   # clsx + tailwind-merge
│   └── formatters.ts           # fechas, bytes→MB, duración de stages
│
├── App.tsx                     # Router (createBrowserRouter)
├── main.tsx                    # Entry point — Providers: QueryClient, Theme
└── styles.css                  # Tailwind @theme + utilities
```

---

## Las 3 Reglas de Oro

### Regla 1 — Las `pages/` son tontas, las `features/` son listas

Un archivo en `pages/` tiene exactamente tres responsabilidades:

1. Leer parámetros de URL (`useParams`)
2. Llamar al hook de datos de la feature (`useExtractState(jobId)`)
3. Renderizar el layout inyectando los componentes de la feature

```tsx
// pages/job/ExtractPage.tsx — correcto
export function ExtractPage() {
  const { source, jobId } = useParams();
  const { data, isLoading } = useExtractState(source!, jobId!);
  return <JobWorkspaceShell><ExtractView data={data} loading={isLoading} /></JobWorkspaceShell>;
}
```

**Si tu Page tiene más de ~80 líneas, estás poniendo lógica donde no va.**

---

### Regla 2 — Feature-Sliced evita el acoplamiento

Agrupar por feature (no por tipo de archivo) significa que borrar o rediseñar una vista
no contamina el resto de la app. Toda la lógica de Match vive y muere en `features/job-pipeline/`.

```
# MAL — agrupa por tipo (el clásico que escala fatal)
hooks/useMatchState.ts
hooks/useExtractState.ts
components/MatchPanel.tsx
components/RequirementList.tsx

# BIEN — agrupa por feature
features/job-pipeline/api/useMatchState.ts
features/job-pipeline/api/useExtractState.ts
features/job-pipeline/components/MatchPanel.tsx
features/job-pipeline/components/RequirementList.tsx
```

---

### Regla 3 — `cn()` para todos los átomos

Los componentes base (`<Button>`, `<Badge>`, etc.) reciben `className` como prop para
permitir overrides contextuales. Sin `cn()`, Tailwind genera clases duplicadas que se
anulan de forma impredecible.

```ts
// utils/cn.ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

Uso en cualquier átomo:

```tsx
// components/atoms/Button.tsx
export function Button({ className, ...props }) {
  return (
    <button className={cn("bg-primary text-primary-on font-headline uppercase", className)} {...props} />
  );
}

// Llamada con override — bg-secondary gana limpio, sin colisión
<Button className="bg-secondary text-secondary-on" />
```

**Instalar antes de escribir el primer átomo:**
```bash
npm install clsx tailwind-merge
```

---

## Dirección del flujo de datos

```
API (mock o real)
  └── React Query hook (features/*/api/)
        └── Page (lee params, llama hook)
              └── Feature component (recibe data via props)
                    └── Organism / Molecule / Atom (UI pura)
```

- Las capas de abajo **nunca** importan de las capas de arriba
- Los `atoms/` y `molecules/` no saben nada del backend
- Los `features/` no importan entre sí (máximo via `types/`)
