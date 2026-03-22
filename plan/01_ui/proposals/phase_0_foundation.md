# Proposal: Phase 0 — Foundation (Router + Layouts + Portfolio)

**Objetivo:** Dejar el armazón completo de la app funcionando con datos reales del mock.
Al final de esta fase, `VITE_MOCK=true npm run dev` muestra la home con los jobs reales
y la navegación global funciona end-to-end.

**Estado:** Proposal — pendiente de implementación.

---

## Paso 1 — Instalar dependencias

```bash
cd apps/review-workbench
npm install clsx tailwind-merge
npm install @tanstack/react-query @tanstack/react-query-devtools
npm install lucide-react
```

`@xyflow/react` ya está instalado. El resto (codemirror, dnd-kit, dagre) se instalan
cuando llegue su feature.

---

## Paso 2 — Utilitarios base

### `src/utils/cn.ts`

```ts
import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}
```

### `src/main.tsx` — Providers

```tsx
import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import App from './App';
import './styles.css';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 30_000, retry: 1 },
  },
});

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </StrictMode>,
);
```

---

## Paso 3 — Router con `createBrowserRouter`

### `src/App.tsx`

`JobWorkspaceShell` se anida dentro de `AppShell` — el LeftNav siempre renderiza,
nunca se duplica, nunca parpadea al navegar entre vistas.

```tsx
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { AppShell } from './components/layouts/AppShell';
import { JobWorkspaceShell } from './components/layouts/JobWorkspaceShell';
import { PortfolioDashboard } from './pages/global/PortfolioDashboard';
import { DataExplorer } from './pages/global/DataExplorer';
import { BaseCvEditor } from './pages/global/BaseCvEditor';
import { JobFlowInspector } from './pages/job/JobFlowInspector';
import { ScrapeDiagnostics } from './pages/job/ScrapeDiagnostics';
import { ExtractUnderstand } from './pages/job/ExtractUnderstand';
import { Match } from './pages/job/Match';
import { GenerateDocuments } from './pages/job/GenerateDocuments';
import { PackageDeployment } from './pages/job/PackageDeployment';
import { IntelligentEditorPage } from './sandbox/pages/IntelligentEditorPage';

const router = createBrowserRouter([
  {
    path: '/',
    element: <AppShell />,          // LeftNav siempre visible
    children: [
      // Vistas globales
      { index: true,       element: <PortfolioDashboard /> },
      { path: 'explorer',  element: <DataExplorer /> },
      { path: 'cv',        element: <BaseCvEditor /> },

      // Job workspace — anidado, hereda el LeftNav de AppShell
      {
        path: 'jobs/:source/:jobId',
        element: <JobWorkspaceShell />,   // inyecta el Pipeline TopBar
        children: [
          { index: true,      element: <JobFlowInspector /> },  // B0
          { path: 'scrape',   element: <ScrapeDiagnostics /> }, // B1
          { path: 'extract',  element: <ExtractUnderstand /> }, // B2
          { path: 'match',    element: <Match /> },             // B3
          { path: 'sculpt',      element: <GenerateDocuments /> }, // B4
          { path: 'deployment', element: <PackageDeployment /> }, // B5
        ],
      },
    ],
  },
  // Sandbox — fuera del AppShell, sin LeftNav
  { path: '/sandbox/intelligent_editor', element: <IntelligentEditorPage /> },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
```

**Árbol de rutas:**
```
/                        → PortfolioDashboard  (A1)
/explorer                → DataExplorer         (A2)
/cv                      → BaseCvEditor         (A3)
/jobs/:source/:jobId     → JobFlowInspector     (B0)
/jobs/:source/:jobId/scrape   → ScrapeDiagnostics   (B1)
/jobs/:source/:jobId/extract  → ExtractUnderstand   (B2)
/jobs/:source/:jobId/match    → Match               (B3)
/jobs/:source/:jobId/sculpt      → GenerateDocuments   (B4)
/jobs/:source/:jobId/deployment → PackageDeployment    (B5)
/sandbox/intelligent_editor      → IntelligentEditorPage (sin shell)
```

---

## Paso 4 — Layouts

### `src/components/layouts/AppShell.tsx`

LeftNav fijo a la izquierda (w-14). Área de contenido scrolleable a la derecha.

```
┌─ LeftNav (w-14, fixed) ──┬─ main (flex-1) ───────────┐
│  [P2]                    │                            │
│  [icon] Portfolio        │   <Outlet />               │
│  [icon] Explorer         │   (PortfolioDashboard,     │
│  [icon] CV               │    DataExplorer, o         │
│                          │    JobWorkspaceShell)       │
│  ── bottom ──            │                            │
│  [icon] Sandbox          │                            │
└──────────────────────────┴────────────────────────────┘
```

