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
    queries: {
      staleTime: 30_000,
      retry: 1,
    },
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

```tsx
import { createBrowserRouter, RouterProvider } from 'react-router-dom';
import { AppShell } from './components/layouts/AppShell';
import { JobWorkspaceShell } from './components/layouts/JobWorkspaceShell';
import { PortfolioPage } from './pages/global/PortfolioPage';
import { DataExplorerPage } from './pages/global/DataExplorerPage';
import { CvEditorPage } from './pages/global/CvEditorPage';
import { JobFlowPage } from './pages/job/JobFlowPage';
import { ExtractPage } from './pages/job/ExtractPage';
import { MatchPage } from './pages/job/MatchPage';
import { DocumentsPage } from './pages/job/DocumentsPage';
import { IntelligentEditorPage } from './sandbox/pages/IntelligentEditorPage';

const router = createBrowserRouter([
  {
    element: <AppShell />,           // LeftNav + fondo oscuro
    children: [
      { path: '/',         element: <PortfolioPage /> },
      { path: '/explorer', element: <DataExplorerPage /> },
      { path: '/cv',       element: <CvEditorPage /> },
    ],
  },
  {
    path: '/jobs/:source/:jobId',
    element: <JobWorkspaceShell />,  // LeftNav + job breadcrumb + status sidebar
    children: [
      { index: true,            element: <JobFlowPage /> },
      { path: 'extract',        element: <ExtractPage /> },
      { path: 'match',          element: <MatchPage /> },
      { path: 'documents',      element: <DocumentsPage /> },
    ],
  },
  // Sandbox — sin shell
  { path: '/sandbox/intelligent_editor', element: <IntelligentEditorPage /> },
]);

export default function App() {
  return <RouterProvider router={router} />;
}
```

**Por qué `createBrowserRouter` en lugar de `<BrowserRouter>`:**
- Permite loaders y actions (React Router v6.4+) para pre-fetch en la navegación
- El layout nesting es explícito y estático — más fácil de leer
- Habilita `useRouteError` para error boundaries por ruta

---

## Paso 4 — Layouts (cascarones)

### `src/components/layouts/AppShell.tsx`

Shell global: LeftNav fijo a la izquierda + área de contenido scrolleable.

```
┌──────────────────────────────────────────────────────┐
│ LeftNav (w-14, fixed, bg-background)                  │
│  [logo]                                               │
│  [icon: portfolio]  ← activo si path='/'              │
│  [icon: explorer]   ← activo si path='/explorer'      │
│  [icon: cv]         ← activo si path='/cv'            │
│  ──────────────────                                   │
│  [icon: sandbox]    ← bottom                          │
├──────────────────────────────────────────────────────┤
│ <main> (ml-14, min-h-screen, bg-background)           │
│   <Outlet />                                          │
└──────────────────────────────────────────────────────┘
```

```tsx
// src/components/layouts/AppShell.tsx
import { Outlet, NavLink } from 'react-router-dom';
import { LayoutDashboard, FolderOpen, Network, FlaskConical } from 'lucide-react';
import { cn } from '../../utils/cn';

const NAV_ITEMS = [
  { to: '/',         icon: LayoutDashboard, label: 'Portfolio' },
  { to: '/explorer', icon: FolderOpen,      label: 'Explorer'  },
  { to: '/cv',       icon: Network,         label: 'Base CV'   },
];

export function AppShell() {
  return (
    <div className="flex min-h-screen bg-background">
      <nav className="fixed left-0 top-0 h-full w-14 bg-surface flex flex-col items-center py-4 gap-2 border-r border-outline/10 z-50">
        {/* Logo mark */}
        <div className="w-7 h-7 mb-4 border border-primary/40 flex items-center justify-center">
          <span className="text-primary font-mono text-[10px] font-bold">P2</span>
        </div>

        {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            end={to === '/'}
            className={({ isActive }) =>
              cn(
                'w-10 h-10 flex items-center justify-center transition-colors group relative',
                isActive
                  ? 'text-primary tactical-glow'
                  : 'text-on-muted hover:text-on-surface',
              )
            }
          >
            <Icon size={18} />
            {/* Tooltip */}
            <span className="absolute left-full ml-2 px-2 py-1 bg-surface-high text-on-surface text-[10px] font-mono uppercase tracking-widest opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none">
              {label}
            </span>
          </NavLink>
        ))}

        {/* Bottom: sandbox link */}
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

Shell de job: hereda el LeftNav de AppShell + añade breadcrumb del job arriba
y un status sidebar colapsable a la derecha (para la fase siguiente).

```
┌─ LeftNav (w-14) ─┬─ JobBreadcrumb ─────────────────────────────────┐
│                  │ tu_berlin / 201397 / review_match  [status pill] │
│                  ├─────────────────────────────────────────────────  │
│                  │  <Outlet />   (el contenido de la vista actual)   │
└──────────────────┴─────────────────────────────────────────────────  ┘
```

```tsx
// src/components/layouts/JobWorkspaceShell.tsx
import { Outlet, useParams, NavLink } from 'react-router-dom';
import { AppShell } from './AppShell';        // reutiliza el LeftNav
import { ChevronRight } from 'lucide-react';

