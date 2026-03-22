# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working on the UI redesign.

## Primeros Pasos

1. **Leer el plan:** `plan/README.md` y `plan/index_checklist.md`
2. **Elegir spec:** buscar en `plan/01_ui/specs/` la fase actual
3. **Revisar Migration Notes:** cada spec indica qué extraer del branch `dev`
4. **Implementar:** seguir estructura de archivos del spec
5. **Cerrar fase:** commit + changelog + checklist (obligatorio)

## Commands

```bash
# Frontend development
cd apps/review-workbench
npm run dev          # con VITE_MOCK=true por defecto

# Con API real (mock=false)
VITE_MOCK=false npm run dev

# Tests
cd apps/review-workbench && npm test
```

## Workflow

```
plan/01_ui/specs/<spec>.md
    ↓
Migration Notes (legacy source en dev)
    ↓
Implementar componentes en features/
    ↓
Verificar Definition of Done
    ↓
E2E Tests
    ↓
COMMIT (formato obligatorio)
    ↓
CHANGELOG + CHECKLIST
```

## Estructura del Frontend

```
apps/review-workbench/src/
├── api/                    # Cliente API (mock o real)
│   └── client.ts          # Toggle: VITE_MOCK=true/false
├── mock/                  # Mock API con fixtures
│   ├── client.ts         # Mock implementation
│   └── fixtures/         # 32 JSON fixtures
├── features/              # Feature-Sliced (negocio)
│   ├── portfolio/
│   │   ├── api/usePortfolioSummary.ts
│   │   └── components/PortfolioTable.tsx
│   └── job-pipeline/
│       ├── api/useJobTimeline.ts
│       └── components/
├── components/            # Diseño Atómico
│   ├── atoms/            # Button, Badge, Tag, Icon, Spinner, Kbd
│   ├── molecules/        # SplitPane, ControlPanel
│   └── layouts/          # AppShell, JobWorkspaceShell
├── pages/
│   ├── global/          # PortfolioDashboard, DataExplorer, BaseCvEditor
│   └── job/             # JobFlowInspector, ExtractUnderstand, Match...
└── types/
    └── api.types.ts     # Contratos TypeScript
```

## Stack

- React 18 + TypeScript
- Tailwind CSS (Terran Command tokens)
- @tanstack/react-query
- react-router-dom v6
- lucide-react
- @uiw/react-codemirror
- @xyflow/react + @dagrejs/dagre
- @dnd-kit/core
- react-resizable-panels

## Key Resources

- **Specs:** `plan/01_ui/specs/`
- **Design System:** `plan/01_ui/specs/00_design_system.md`
- **Component Templates:** `plan/01_ui/proposals/component_templates.md`
- **Migration Guide:** `plan/01_ui/proposals/migration_agent_prompt.md`

## Progreso Actual

Fase 0 y Fase 1 completadas (Foundation + JobFlowInspector).  
Ver: `plan/index_checklist.md`

## Reglas

1. **No hardcoded data** — todo del mock/API
2. **Pages tontas** — solo useParams + hook + render
3. **Lógica en features/** — nunca en pages/
4. **cn()** para toda composición de clases Tailwind
5. **Commit obligatorio** al cerrar fase — formato en `plan/README.md`