```tsx
import { Outlet, NavLink } from 'react-router-dom';
import { LayoutDashboard, FolderOpen, Network, FlaskConical } from 'lucide-react';
import { cn } from '../../utils/cn';

const NAV_ITEMS = [
  { to: '/',        icon: LayoutDashboard, label: 'Portfolio', end: true },
  { to: '/explorer', icon: FolderOpen,     label: 'Explorer',  end: false },
  { to: '/cv',      icon: Network,         label: 'Base CV',   end: false },
];

export function AppShell() {
  return (
    <div className="flex min-h-screen bg-background">
      <nav className="fixed left-0 top-0 h-full w-14 bg-surface flex flex-col items-center py-4 gap-2 border-r border-outline/10 z-50">
        <div className="w-7 h-7 mb-4 border border-primary/40 flex items-center justify-center">
          <span className="text-primary font-mono text-[10px] font-bold">P2</span>
        </div>

        {NAV_ITEMS.map(({ to, icon: Icon, label, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              cn(
                'w-10 h-10 flex items-center justify-center transition-colors group relative',
                isActive ? 'text-primary tactical-glow' : 'text-on-muted hover:text-on-surface',
              )
            }
          >
            <Icon size={18} />
            <span className="absolute left-full ml-2 px-2 py-1 bg-surface-high text-on-surface text-[10px] font-mono uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-50">
              {label}
            </span>
          </NavLink>
        ))}

        <div className="mt-auto">
          <NavLink
            to="/sandbox/intelligent_editor"
            className="w-10 h-10 flex items-center justify-center text-on-muted hover:text-secondary transition-colors"
          >
            <FlaskConical size={18} />
          </NavLink>
        </div>
      </nav>

      <main className="ml-14 flex-1 min-h-screen">
        <Outlet />
      </main>
    </div>
  );
}
```

---

### `src/components/layouts/JobWorkspaceShell.tsx`

Se renderiza dentro del `<main>` de AppShell. Añade el Pipeline TopBar secundario
con las etapas del job. El `<Outlet>` escupe la vista específica (B0–B4).

```
┌─ Pipeline TopBar ──────────────────────────────────────────────────┐
│  tu_berlin / 201397     FLOW · SCRAPE · [EXTRACT] · MATCH · SCULPT │
├────────────────────────────────────────────────────────────────────┤
│  <Outlet />                                                         │
│  (JobFlowInspector, ScrapeDiagnostics, ExtractUnderstand...)        │
└────────────────────────────────────────────────────────────────────┘
```

```tsx
import { Outlet, useParams, NavLink } from 'react-router-dom';
import { ChevronRight } from 'lucide-react';
import { cn } from '../../utils/cn';

const PIPELINE_STEPS = [
  { label: 'Flow',    path: '' },
  { label: 'Scrape',  path: 'scrape' },
  { label: 'Extract', path: 'extract' },
  { label: 'Match',   path: 'match' },
  { label: 'Sculpt',  path: 'sculpt' },
];

export function JobWorkspaceShell() {
  const { source, jobId } = useParams();
  const base = `/jobs/${source}/${jobId}`;

  return (
    <div className="flex flex-col min-h-full">
      <header className="h-10 flex items-center justify-between px-4 border-b border-outline/10 bg-surface shrink-0">
        {/* Breadcrumb */}
        <div className="flex items-center gap-2 text-[11px] font-mono text-on-muted">
          <NavLink to="/" className="hover:text-primary transition-colors">Portfolio</NavLink>
          <ChevronRight size={12} />
          <span>{source}</span>
          <ChevronRight size={12} />
          <span className="text-primary">{jobId}</span>
        </div>

        {/* Pipeline step nav */}
        <nav className="flex items-center gap-1">
          {PIPELINE_STEPS.map(({ label, path }) => (
            <NavLink
              key={path}
              to={path ? `${base}/${path}` : base}
              end={path === ''}
              className={({ isActive }) =>
                cn(
                  'px-3 py-1 text-[10px] font-mono uppercase tracking-widest transition-colors',
                  isActive
                    ? 'text-primary border-b border-primary'
                    : 'text-on-muted hover:text-on-surface',
                )
              }
            >
              {label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}
```

---

## Paso 5 — Átomo: Badge

Necesario para `PortfolioTable`. Primer átomo del sistema.

```tsx
// src/components/atoms/Badge.tsx
import { cn } from '../../utils/cn';

const VARIANTS = {
  primary:   'bg-primary/15 text-primary border border-primary/30',
  secondary: 'bg-secondary/15 text-secondary border border-secondary/30',
  success:   'bg-primary/10 text-primary-dim border border-primary/20',
  danger:    'bg-error-container/20 text-error border border-error/30',
  muted:     'bg-surface-high text-on-muted border border-outline/20',
};

interface Props {
  variant?: keyof typeof VARIANTS;
  className?: string;
  children: React.ReactNode;
}

export function Badge({ variant = 'muted', className, children }: Props) {
  return (
    <span className={cn('inline-flex items-center px-2 py-0.5 text-[10px] font-mono uppercase tracking-widest', VARIANTS[variant], className)}>
      {children}
    </span>
  );
}
```

---

## Paso 6 — Feature: Portfolio

### `src/features/portfolio/api/usePortfolioSummary.ts`

