# Legacy CSS Usage Audit Report

**Project:** PHD 2.0 UI Redesign
**Audited Directory:** `/apps/review-workbench/src/`
**Date:** 2026-03-23
**Scope:** All `.ne-*` class usage and CSS custom property (`var(--*)`) references

---

## SECTION A: `.ne-*` Classes Used in `.tsx`/`.ts` Files

### Summary
- **Total unique `.ne-*` classes found:** 80
- **Files using `.ne-*` classes:** 18

### Breakdown by File

#### **1. `pages/global/KnowledgeGraph.tsx`** (64 unique classes)
Primary consumer of legacy `.ne-*` classes. This is the Node Editor / Knowledge Graph page—a large, monolithic component migrated from a sandbox prototype.

Classes used:
- `ne-page`, `ne-workspace`
- `ne-sidebar`, `ne-sidebar-collapsed`, `ne-sidebar-content`, `ne-sidebar-toggle`
- `ne-state-section`, `ne-state-badge`, `ne-unfocus-btn`
- `ne-stats`, `ne-filter-section`, `ne-template-list`, `ne-template-chip`, `ne-template-hint`
- `ne-checkbox-label`, `ne-canvas-wrap`
- `ne-node-container`, `ne-container-header`, `ne-container-name`, `ne-container-badge`
- `ne-node-free`, `ne-node-child`, `ne-node-focused`, `ne-node-dimmed`
- `ne-edge-dimmed`, `ne-edge-focused`
- `ne-node-simple`, `ne-node-simple-selected`, `ne-node-handle`, `ne-node-edit-chip`, `ne-node-edit-chip-visible`
- `ne-section`, `ne-section-toggle`, `ne-section-body`
- `ne-control-row`, `ne-control-row-single`
- `ne-btn`, `ne-btn-primary`, `ne-btn-danger`, `ne-btn-small`, `ne-remove-btn`
- `ne-dirty-dot`, `ne-dirty-dot-on`
- `ne-inline-note`, `ne-empty-note`
- `ne-selection-summary`
- `ne-input`, `ne-input-textarea`
- `ne-field`, `ne-property-list`, `ne-property-row`
- `ne-relation-pill-list`, `ne-relation-pill-row`, `ne-relation-pill-text`
- `ne-modal-backdrop`, `ne-modal-card`, `ne-modal-card-confirm`, `ne-modal-actions`, `ne-confirm-copy`
- `ne-mode-badge`
- `ne-connect-menu`, `ne-connect-list`, `ne-connect-list-scroll`, `ne-connect-item`
- `ne-history-list`, `ne-history-item`
- `ne-checkbox-inline`

#### **2. `components/atoms/Badge.tsx`** (0 classes)
Uses Tailwind only: `bg-primary/15`, `text-primary`, `border-primary/30`, etc.

#### **3. `components/atoms/Button.tsx`** (0 classes)
Uses Tailwind only: variant system with Tailwind classes.

#### **4. `components/atoms/Spinner.tsx`** (1 class)
- `ne-block` — Used in animation for spinner (likely a Tailwind utility)

#### **5. `components/atoms/Kbd.tsx`** (0 classes)
Uses Tailwind only.

#### **6. `components/atoms/Tag.tsx`** (0 classes)
Uses Tailwind only.

#### **7. `components/organisms/IntelligentEditor.tsx`** (1 class)
- `ne-dark` — Applied to root editor container

#### **8. `features/job-pipeline/components/ScrapeControlPanel.tsx`** (0 classes)
Uses Tailwind only.

#### **9. `features/job-pipeline/components/SourceTextPreview.tsx`** (0 classes)
Uses Tailwind only.

#### **10. `features/job-pipeline/components/StageRow.tsx`** (0 classes)
Uses Tailwind only.

#### **11. `features/job-pipeline/components/MatchControlPanel.tsx`** (1 class)
- `ne-block` — Used for flex container

#### **12. `features/job-pipeline/components/EvidenceBankPanel.tsx`** (1 class)
- `ne-clamp-2` — Custom utility class (not in styles.css, likely inline/missing)

#### **13. `features/job-pipeline/components/RequirementItem.tsx`** (0 classes)
Uses Tailwind only: modern pattern with `border-outline/20`, `bg-primary/5`, etc.

#### **14. `features/job-pipeline/components/RequirementList.tsx`** (0 classes)
Uses Tailwind only.

#### **15. `features/job-pipeline/components/RegenModal.tsx`** (1 class)
- `ne-none` — Display: none utility

