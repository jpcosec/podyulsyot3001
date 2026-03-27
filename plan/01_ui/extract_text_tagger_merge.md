# Extract Page — Text Tagger Feature Merge Plan

## Context

These two implementations serve **related but different purposes**:

| | `ui-redesign` `/jobs/:source/:jobId/extract` | `dev` `TextTaggerPage` (`RichTextPane`) |
|---|---|---|
| **Purpose** | Review and correct LLM-extracted requirements | Manually annotate raw source text |
| **Source data** | `useViewExtract` — LLM-produced requirement list + source markdown | Hard-coded default text (sandbox) |
| **Left pane** | `SourceTextPane` — monospace source with **line-level** highlight | Free-text display with **character-level** inline `<mark>` highlights |
| **Center/right** | `RequirementList` — CRUD cards (add/edit/delete) | Sidebar with category boxes, subcategory grid, note cards |
| **Priority model** | `must` / `nice` (two levels) | `must` / `nice` + subcategories: blocker, important, less_important, other |
| **Add requirement** | "+ ADD" button → blank card | Select text → drag or keyboard → tagged note card |
| **Edit text** | Double-click text in card → inline textarea | Double-click node label or details field |
| **Span tracking** | `text_span: { start_line, end_line }` — line range | `start / end` character offsets — precise |
| **Keyboard tagging** | None | `1` = requirement, `2` = info → then `1-N` for subcategory |
| **Drag-and-drop** | None | `@dnd-kit` — drag selected text to category box, drag note to reclassify |
| **Details / notes** | None | Editable "Details" field per note card |
| **Search** | None | Filter notes by text within active subcategory |
| **Collapse cards** | None | Toggle collapsed/expanded per card |
| **Gate action** | COMMIT → MATCH (navigates to next stage) | None (sandbox only) |
| **HITL gate** | `useEditorState` + `useGateDecide` hooks | None |

---

## What to keep (ui-redesign is canonical)

| What | Why |
|---|---|
| `ExtractUnderstand` page + `SplitPane` layout | Connected to real pipeline data |
| `SourceTextPane` + `RequirementList` + `RequirementItem` | Correct CRUD model for reviewing LLM output |
| `ExtractControlPanel` (SAVE DRAFT + COMMIT → MATCH) | HITL gate — must be preserved |
| React Query hooks (`useViewExtract`, `useEditorState`) | Correct cache/mutation patterns |
| `RequirementItem` double-click to edit | Clean inline edit pattern |
| Priority select (`must` / `nice`) | Simple enough for now |

---

## What to port from `dev` `RichTextPane`

### 1. Character-Level Inline Span Highlighting

**Source:** `RichTextPane` — `buildSegments()` + `<mark>` rendering (lines 134–171, 828–846)

**Target:** `SourceTextPane.tsx` — replace line-range highlight with character-offset highlight

**What changes:**
- `RequirementItem` data gains character offsets (`start_char`, `end_char`) in addition to the existing `text_span: { start_line, end_line }`
- `SourceTextPane` receives all requirement spans (not just the hovered/selected one) and renders each as a colored `<mark>` inline
- Each requirement gets a distinct color (by priority: primary for must, secondary for nice)
- Clicking a highlighted span in the source selects that requirement in the list

**Why it matters:** Currently hovering a card only highlights an entire line range. Character offsets let the operator see exactly which text fragment produced each requirement.

---

### 2. Select Text → Create Requirement

**Source:** `RichTextPane` — `captureSelection()` + `addNote()` (lines 522–596)

**Target:** `SourceTextPane.tsx` + `ExtractUnderstand.tsx`

**What to add:**
- `onMouseUp` / `onKeyUp` handler on the source text pane captures `window.getSelection()`
- Converts DOM range to character offsets (same `toOffset()` helper as `RichTextPane`)
- Shows a floating "Tag as requirement" chip above the selection (replaces `SelectionChip`)
- Pressing `1` (must) or `2` (nice) while text is selected immediately creates a new `RequirementItem` with the selected text pre-filled and the `text_span` / character offsets recorded

**Why it matters:** The operator can read the source and create requirements in-place — much faster than clicking "+ ADD" and typing.

**Note:** Only carry over the selection → requirement creation. Drop the "Info" category and all its subcategories — the pipeline only needs `must` / `nice` / `nice_to_have` priority.

---

### 3. Keyboard-First Priority Assignment

**Source:** `RichTextPane` — `useEffect` keydown handler (lines 690–736)

