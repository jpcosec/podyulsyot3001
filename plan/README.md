# Planning Tree

This directory contains the active implementation plan for the **UI Redesign** of PhD 2.0 Review Workbench.

## What This Is

- **UI Redesign** using Atomic Design + Feature-Sliced Design + Terran Command
- Full implementation specs in `01_ui/specs/`
- Templates and guides in `01_ui/proposals/`

## Quick Start

1. Lee el spec de la vista a implementar (ej. `specs/B2_extract_understand.md`)
2. Revisa Migration Notes para saber qué extraer del branch `dev`
3. Implementa siguiendo la estructura de archivos del spec
4. Verifica Definition of Done
5. Ejecuta E2E tests
6. **Commit con formato obligatorio** (ver abajo)
7. **Agrega entrada en changelog.md**
8. **Marca [x] en index_checklist.md**

## Completion Workflow

```
spec → implement → verify DoD → E2E → commit → changelog → checklist
```

## Commit Message Format (OBLIGATORIO)

```bash
feat(ui): implement <view name> (<spec-id>)

- <component 1>
- <component 2>
...
- Connected to <hook names>
```

**No hacer commit sin seguir este formato.**

## Changelog Entry (OBLIGATORIO)

```markdown
## YYYY-MM-DD

- Implemented <spec-id> <view name>: <brief description>.
```

## Source of Truth

- **Progress:** `index_checklist.md`
- **Specs:** `01_ui/specs/`
- **Design System:** `01_ui/specs/00_design_system.md`
- **Architecture:** `01_ui/specs/00_architecture.md`