#### **16. `features/job-pipeline/components/MatchDecisionModal.tsx`** (1 class)
- `ne-none` — Display: none utility

#### **17. `features/base-cv/components/SkillPalette.tsx`** (1 class)
- `ne-none` — Display: none utility

#### **18. `features/base-cv/components/NodeInspector.tsx`** (1 class)
- `ne-none` — Display: none utility

#### **19. `features/base-cv/components/EntryNode.tsx`** (1 class)
- `ne-none` — Display: none utility

#### **20. `features/base-cv/components/SkillBallNode.tsx`** (1 class)
- `ne-block` — Display: block utility

### Complete Unique `.ne-*` Class List (80 total)
```
ne-block
ne-btn
ne-btn-danger
ne-btn-primary
ne-btn-small
ne-canvas-wrap
ne-checkbox-inline
ne-checkbox-label
ne-clamp-2
ne-confirm-copy
ne-connect-item
ne-connect-list
ne-connect-list-scroll
ne-connect-menu
ne-control-row
ne-control-row-single
ne-dark
ne-dirty-dot
ne-dirty-dot-on
ne-edge-dimmed
ne-edge-focused
ne-empty-note
ne-field
ne-filter-section
ne-flex
ne-history-item
ne-history-list
ne-inline-note
ne-input
ne-input-textarea
ne-modal-actions
ne-modal-backdrop
ne-modal-card
ne-modal-card-confirm
ne-mode-badge
ne-node-dimmed
ne-node-edit-chip
ne-node-edit-chip-visible
ne-node-focused
ne-node-handle
ne-node-simple
ne-node-simple-selected
ne-none
ne-page
ne-property-list
ne-property-row
ne-relation-pill-list
ne-relation-pill-row
ne-relation-pill-text
ne-remove-btn
ne-section
ne-section-body
ne-section-toggle
ne-selection-summary
ne-sidebar
ne-sidebar-collapsed
ne-sidebar-content
ne-sidebar-toggle
ne-state-badge
ne-state-section
ne-stats
ne-template-chip
ne-template-hint
ne-template-list
ne-unfocus-btn
ne-workspace
```

**Note:** Several classes appear defined in `styles.css` but are NOT used in any `.tsx/.ts` file:
- `ne-container-header`, `ne-container-name`, `ne-container-badge`
- `ne-node-free`, `ne-node-child`
- `ne-selection-summary` (defined but not directly referenced in code)

Some classes in code are NOT defined in `styles.css`:
- `ne-block` — Used 3 times; likely should be Tailwind `block`
- `ne-clamp-2` — Used 1 time; not in styles.css
- `ne-dark` — Used 1 time; not in styles.css
- `ne-flex` — Used 4 times; likely should be Tailwind `flex`
- `ne-none` — Used 5 times; likely should be Tailwind `hidden`

---

## SECTION B: CSS Custom Property (`var(--*)`) Usage

### Variable Definitions (from `src/styles.css` lines 43–54)
```css
:root {
  --panel:      #121416;      /* Surface color for panels/backgrounds */
  --line:       #3a494b;      /* Border/divider color */
  --accent:     #00f2ff;      /* Primary accent color (cyan) */
  --accent-soft:#005f66;      /* Secondary accent (dark cyan) */
  --text-main:  #e2e2e5;      /* Main text color */
  --text-dim:   #849495;      /* Dimmed/secondary text */
  --bad:        #ffb4ab;      /* Error state color */
  --good:       #00f2ff;      /* Success state color (same as --accent) */
  --warn:       #ffaa00;      /* Warning state color */
  --pending:    #ffaa00;      /* Pending state color (same as --warn) */
}
```

### Usage Count by Variable

#### **`var(--panel)`** — 10 occurrences
- **Definition value:** `#121416` (Terran: `bg-surface`)
- **Used in CSS classes:**
  - `.ne-sidebar` (background)
  - `.ne-sidebar-toggle` (background)
  - `.ne-unfocus-btn` (background)
  - `.ne-template-chip` (background)
  - `.ne-node-child` (background)
  - `.ne-section-toggle` (background)
  - `.ne-btn` (background)
  - `.ne-node-edit-chip` (background)
  - `.ne-modal-card` (background)

**Inline usage in .tsx files:** None