export function JobWorkspaceShell() {
  const { source, jobId } = useParams();

  return (
    // JobWorkspaceShell es un <AppShell> con contenido adicional arriba del Outlet
    // Alternativa: repetir el LeftNav inline y no heredar de AppShell.
    // Decisión pendiente según cómo quede el anidamiento de rutas.
    <div className="flex min-h-screen bg-background ml-14">
      {/* Breadcrumb de job */}
      <div className="flex flex-col flex-1">
        <header className="h-10 flex items-center gap-2 px-4 border-b border-outline/10 bg-surface text-[11px] font-mono text-on-muted">
          <NavLink to="/" className="hover:text-primary transition-colors">Portfolio</NavLink>
          <ChevronRight size={12} />
          <span className="text-on-surface">{source}</span>
          <ChevronRight size={12} />
          <span className="text-primary">{jobId}</span>
        </header>
        <main className="flex-1">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
```

> **Duda de diseño:** ¿`JobWorkspaceShell` anida dentro de `AppShell` (reutilizando el LeftNav)
> o tiene su propio LeftNav? En el router actual están como rutas separadas — si se quiere
> el mismo LeftNav en ambos, hay que hacer `AppShell` como layout raíz y anidar ambos grupos
> dentro de él. Resolver antes de implementar.

---

## Paso 5 — Feature: Portfolio

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

### `src/pages/global/PortfolioPage.tsx` (página tonta)

```tsx
import { usePortfolioSummary } from '../../features/portfolio/api/usePortfolioSummary';
import { PortfolioTable } from '../../features/portfolio/components/PortfolioTable';

export function PortfolioPage() {
  const { data, isLoading, isError } = usePortfolioSummary();
  return (
    <div className="p-6">
      <header className="mb-6">
        <p className="font-mono text-[10px] text-primary uppercase tracking-widest">System / PhD 2.0</p>
        <h1 className="font-headline text-xl font-bold text-on-surface mt-1">Application Portfolio</h1>
      </header>
      <PortfolioTable data={data} loading={isLoading} error={isError} />
    </div>
  );
}
```

### `src/features/portfolio/components/PortfolioTable.tsx` (esqueleto)

```tsx
import type { PortfolioSummary } from '../../../types/models';
import { Badge } from '../../../components/atoms/Badge';

interface Props {
  data?: PortfolioSummary;
  loading: boolean;
  error: boolean;
}

export function PortfolioTable({ data, loading, error }: Props) {
  if (loading) return <div className="text-on-muted font-mono text-sm">Loading...</div>;
  if (error)   return <div className="text-error font-mono text-sm">Failed to load portfolio.</div>;
  if (!data)   return null;

  return (
    <table className="w-full text-sm font-mono border-collapse">
      <thead>
        <tr className="text-[10px] text-on-muted uppercase tracking-widest border-b border-outline/20">
          <th className="text-left py-2 pr-4">Source / Job ID</th>
          <th className="text-left py-2 pr-4">Current Stage</th>
          <th className="text-left py-2 pr-4">Status</th>
          <th className="text-left py-2">Updated</th>
        </tr>
      </thead>
      <tbody>
        {data.jobs.map((job) => (
          <tr key={job.job_id} className="border-b border-outline/10 hover:bg-surface-low transition-colors">
            <td className="py-3 pr-4">
              <span className="text-on-muted">{job.source} / </span>
              <span className="text-primary">{job.job_id}</span>
            </td>
            <td className="py-3 pr-4 text-on-surface">{job.current_node}</td>
            <td className="py-3 pr-4">
              <Badge variant={job.status === 'completed' ? 'success' : job.status === 'paused_review' ? 'secondary' : 'muted'}>
                {job.status}
              </Badge>
            </td>
            <td className="py-3 text-on-muted">{job.updated_at}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
```

---

## Archivos que se crean en esta fase

```
src/
  utils/cn.ts                                          NEW
  main.tsx                                             UPDATE (add QueryClient)
  App.tsx                                              UPDATE (createBrowserRouter)
  components/
    atoms/
      Badge.tsx                                        NEW (necesario para PortfolioTable)
    layouts/
      AppShell.tsx                                     NEW
      JobWorkspaceShell.tsx                            NEW
  features/
    portfolio/
      api/usePortfolioSummary.ts                       NEW
      components/PortfolioTable.tsx                    NEW
  pages/
    global/
      PortfolioPage.tsx                                NEW
      DataExplorerPage.tsx                             STUB (solo placeholder)
      CvEditorPage.tsx                                 STUB
    job/
      JobFlowPage.tsx                                  STUB
      ExtractPage.tsx                                  STUB
      MatchPage.tsx                                    STUB
      DocumentsPage.tsx                                STUB
```

---

## Criterios de aceptación

```
[ ] npm run dev arranca sin errores de TypeScript
[ ] / → AppShell visible (LeftNav oscuro, fondo #0c0e10)
[ ] / → PortfolioTable muestra los 2 jobs del mock (201397 + 999001)
[ ] Badge de status renderiza con color correcto (cyan=paused, green=completed)
[ ] NavLink activo en LeftNav → icon con tactical-glow
[ ] /jobs/tu_berlin/201397 → JobWorkspaceShell con breadcrumb correcto
[ ] Rutas desconocidas → no crash (404 handler pendiente)
[ ] Tooltips del LeftNav aparecen al hover
[ ] VITE_MOCK=false → el fetch falla gracefully (no crash de import)
```

---

## Dudas abiertas

1. **LeftNav duplicado:** ¿`JobWorkspaceShell` hereda `AppShell` o tiene su propio nav?
   Si se decide heredar, el router necesita un layout raíz único que envuelva todo.
2. **Stub pages:** ¿Qué muestran las stubs? ¿`"Coming soon"` o un placeholder con el nombre de la vista?
3. **Badge variants:** ¿`success/secondary/muted` son suficientes para todos los `StageStatus`, o se necesita un `danger` también?
4. **`PortfolioSummary.jobs` shape:** Verificar que el mock fixture tiene el campo `jobs[]` con la forma que espera `PortfolioTable` antes de implementar.
