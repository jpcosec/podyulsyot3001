# UI Redesign Plan

## Overview

This folder contains the complete implementation plan for the PhD 2.0 Review Workbench UI redesign using:
- **Atomic Design** for UI components
- **Feature-Sliced Design** for code organization
- **Terran Command** design system (dark mode, cyberpunk, cyan/amber accents)

## Structure

```
plan/01_ui/
├── specs/           # 16 specs (A1-A3, B0-B5, B3b, B4b)
├── proposals/        # Templates y guías de implementación
└── README.md        # Este archivo
```

## Specs Index

### Global Views
| Spec | View | Fase | Status |
|------|------|------|--------|
| A1 | Portfolio Dashboard | 0 | ✅ Done |
| A2 | Data Explorer | 2 | ⏳ Pending |
| A3 | Base CV Editor | 9 | ⏳ Pending |

### Job Pipeline Views
| Spec | View | Fase | Status |
|------|------|------|--------|
| B0 | Job Flow Inspector | 1 | ✅ Done |
| B1 | Scrape Diagnostics | 3 | ⏳ Pending |
| B2 | Extract & Understand | 4 | ⏳ Pending |
| B3 | Match | 5 | ⏳ Pending |
| B4 | Generate Documents | 6 | ⏳ Pending |
| B5 | Package & Deployment | 7 | ⏳ Pending |

### Blocked (Backend Required)
| Spec | View | Fase | Status |
|------|------|------|--------|
| B3b | Application Context Gate | 10 | ⚠️ BLOCKED |
| B4b | Default Document Gates | 8 | ⚠️ BLOCKED |

## Workflow Rules

### Per-Spec Completion Checklist

1. **Implementar** según spec en `specs/`
2. **Verificar** Definition of Done
3. **Ejecutar E2E** tests (TestSprite)
4. **Commit** con mensaje requerido (ver abajo)
5. **Changelog** — agregar entrada en `changelog.md`
6. **Checklist** — marcar `[x]` en `index_checklist.md`

### Commit Message Format

```bash
feat(ui): implement <view name> (<spec-id>)

- <component 1>
- <component 2>
...
- Connected to <hook names>
```

### Changelog Entry Format

```markdown
## YYYY-MM-DD

- Implemented <spec-id> <view name>: <brief description>.
```

## Key Resources

- **Agent Prompt Template:** `proposals/migration_agent_prompt.md`
- **Component Templates:** `proposals/component_templates.md`
- **Phase 0 Plan:** `proposals/phase_0_foundation.md`
- **Design System:** `specs/00_design_system.md`
- **Architecture:** `specs/00_architecture.md`
- **Component Map:** `specs/00_component_map.md`
- **Stack Reference:** `specs/00_stack.md`
- **Pipeline Reference:** `specs/00_pipeline_reference.md`

## Migration Guide

### From dev branch

Cada spec tiene una sección **Migration Notes** que indica:
- Legacy source path en branch `dev`
- Legacy components a extraer
- Hook de API a usar

### Steps

1. Leer spec completo
2. Revisar legacy source en branch `dev`
3. Extraer shape de JSON de fixtures en `mock/fixtures/`
4. Crear componentes en `features/<feature>/`
5. Conectar via hooks de React Query
6. Aplicar estética Terran Command
7. Seguir anti-patrones de `component_templates.md`

## Stack

- **Framework:** React 18 + TypeScript
- **Styling:** Tailwind CSS (Terran Command tokens)
- **Data:** @tanstack/react-query
- **Routing:** react-router-dom v6
- **Icons:** lucide-react
- **Code Editor:** @uiw/react-codemirror
- **Graph:** @xyflow/react + @dagrejs/dagre
- **DnD:** @dnd-kit/core
- **Layout:** react-resizable-panels
- **Testing:** Vitest + RTL + TestSprite