```ts
import { useQuery } from '@tanstack/react-query';
import { getPortfolioSummary } from '../../../api/client';

export function usePortfolioSummary() {
  return useQuery({
    queryKey: ['portfolio', 'summary'],
    queryFn: getPortfolioSummary,
    staleTime: 60_000,
  });
}
```

### `src/features/portfolio/components/PortfolioTable.tsx`

```tsx
import { useNavigate } from 'react-router-dom';
import type { PortfolioSummary } from '../../../types/models';
import { Badge } from '../../../components/atoms/Badge';

const STATUS_VARIANT: Record<string, 'primary' | 'secondary' | 'success' | 'danger' | 'muted'> = {
  completed:    'success',
  pending_hitl: 'secondary',
  running:      'primary',
  failed:       'danger',
  archived:     'muted',
  failed:        'danger',
};

interface Props {
  data?: PortfolioSummary;
  loading: boolean;
  error: boolean;
}

export function PortfolioTable({ data, loading, error }: Props) {
  const navigate = useNavigate();

  if (loading) return <p className="text-on-muted font-mono text-sm">Loading...</p>;
  if (error)   return <p className="text-error font-mono text-sm">Failed to load portfolio.</p>;
  if (!data)   return null;

  return (
    <table className="w-full text-sm border-collapse">
      <thead>
        <tr className="text-[10px] font-mono text-on-muted uppercase tracking-widest border-b border-outline/20">
          <th className="text-left py-2 pr-6">Source / Job ID</th>
          <th className="text-left py-2 pr-6">Current Stage</th>
          <th className="text-left py-2 pr-6">Status</th>
          <th className="text-left py-2">Updated</th>
        </tr>
      </thead>
      <tbody>
        {data.jobs.map((job) => (
          <tr
            key={job.job_id}
            className="border-b border-outline/10 hover:bg-surface-low transition-colors cursor-pointer"
            onClick={() => navigate(`/jobs/${job.source}/${job.job_id}`)}
          >
            <td className="py-3 pr-6 font-mono">
              <span className="text-on-muted">{job.source} / </span>
              <span className="text-primary">{job.job_id}</span>
            </td>
            <td className="py-3 pr-6 font-mono text-on-surface">{job.current_node}</td>
            <td className="py-3 pr-6">
              <Badge variant={STATUS_VARIANT[job.status] ?? 'muted'}>{job.status}</Badge>
            </td>
            <td className="py-3 font-mono text-on-muted text-xs">{job.updated_at}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

### `src/pages/global/PortfolioDashboard.tsx`

```tsx
import { usePortfolioSummary } from '../../features/portfolio/api/usePortfolioSummary';
import { PortfolioTable } from '../../features/portfolio/components/PortfolioTable';

export function PortfolioDashboard() {
  const { data, isLoading, isError } = usePortfolioSummary();
  return (
    <div className="p-6">
      <p className="font-mono text-[10px] text-primary uppercase tracking-widest">System / PhD 2.0</p>
      <h1 className="font-headline text-xl font-bold text-on-surface mt-1 mb-6">Application Portfolio</h1>
      <PortfolioTable data={data} loading={isLoading} error={isError} />
    </div>
  );
}
```

---

## Archivos que se crean en esta fase

```
src/
  utils/
    cn.ts                                                NEW
  main.tsx                                               UPDATE — add QueryClient + providers
  App.tsx                                                UPDATE — createBrowserRouter nested
  components/
    atoms/
      Badge.tsx                                          NEW
    layouts/
      AppShell.tsx                                       NEW
      JobWorkspaceShell.tsx                              NEW
  features/
    portfolio/
      api/usePortfolioSummary.ts                         NEW
      components/PortfolioTable.tsx                      NEW
  pages/
    global/
      PortfolioDashboard.tsx                             NEW
      DataExplorer.tsx                                   STUB
      BaseCvEditor.tsx                                   STUB
    job/
      JobFlowInspector.tsx                               STUB
      ScrapeDiagnostics.tsx                              STUB
      ExtractUnderstand.tsx                              STUB
      Match.tsx                                          STUB
      GenerateDocuments.tsx                              STUB
      PackageDeployment.tsx                              STUB
```

---

## Criterios de aceptación

```
[ ] npm run dev arranca sin errores de TypeScript
[ ] / → AppShell con LeftNav oscuro (w-14, fondo #121416)
[ ] / → PortfolioTable muestra los 2 jobs del mock (201397 + 999001)
[ ] Badge status: pending_hitl=secondary(amber), completed=success(cyan-dim), running=primary
[ ] Click en fila → navega a /jobs/tu_berlin/201397
[ ] /jobs/tu_berlin/201397 → Pipeline TopBar visible con FLOW·SCRAPE·EXTRACT·MATCH·SCULPT
[ ] NavLink activo en Pipeline TopBar resalta con border-b border-primary
[ ] NavLink activo en LeftNav → tactical-glow
[ ] Tooltip del LeftNav aparece al hover
[ ] Rutas stub muestran placeholder sin crash
[ ] Sandbox /sandbox/intelligent_editor → sin LeftNav
```