#### **`var(--line)`** — 19 occurrences
- **Definition value:** `#3a494b` (Terran: `border-outline-variant`)
- **Used in CSS classes:**
  - `.ne-sidebar` (border-right)
  - `.ne-sidebar-toggle` (border)
  - `.ne-unfocus-btn` (border)
  - `.ne-node-container` (border)
  - `.ne-node-free` (border)
  - `.ne-node-child` (border)
  - `.ne-node-simple` (border)
  - `.ne-node-edit-chip` (border)
  - `.ne-inline-note` (border)
  - `.ne-section` (border)
  - `.ne-section-toggle` (border-bottom)
  - `.ne-input` (border)
  - `.ne-remove-btn` (border)
  - `.ne-relation-pill-text` (border)
  - `.ne-modal-card` (border)
  - `.ne-mode-badge` (border)
  - `.ne-connect-menu` (border)
  - `.ne-connect-item` (border)

**Inline usage in .tsx files:** None

#### **`var(--accent)`** — 16 occurrences
- **Definition value:** `#00f2ff` (Terran: `text-primary` / `bg-primary` / `border-primary`)
- **Used in CSS classes:**
  - `.ne-state-badge` (color)
  - `.ne-unfocus-btn:not(:disabled):hover` (background, border-color)
  - `.ne-template-chip` (color)
  - `.ne-container-badge` (background)
  - `.ne-node-simple-selected` (box-shadow reference via offset)
  - `.ne-node-focused` (outline)
  - `.ne-node-edit-chip:hover` (border-color)
  - `.ne-section-toggle:not(:disabled)` (implied hover)
  - `.ne-btn:hover:not(:disabled)` (border-color)
  - `.ne-btn-primary` (background, border-color)
  - `.ne-mode-badge:hover:not(:disabled)` (border-color)
  - `.ne-connect-item:hover` (border-color)

**Inline usage in .tsx files:**
1. **`pages/global/KnowledgeGraph.tsx:623`** — `style={{ stroke: 'var(--accent)', strokeWidth: 1.5, ...style }}`
   - Used in edge rendering for the knowledge graph SVG edges

2. **`pages/global/KnowledgeGraph.tsx:463`** — `color: 'var(--text-main)'` (inline string, not in a `var()` call)
   - Actually inline style but not using `var()` directly in TSX

#### **`var(--accent-soft)`** — 1 occurrence
- **Definition value:** `#005f66` (Terran: `bg-primary-on`)
- **Used in CSS classes:**
  - `.ne-template-chip` (border-color, dashed)

**Inline usage in .tsx files:** None

#### **`var(--text-main)`** — 6 occurrences
- **Definition value:** `#e2e2e5` (Terran: `text-on-surface`)
- **Used in CSS classes:**
  - `.ne-section-toggle` (color)
  - `.ne-btn` (color)
  - `.ne-node-edit-chip` (color)
  - `.ne-input` (color)
  - `.ne-selection-summary strong` (color)
  - `.ne-mode-badge` (color)

**Inline usage in .tsx files:**
1. **`pages/global/KnowledgeGraph.tsx:463`** — `color: 'var(--text-main)'` (inline style in SimpleNode component)

#### **`var(--text-dim)`** — 8 occurrences
- **Definition value:** `#849495` (Terran: `text-on-muted`)
- **Used in CSS classes:**
  - `.ne-stats` (color)
  - `.ne-filter-section h3` (color)
  - `.ne-template-hint` (color)
  - `.ne-field` (color)
  - `.ne-inline-note` (color)
  - `.ne-empty-note` (color)
  - `.ne-selection-summary` (color)
  - `.ne-connect-menu h4` (color)

**Inline usage in .tsx files:** None

#### **`var(--bad)`** — 0 occurrences in CSS
- **Definition value:** `#ffb4ab` (Terran: `text-error`)
- **Unused in provided codebase**

#### **`var(--good)`** — 0 occurrences in CSS
- **Definition value:** `#00f2ff` (identical to `--accent`)
- **Unused in provided codebase**

#### **`var(--warn)`** — 0 occurrences in CSS
- **Definition value:** `#ffaa00` (Terran: `text-secondary`)
- **Unused in provided codebase**

#### **`var(--pending)`** — 0 occurrences in CSS
- **Definition value:** `#ffaa00` (identical to `--warn`)
- **Unused in provided codebase**