**Target:** `ExtractUnderstand.tsx` — extend existing `handleKeyDown`

**Shortcuts to add:**
| Key | Action |
|---|---|
| `1` | Tag selection as `must` (when text selected in source) |
| `2` | Tag selection as `nice` / `nice_to_have` |
| `Escape` | Clear selection |

Simple two-step: select text in source → press `1` or `2` → requirement card created.

---

### 4. Details / Annotation Field per Requirement

**Source:** `RichTextPane` — `EditableField` + `NoteCard` details field (lines 192–253, 461–473)

**Target:** `RequirementItem.tsx` — add collapsible "Notes" textarea

**What to add:**
- Each `RequirementItem` gets an optional `notes?: string` field
- When expanded (selected), shows a textarea for operator annotations
- Notes are saved with the editor state via `useEditorState`
- Displayed as a dimmed italic preview in the collapsed card

**Why it matters:** Operator may want to record *why* a requirement was adjusted, or flag it for later.

---

### 5. Collapse / Expand Cards

**Source:** `RichTextPane` — `collapsedNoteIds: Set<string>` + `toggleCollapse()` (lines 496, 772–782)

**Target:** `RequirementItem.tsx` — add collapsed state

**What to add:**
- Collapsed (default): shows only ID badge + priority chip + first ~60 chars of text
- Expanded (on click): shows full text editor + notes field + delete button
- Selected card auto-expands

**Why it matters:** With 10–20 requirements the list gets long. Collapsed cards give an overview; expanded shows editing controls.

---

### 6. Search / Filter in Requirement List

**Source:** `RichTextPane` — `searchQuery` state + filter logic (lines 497, 785–804)

**Target:** `RequirementList.tsx` — add search input in header

**What to add:**
- Search input in the "Extracted Reqs (N)" header bar
- Filters cards by requirement text, notes, or ID
- Clears on `Escape`

---

### 7. Drag-and-Drop Priority Reclassification

**Source:** `RichTextPane` — `@dnd-kit/core`, `MainCategoryBox` as drop target, `NoteCard` as draggable (lines 1–13, 276–349, 363–481)

**Target:** `RequirementList.tsx` — optional, lowest priority

**What to add:**
- Drag a requirement card from the list onto a "MUST" or "NICE" zone at the top of the list
- Reclassifies the requirement priority on drop

**Note:** This is the most complex feature to port. Implement only after 1–6 are done.

---

## Files to copy / reference (dev branch)

| Dev source | Target (ui-redesign) | Notes |
|---|---|---|
| `RichTextPane.tsx` — `toOffset()` helper | `utils/text-offsets.ts` | Copy verbatim |
| `RichTextPane.tsx` — `buildSegments()` | `features/job-pipeline/components/SourceTextPane.tsx` | Adapt to `RequirementItem[]` instead of `HighlightNote[]` |
| `RichTextPane.tsx` — `captureSelection()` | `SourceTextPane.tsx` | Adapt: emit `{start, end, text}` via prop callback |
| `RichTextPane.tsx` — keyboard handler | `ExtractUnderstand.tsx` | Simplified to 2 keys only (1=must, 2=nice) |
| `RichTextPane.tsx` — `EditableField` | Inline in `RequirementItem.tsx` | Already partially exists (double-click edit) |

---

## Data model delta

Add to `RequirementItem` type (already in `api.types`):

```ts
interface RequirementItem {
  id: string;
  text: string;
  priority: 'must' | 'nice' | 'nice_to_have';
  spans: unknown[];          // existing
  text_span: RequirementTextSpan | null;  // existing — line range
  // NEW:
  char_start?: number | null;  // character offset in source_markdown
  char_end?: number | null;
  notes?: string;            // operator annotation
}
```

The `char_start` / `char_end` are set when a requirement is created via text selection. LLM-produced requirements may not have them initially — that's fine, line-range highlight still works as fallback.

---

## Usage Guide

### What is this page?

The Extract page is the first human gate in the pipeline. The LLM has already read the job posting and extracted a list of requirements (must-haves and nice-to-haves). Your job is to:

1. **Audit** the extracted list — is anything missing, duplicated, or wrong?
2. **Correct** requirements — edit text, change priority, delete obvious errors
3. **Add** anything the LLM missed — select the text in the source, tag it
4. **Commit** to advance to the Match stage

---

### Layout