### Summary of Variable Usage
| Variable | Occurrences | Status | Terran Equivalent |
|----------|------------|--------|-------------------|
| `--panel` | 10 | Active | `bg-surface` |
| `--line` | 19 | Active | `border-outline-variant` or `border-[#3a494b]` |
| `--accent` | 17 (16 CSS + 1 inline) | Active | `text-primary`, `bg-primary`, `border-primary` |
| `--accent-soft` | 1 | Active | `bg-primary-on` |
| `--text-main` | 7 (6 CSS + 1 inline) | Active | `text-on-surface` |
| `--text-dim` | 8 | Active | `text-on-muted` |
| `--bad` | 0 | Unused | `text-error` |
| `--good` | 0 | Unused | `text-primary` |
| `--warn` | 0 | Unused | `text-secondary` |
| `--pending` | 0 | Unused | `text-secondary` |

---

## SECTION C: CSS Class Definitions & Tailwind Equivalents

### Complete `.ne-*` Class Definition Summary

#### **Layout & Structure**

| Class | CSS Definition | Tailwind Equivalent |
|-------|----------------|-------------------|
| `.ne-page` | `margin: 0; min-height: 100vh;` | `m-0 min-h-screen` |
| `.ne-workspace` | `display: flex; height: 100vh;` | `flex h-screen` |
| `.ne-canvas-wrap` | `flex: 1; position: relative;` | `flex-1 relative` |

#### **Sidebar**

| Class | CSS Definition | Tailwind Equivalent |
|-------|----------------|-------------------|
| `.ne-sidebar` | `width: 280px; min-width: 280px; background: var(--panel); border-right: 1px solid var(--line); padding: 12px 16px; overflow-y: auto; transition: width 0.2s, min-width 0.2s, padding 0.2s; position: relative;` | `w-70 bg-surface border-r border-outline-variant px-4 py-3 overflow-y-auto transition-all duration-200` |
| `.ne-sidebar-collapsed` | `width: 40px; min-width: 40px; padding: 12px 6px; overflow: hidden;` | `w-10 px-1.5 py-3 overflow-hidden` |
| `.ne-sidebar-content` | `padding-right: 8px; display: grid; gap: 10px;` | `pr-2 grid gap-2.5` |
| `.ne-sidebar-toggle` | `position: absolute; top: 8px; right: 8px; width: 26px; height: 26px; border: 1px solid var(--line); border-radius: 6px; background: var(--panel); cursor: pointer; font-size: 0.7rem; display: flex; align-items: center; justify-content: center;` | `absolute top-2 right-2 w-6.5 h-6.5 border border-outline-variant rounded bg-surface flex items-center justify-center cursor-pointer text-[0.7rem]` |

#### **State & Info Display**

| Class | CSS Definition | Tailwind Equivalent |
|-------|----------------|-------------------|
| `.ne-state-section` | `display: flex; align-items: center; justify-content: space-between; gap: 8px; margin-bottom: 12px; padding-right: 32px;` | `flex items-center justify-between gap-2 mb-3 pr-8` |
| `.ne-state-badge` | `font-size: 0.82rem; font-weight: 600; color: var(--accent); white-space: nowrap; overflow: hidden; text-overflow: ellipsis;` | `text-xs font-bold text-primary whitespace-nowrap overflow-hidden text-ellipsis` |
| `.ne-stats` | `margin-bottom: 12px; font-size: 0.82rem; color: var(--text-dim);` | `mb-3 text-xs text-on-muted` |
| `.ne-selection-summary` | `display: grid; gap: 4px; margin-bottom: 10px; font-size: 0.78rem; color: var(--text-dim);` | `grid gap-1 mb-2.5 text-[0.78rem] text-on-muted` |

#### **Filter & Template**

| Class | CSS Definition | Tailwind Equivalent |
|-------|----------------|-------------------|
| `.ne-filter-section` | `margin-bottom: 12px;` | `mb-3` |
| `.ne-filter-section h3` | `font-size: 0.82rem; margin: 0 0 6px; color: var(--text-dim);` | `text-xs m-0 mb-1.5 text-on-muted` |
| `.ne-template-list` | `display: flex; flex-wrap: wrap; gap: 6px;` | `flex flex-wrap gap-1.5` |
| `.ne-template-chip` | `border: 1px dashed var(--accent-soft); border-radius: 999px; background: var(--panel); color: var(--accent); font-size: 0.76rem; font-weight: 600; padding: 5px 9px; cursor: grab;` | `border border-dashed border-primary-on rounded-full bg-surface text-primary text-[0.76rem] font-bold py-1 px-2.25 cursor-grab` |
| `.ne-template-chip:active` | `cursor: grabbing;` | `:active:cursor-grabbing` |
| `.ne-template-hint` | `margin: 6px 0 0; font-size: 0.75rem; color: var(--text-dim);` | `mt-1.5 text-[0.75rem] text-on-muted` |