```
┌─────────────────────────────────────────────────────────────────┐
│  Portfolio > tu_berlin > 999001     FLOW SCRAPE EXTRACT MATCH   │  ← job nav
├──────────────────────────┬───────────────────────┬──────────────┤
│                          │  EXTRACTED REQS (3)   │  PHASE       │
│  SOURCE TEXT             │  ┌─────────────────┐  │  EXTRACT     │
│                          │  │ R1 [MUST] Python │  │             │
│  # PhD Researcher ...    │  │ ─────────────── │  │  (selected  │
│  - Python (required) ██  │  │ R2 [MUST] Eng.. │  │   req JSON) │
│  - English C1 (req.) ██  │  │ R3 [NICE] Res.. │  │             │
│  - Research in AI ...    │  └─────────────────┘  │  SAVE DRAFT │
│                          │  [ + ADD ]             │  COMMIT→MATCH│
└──────────────────────────┴───────────────────────┴──────────────┘
```

**Left pane — Source Text:** The raw job posting (markdown). Line numbers on the left.
When you hover or select a requirement card, the relevant lines highlight in cyan.
*(After span porting: the exact text fragment highlights inline.)*

**Center pane — Extracted Reqs:** The LLM's requirement list. Each card shows:
- **ID** (R1, R2, …)
- **Priority badge** — `MUST` (amber) or `NICE` (muted) — click to change
- **Requirement text** — double-click to edit
- **Delete button** (×) — confirm before deleting MUST requirements

**Right panel — Control Panel:**
- When a requirement is selected: shows its full JSON (→ will become structured fields)
- Shortcut hints: `Ctrl+S` / `Ctrl+Enter`
- `SAVE DRAFT` — persist edits without committing
- `COMMIT → MATCH` — saves and navigates to the Match stage

---

### Step-by-step workflow

#### 1. Read the source text (left pane)
Scan the job posting. Mentally note any requirements the LLM may have missed.

#### 2. Review each requirement card (center pane)
- Hover a card → source text highlights the matching lines
- Is the priority right? `MUST` = truly required; `NICE` = desirable but not blocking
- Is the text accurate? Double-click to edit inline

#### 3. Delete a wrong requirement
Click the × button on any card. For `MUST` cards you'll get a confirm dialog.

#### 4. Add a missing requirement (two ways)

**Method A — Type it:**
Click `+ ADD` → a blank card appears at the bottom. Double-click the text to edit it. Set the priority.

**Method B — Select from source *(after span porting)*:**
Click and drag to select text in the left pane → press `1` (MUST) or `2` (NICE) → a new card appears with the selected text pre-filled and the source span recorded.

#### 5. Annotate a requirement *(after details porting)*
Click a card to expand it → add a note in the "Notes" field (e.g. "LLM paraphrased — original says 'proficiency in R or Python'").

#### 6. Save draft
`Ctrl+S` saves your current list. Use this to pause and return. The list will reload from the saved state on next visit.

#### 7. Commit to Match
When satisfied: `Ctrl+Enter` or **COMMIT → MATCH** button.
This saves and navigates to the Match page. The pipeline uses your final requirement list to run matching.

> ⚠ Note: Currently COMMIT → MATCH just navigates — it does not send a formal gate decision to the backend yet. A `useGateDecide` hook call will be added in a future iteration.

---

### Keyboard shortcuts

| Key | Action |
|---|---|
| `Ctrl+S` | Save draft |
| `Ctrl+Enter` | Save + navigate to Match |
| `1` | Tag selected source text as MUST *(after span porting)* |
| `2` | Tag selected source text as NICE *(after span porting)* |
| `Escape` | Clear text selection / deselect card |

---

### Empty and error states

| State | What the operator sees |
|---|---|
| Extract not yet run | `EXTRACT_DATA_NOT_FOUND` monospace error message |
| Loading | Spinner centered in page |
| No requirements extracted | "NO_REQUIREMENTS_EXTRACTED" + "+ Add Manual" button |
| Delete MUST requirement | Browser confirm dialog: `Delete MUST requirement "…"?` |
| Save failed | *(not yet shown — add error toast)* |

---

## Suggested implementation order

1. Collapse/expand cards in `RequirementItem` (state only, no DnD)
2. Add `notes` field to `RequirementItem` (collapsible textarea)
3. Search/filter in `RequirementList` header
4. Port `toOffset()` + `buildSegments()` → `SourceTextPane` for character-level highlights
5. `captureSelection()` on source pane + floating "Tag as…" chip
6. Keyboard `1` / `2` to create requirement from selection
7. *(Optional)* Drag-and-drop priority reclassification via `@dnd-kit`