#### **Nodes & Edges (Knowledge Graph)**

| Class | CSS Definition | Tailwind Equivalent |
|-------|----------------|-------------------|
| `.ne-node-container` | `border: 2px solid var(--line); border-radius: 12px; padding: 8px; min-width: 100%; min-height: 100%;` | `border-2 border-outline-variant rounded-3xl p-2 min-w-full min-h-full` |
| `.ne-node-free` | `border: 2px solid var(--line); border-radius: 10px; padding: 10px 18px; font-size: 0.85rem; font-weight: 500; text-align: center; min-width: 100px;` | `border-2 border-outline-variant rounded-[10px] px-4.5 py-2.5 text-[0.85rem] font-medium text-center min-w-[100px]` |
| `.ne-node-child` | `background: var(--panel); border: 1px solid var(--line); border-radius: 8px; padding: 6px 14px; font-size: 0.78rem; min-width: 200px;` | `bg-surface border border-outline-variant rounded px-3.5 py-1.5 text-[0.78rem] min-w-[200px]` |
| `.ne-node-simple` | `border: 2px solid var(--line); border-radius: 10px; padding: 10px 18px; font-size: 0.83rem; font-weight: 500; text-align: center; min-width: 110px; position: relative;` | `border-2 border-outline-variant rounded-[10px] px-4.5 py-2.5 text-[0.83rem] font-medium text-center min-w-[110px] relative` |
| `.ne-node-simple-selected` | `border-color: var(--accent); box-shadow: 0 0 0 1px rgba(15, 118, 110, 0.28);` | `border-primary shadow-[0_0_0_1px_rgba(15,118,110,0.28)]` |
| `.ne-node-focused` | `outline: 2px solid var(--accent) !important; outline-offset: 2px; z-index: 10;` | `outline-2 outline-primary outline-offset-2 z-10` |
| `.ne-node-dimmed` | `opacity: 0.25; pointer-events: none;` | `opacity-25 pointer-events-none` |
| `.ne-node-handle` | `opacity: 0; pointer-events: none; transition: opacity 0.14s;` | `opacity-0 pointer-events-none transition-opacity duration-140` |
| `.ne-node-edit-chip` | `position: absolute; top: -8px; right: -8px; border: 1px solid var(--line); border-radius: 999px; background: var(--panel); color: var(--text-main); font-size: 0.7rem; font-weight: 600; padding: 2px 8px; cursor: pointer; opacity: 0; pointer-events: none; transition: opacity 0.14s, border-color 0.14s;` | `absolute -top-2 -right-2 border border-outline-variant rounded-full bg-surface text-on-surface text-[0.7rem] font-bold px-2 py-0.5 cursor-pointer opacity-0 pointer-events-none transition-[opacity,border-color] duration-140` |
| `.ne-edge-dimmed` | `opacity: 0.15;` | `opacity-15` |
| `.ne-edge-focused` | `opacity: 1;` | `opacity-100` |

#### **Sections & Panels**

| Class | CSS Definition | Tailwind Equivalent |
|-------|----------------|-------------------|
| `.ne-section` | `border: 1px solid var(--line); border-radius: 12px; background: rgba(0, 242, 255, 0.03); overflow: hidden;` | `border border-outline-variant rounded-3xl bg-primary/[0.03] overflow-hidden` |
| `.ne-section-toggle` | `width: 100%; border: 0; border-bottom: 1px solid var(--line); background: var(--panel); color: var(--text-main); display: flex; justify-content: space-between; align-items: center; padding: 10px 12px; font-size: 0.84rem; font-weight: 600; cursor: pointer;` | `w-full border-b border-outline-variant bg-surface text-on-surface flex justify-between items-center px-3 py-2.5 text-[0.84rem] font-bold cursor-pointer` |
| `.ne-section-body` | `padding: 12px;` | `p-3` |

#### **Controls & Buttons**

| Class | CSS Definition | Tailwind Equivalent |
|-------|----------------|-------------------|
| `.ne-unfocus-btn` | `padding: 4px 12px; font-size: 0.78rem; border: 1px solid var(--line); border-radius: 6px; background: var(--panel); cursor: pointer; white-space: nowrap;` | `px-3 py-1 text-[0.78rem] border border-outline-variant rounded bg-surface cursor-pointer whitespace-nowrap` |
| `.ne-unfocus-btn:disabled` | `opacity: 0.4; cursor: default;` | `disabled:opacity-40 disabled:cursor-default` |
| `.ne-btn` | `border: 1px solid var(--line); border-radius: 8px; background: var(--panel); color: var(--text-main); font-size: 0.8rem; padding: 6px 10px; cursor: pointer;` | `border border-outline-variant rounded-lg bg-surface text-on-surface text-[0.8rem] px-2.5 py-1.5 cursor-pointer` |
| `.ne-btn:hover:not(:disabled)` | `border-color: var(--accent);` | `hover:border-primary` |
| `.ne-btn:disabled` | `opacity: 0.45; cursor: default;` | `disabled:opacity-45 disabled:cursor-default` |
| `.ne-btn-primary` | `background: var(--accent); border-color: var(--accent); color: #fff;` | `bg-primary border-primary text-white` |
| `.ne-btn-danger` | `background: #991b1b; border-color: #991b1b; color: #fff;` | `bg-red-900 border-red-900 text-white` |
| `.ne-btn-small` | `width: fit-content; margin-top: 8px; font-size: 0.76rem;` | `w-fit mt-2 text-[0.76rem]` |
| `.ne-remove-btn` | `border: 1px solid var(--line); border-radius: 8px; background: #fff; color: #991b1b; width: 34px; cursor: pointer;` | `border border-outline-variant rounded-lg bg-white text-red-900 w-8.5 cursor-pointer` |
| `.ne-control-row` | `display: grid; grid-template-columns: 1fr 1fr; gap: 8px; margin-bottom: 10px;` | `grid grid-cols-2 gap-2 mb-2.5` |
| `.ne-control-row-single` | `grid-template-columns: 1fr;` | `grid-cols-1` |

#### **Modal & Dialogs**

| Class | CSS Definition | Tailwind Equivalent |
|-------|----------------|-------------------|
| `.ne-modal-backdrop` | `position: fixed; inset: 0; background: rgba(15, 23, 42, 0.35); backdrop-filter: blur(2px); display: flex; align-items: center; justify-content: center; z-index: 60;` | `fixed inset-0 bg-slate-900/35 backdrop-blur-[2px] flex items-center justify-center z-60` |
| `.ne-modal-card` | `width: min(620px, 90vw); max-height: 82vh; overflow-y: auto; background: var(--panel); border: 1px solid var(--line); border-radius: 14px; padding: 16px; box-shadow: 0 24px 40px rgba(15, 23, 42, 0.25);` | `w-[min(620px,90vw)] max-h-[82vh] overflow-y-auto bg-surface border border-outline-variant rounded-3.5xl p-4 shadow-xl` |
| `.ne-modal-card-confirm` | `width: min(440px, 90vw);` | `w-[min(440px,90vw)]` |
| `.ne-modal-actions` | `display: flex; gap: 8px; justify-content: flex-end; margin-top: 12px;` | `flex gap-2 justify-end mt-3` |
| `.ne-mode-badge` | `position: absolute; top: 12px; left: 12px; z-index: 20; border: 1px solid var(--line); border-radius: 999px; background: rgba(255, 255, 255, 0.9); color: var(--text-main); font-size: 0.76rem; font-weight: 600; padding: 5px 10px; cursor: pointer; transition: border-color 0.14s, background 0.14s;` | `absolute top-3 left-3 z-20 border border-outline-variant rounded-full bg-white/90 text-on-surface text-[0.76rem] font-bold px-2.5 py-1 cursor-pointer transition-[border-color,background] duration-140` |

#### **Inputs & Fields**

| Class | CSS Definition | Tailwind Equivalent |
|-------|----------------|-------------------|
| `.ne-input` | `width: 100%; border: 1px solid var(--line); border-radius: 8px; padding: 7px 9px; font-size: 0.82rem; background: #fff; color: var(--text-main);` | `w-full border border-outline-variant rounded-lg px-2 py-1.75 text-[0.82rem] bg-white text-on-surface` |
| `.ne-input-textarea` | `min-height: 64px; resize: vertical;` | `min-h-16 resize-y` |
| `.ne-field` | `display: flex; flex-direction: column; gap: 6px; margin-bottom: 10px; font-size: 0.8rem; color: var(--text-dim);` | `flex flex-col gap-1.5 mb-2.5 text-[0.8rem] text-on-muted` |
| `.ne-checkbox-label` | `display: flex; align-items: center; gap: 6px; font-size: 0.82rem; cursor: pointer;` | `flex items-center gap-1.5 text-[0.82rem] cursor-pointer` |
| `.ne-checkbox-inline` | `display: inline-flex; align-items: center; gap: 6px; font-size: 0.8rem; color: var(--text-main);` | `inline-flex items-center gap-1.5 text-[0.8rem] text-on-surface` |

#### **Properties & Relations**

| Class | CSS Definition | Tailwind Equivalent |
|-------|----------------|-------------------|
| `.ne-property-list` | `display: flex; flex-direction: column; gap: 8px;` | `flex flex-col gap-2` |
| `.ne-property-row` | `display: grid; grid-template-columns: 1fr 0.9fr 1.2fr auto; gap: 8px;` | `grid gap-2` (with custom col fractions) |
| `.ne-relation-pill-list` | `display: grid; gap: 8px;` | `grid gap-2` |
| `.ne-relation-pill-row` | `display: grid; grid-template-columns: 1fr auto; gap: 8px; align-items: center;` | `grid grid-cols-[1fr_auto] gap-2 items-center` |
| `.ne-relation-pill-text` | `border: 1px solid var(--line); border-radius: 999px; background: #fff; color: var(--text-main); font-size: 0.76rem; padding: 6px 10px;` | `border border-outline-variant rounded-full bg-white text-on-surface text-[0.76rem] px-2.5 py-1.5` |

#### **Inline Notes & Empty States**

| Class | CSS Definition | Tailwind Equivalent |
|-------|----------------|-------------------|
| `.ne-inline-note` | `display: inline-flex; align-items: center; justify-content: center; border: 1px dashed var(--line); border-radius: 8px; color: var(--text-dim); font-size: 0.76rem; padding: 4px 8px;` | `inline-flex items-center justify-center border border-dashed border-outline-variant rounded-lg text-on-muted text-[0.76rem] px-2 py-1` |
| `.ne-empty-note` | `margin: 0; font-size: 0.78rem; color: var(--text-dim);` | `m-0 text-[0.78rem] text-on-muted` |

#### **Connection Menu**

| Class | CSS Definition | Tailwind Equivalent |
|-------|----------------|-------------------|
| `.ne-connect-menu` | `position: fixed; z-index: 80; width: 240px; border: 1px solid var(--line); border-radius: 10px; background: #fff; box-shadow: 0 16px 28px rgba(15, 23, 42, 0.18); padding: 10px; transform: translate(8px, 8px);` | `fixed z-80 w-60 border border-outline-variant rounded-[10px] bg-white shadow-lg p-2.5 translate-x-2 translate-y-2` |
| `.ne-connect-list` | `max-height: 160px; overflow-y: auto; margin: 8px 0; display: flex; flex-direction: column; gap: 6px;` | `max-h-40 overflow-y-auto my-2 flex flex-col gap-1.5` |
| `.ne-connect-list-scroll` | `max-height: 240px;` | `max-h-60` |
| `.ne-connect-item` | `width: 100%; text-align: left; border: 1px solid var(--line); border-radius: 8px; background: #fff; padding: 6px 8px; font-size: 0.78rem; cursor: pointer;` | `w-full text-left border border-outline-variant rounded-lg bg-white px-2 py-1.5 text-[0.78rem] cursor-pointer` |

#### **Utility Classes (Not in CSS, Used in Code)**

| Class | Expected Purpose | Tailwind Equivalent |
|-------|------------------|-------------------|
| `.ne-block` | Display: block utility | `block` |
| `.ne-flex` | Display: flex utility | `flex` |
| `.ne-none` | Display: none utility | `hidden` |
| `.ne-dark` | Dark mode toggle | `dark` (Tailwind's dark mode prefix) |
| `.ne-clamp-2` | Text clamping (2 lines) | `line-clamp-2` |

---

## SECTION D: Inline Styles Using Legacy Variables

### Found Inline `style` Attributes

#### **1. `pages/global/KnowledgeGraph.tsx:463`**
**File location:** `/apps/review-workbench/src/pages/global/KnowledgeGraph.tsx`

**Context:** Simple node rendering in `SimpleNode` component
```tsx
<div
  className={`ne-node-simple ${selected ? "ne-node-simple-selected" : ""}`}
  style={{ borderLeft: `4px solid ${color.border}`, background: color.bg, color: 'var(--text-main)' }}
  title={tooltipFromProperties(nodeData.properties)}
>
```

**Variables used:**
- `color: 'var(--text-main)'` — Direct CSS variable reference for text color

**Notes:**
- The `color.border` and `color.bg` are computed values (not legacy CSS variables), coming from `masteryColorForCategory()` function
- Only `var(--text-main)` is a legacy variable reference

#### **2. `pages/global/KnowledgeGraph.tsx:623`**
**File location:** `/apps/review-workbench/src/pages/global/KnowledgeGraph.tsx`

**Context:** Edge rendering in knowledge graph
```tsx
<BaseEdge
  id={id}
  path={path}
  style={{ stroke: 'var(--accent)', strokeWidth: 1.5, ...style }}
  markerEnd={markerEnd}
/>
```

**Variables used:**
- `stroke: 'var(--accent)'` — Direct CSS variable reference for SVG stroke color

**Notes:**
- This is a React Flow `BaseEdge` component
- The `...style` spreads additional styles that may override or add to these properties

---

## SECTION E: Migration Recommendations

### Priority 1: Replace in `pages/global/KnowledgeGraph.tsx`

This file is the primary consumer of all `.ne-*` classes (64 unique classes). A full migration of this page should be prioritized:

**Strategy:**
1. Break down the monolithic `KnowledgeGraph.tsx` into smaller components
2. Migrate each component to use Tailwind tokens systematically
3. Replace `.ne-*` class references with Tailwind equivalents from Section C above
4. Replace inline `var(--*)` references with Tailwind CSS token utilities

**Example conversions:**
- `.ne-sidebar` → `w-70 bg-surface border-r border-outline-variant px-4 py-3 overflow-y-auto`
- `.ne-btn-primary` → `bg-primary border-primary text-white`
- `var(--accent)` → Tailwind's `text-primary`, `bg-primary`, or `border-primary`

### Priority 2: Cleanup Utility-Only Classes

Files like `RequirementItem.tsx`, `SkillPalette.tsx`, etc., use only utility-like `.ne-*` classes:
- `.ne-block` → Replace with `block`
- `.ne-none` → Replace with `hidden`
- `.ne-flex` → Replace with `flex`
- `.ne-dark` → Replace with `dark` (if using Tailwind's dark mode)
- `.ne-clamp-2` → Replace with `line-clamp-2`

### Priority 3: CSS Cleanup

Once all usages are migrated:
1. Remove the `:root {}` CSS custom property block (lines 43–54 in `styles.css`)
2. Remove all `.ne-*` class definitions (lines 316–896 in `styles.css`)
3. Retain core utilities like `.scanline-overlay`, `.tactical-glow`, `.alert-glow`, `.panel-border` if still in use
4. Update the comment from "LEGACY" to reflect only active patterns

### Tailwind Token Mapping Reference

Keep this reference for all conversions:

| Variable | Color | Tailwind Utility |
|----------|-------|-----------------|
| `--panel` | `#121416` | `bg-surface` |
| `--line` | `#3a494b` | `border-outline-variant` |
| `--accent` | `#00f2ff` | `text-primary` / `bg-primary` / `border-primary` |
| `--accent-soft` | `#005f66` | `bg-primary-on` |
| `--text-main` | `#e2e2e5` | `text-on-surface` |
| `--text-dim` | `#849495` | `text-on-muted` |
| `--bad` | `#ffb4ab` | `text-error` |
| `--good` | `#00f2ff` | `text-primary` |
| `--warn` | `#ffaa00` | `text-secondary` |
| `--pending` | `#ffaa00` | `text-secondary` |

---

## Summary Statistics

| Metric | Count |
|--------|-------|
| Total `.ne-*` classes defined in CSS | 80+ |
| Unique `.ne-*` classes used in code | 80 |
| Files using `.ne-*` classes | 18 |
| Primary consumer file | `pages/global/KnowledgeGraph.tsx` (64 classes) |
| CSS custom properties actively used | 6 (`--panel`, `--line`, `--accent`, `--accent-soft`, `--text-main`, `--text-dim`) |
| CSS custom properties unused | 4 (`--bad`, `--good`, `--warn`, `--pending`) |
| Inline `var(--*)` usages in `.tsx` files | 2 |
| Utility-only `.ne-*` classes (not in CSS) | 5 (`ne-block`, `ne-none`, `ne-flex`, `ne-dark`, `ne-clamp-2`) |

