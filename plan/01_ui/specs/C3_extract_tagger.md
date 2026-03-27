# Spec C3 — Extract Tagger (ExtractUnderstand page enrichment)

**Feature:** `src/features/job-pipeline/`
**Page:** `src/pages/job/ExtractUnderstand.tsx`
**Libraries:** `@tanstack/react-query` · `react-router-dom`
**Phase:** 2 (included in `phase_2_bring_back_migrations`)

---

## Migration Notes

**Legacy source:** `apps/review-workbench/src/sandbox/components/RichTextPane.tsx` in branch `dev`
**Legacy components:**
- `RichTextPane.tsx` — `toOffset(root, targetNode, nodeOffset)` (lines 120–132) — character offset from DOM range
- `RichTextPane.tsx` — `buildSegments(text, notes)` (lines 134–171) — split text into highlight segments
- `RichTextPane.tsx` — `captureSelection()` (lines 522–555) — capture mouse selection as char offsets
- `RichTextPane.tsx` — keyboard handler (lines 690–736) — "1"=must, "2"=nice when text selected

**To migrate:**
1. Extract `toOffset()` → `src/utils/text-offsets.ts`
2. Adapt `buildSegments()` → into `SourceTextPane.tsx` using `RequirementItem[]` instead of `HighlightNote[]`
3. Add `captureSelection()` + `onMouseUp` to `SourceTextPane.tsx`; emit `{start, end, text}` via `onSpanSelect` callback
4. Extend `ExtractUnderstand.tsx`: handle `onSpanSelect` → create requirement with char offsets; add keyboard "1"/"2" handler
5. Add collapse/expand state to `RequirementItem.tsx` (collapsed = preview only)
6. Add `notes?: string` field to `RequirementItem.tsx` (editable textarea when expanded)
7. Add search input to `RequirementList.tsx` header

**Drop from RichTextPane:** Info category, subcategory taxonomy (blocker/important/etc.), drag-and-drop reclassification, DnD library — not needed for production extract workflow.

---

## 1. Operator Objective

- Hover a requirement card → see the exact source text lines highlight in the source pane
- Select text in the source pane → press "1" (MUST) or "2" (NICE) to create a requirement pre-filled with selected text and character offsets recorded
- Each requirement card is collapsed by default (ID + priority + text preview); click to expand full editing controls
- Expanded card shows editable text (double-click), priority select, delete button, and a "Notes" textarea for operator annotations
- Filter the requirement list by typing in a search bar
- Save draft (Ctrl+S); commit to advance to Match (Ctrl+Enter or button)

---

## 2. Data Contract (API I/O)

**Read:**
- `GET /api/v1/jobs/:source/:jobId/view/extract` → `ViewPayload`
  ```ts
  {
    view: 'extract';
    data: {
      source_markdown: string;
      requirements: RequirementItem[];
    }
  }
  ```
  Where `RequirementItem`:
  ```ts
  {
    id: string;
    text: string;
    priority: 'must' | 'nice' | 'nice_to_have';
    spans: unknown[];
    text_span: { start_line: number; end_line: number } | null;
    // NEW (operator-set, not from LLM):
    char_start?: number | null;
    char_end?: number | null;
    notes?: string;
  }
  ```

**Write:**
- `POST /api/v1/jobs/:source/:jobId/editor-state/extract_understand` — save requirements list

---

## 3. UI Composition and Layout

**Layout:** Resizable `SplitPane` (50/50 default) + right control panel (w-80)

```
┌──────── 50% ────────────┬──────── 50% ─────────────────┬── w-80 ──────────┐
│  SOURCE TEXT            │  EXTRACTED REQS (3)  [Search] │  PHASE EXTRACT   │
│                         │  ─────────────────────────    │                  │
│  1  # PhD Researcher    │  R1 [MUST] Python         ▶  │  (selected req   │
│  2                      │  R2 [MUST] English C1     ▶  │   fields or      │
│  3  Contact: …          │  R3 [NICE] Research in AI ▼  │   "click to      │
│  4                      │  ┌─────────────────────────┐  │   inspect")      │
│  5  ## Requirements     │  │ Text: [Research in AI ] │  │                  │
│  6  - Python █████ ◀─── │  │ Notes: [              ] │  │  Ctrl+S — Save   │
│  7  - English C1 ████   │  └─────────────────────────┘  │  Ctrl+Enter→Match│
│  8  - Research in AI    │  [+ ADD]                       │  SAVE DRAFT      │
│                         │                                │  COMMIT → MATCH  │
└─────────────────────────┴────────────────────────────────┴──────────────────┘
│  Selection chip (floats above selected text when text is selected in source) │
│  "Press 1 = MUST · 2 = NICE · Esc = cancel"                                │
```

**Core Components:**
- `SourceTextPane` (extended) — char-level `<mark>` highlights + `onMouseUp` selection capture + floating tag hint
- `RequirementList` (extended) — adds search input in header
- `RequirementItem` (extended) — collapsed/expanded toggle + notes textarea
- `ExtractUnderstand` (extended) — `onSpanSelect` handler, keyboard "1"/"2" handler

---

## 4. Styles (Terran Command)

- Highlight segment: `bg-primary/15 border-x border-primary/60` (must); `bg-secondary/15 border-x border-secondary/40` (nice)
- Selection floating hint: `fixed bottom-4 left-1/2 -translate-x-1/2 font-mono text-[10px] bg-surface-container border border-primary/30 px-3 py-1.5`
- Collapsed card: single-line with truncated text preview
- Expanded card: full controls visible
- Notes textarea: `bg-surface-low border border-outline/20 font-mono text-xs resize-none`
- Search input: `bg-transparent border-0 outline-none font-mono text-[10px] text-on-surface`

**Interactions:**
- Hover requirement card → highlight lines in source pane (existing)
- Click card → expand; click again → collapse
- Double-click text in expanded card → inline textarea edit
- Select text in source pane → floating hint appears
- Press "1" with text selected → create MUST requirement with selected text + char offsets
- Press "2" with text selected → create NICE requirement
- Press Escape → cancel selection
- Type in search bar → filter cards

**Empty State:** "NO_REQUIREMENTS_EXTRACTED" + "+ Add Manual" button
**Error State:** `EXTRACT_DATA_NOT_FOUND` monospace error
**Loading State:** Spinner centered

---

## 5. Files to Create / Modify

```
src/utils/
  text-offsets.ts             NEW: toOffset(root, node, offset) — char offset helper
src/features/job-pipeline/
  components/
    SourceTextPane.tsx         EXTEND: buildSegments(), onMouseUp, floating tag hint,
                                        multi-req char highlights (not just hovered)
    RequirementList.tsx        EXTEND: add search input + filter logic in header
    RequirementItem.tsx        EXTEND: collapsed/expanded state + notes textarea field
src/pages/job/
  ExtractUnderstand.tsx        EXTEND: onSpanSelect handler, keyboard "1"/"2" handler,
                                        notes field in requirements state, search state
```

---

## 6. Definition of Done

```
[ ] ExtractUnderstand renders without console errors or TS errors
[ ] Source text pane shows line-numbered monospace text
[ ] Hovering a requirement card highlights the matching lines in source (existing behavior preserved)
[ ] Selecting text in the source pane shows floating hint "1=MUST · 2=NICE · Esc=cancel"
[ ] Pressing "1" with text selected creates a new MUST requirement with the selected text pre-filled
[ ] Pressing "2" with text selected creates a new NICE requirement
[ ] Pressing Escape clears the text selection and dismisses the hint
[ ] Requirements with char_start/char_end show colored inline <mark> highlights (not just line-level)
[ ] All requirement cards are collapsed by default (single-line preview)
[ ] Clicking a card expands it showing full text editor, priority select, delete, and notes textarea
[ ] Search input in RequirementList header filters cards in real-time
[ ] Ctrl+S saves draft; Ctrl+Enter saves and navigates to /jobs/:source/:jobId/match
[ ] No hardcoded data — all from useViewExtract hook + mock
```

---

## 7. E2E (TestSprite)

**URL:** `/jobs/tu_berlin/999001/extract`

1. Verify source text pane renders with line numbers and markdown content
2. Verify 3 requirement cards render (R1 Python/MUST, R2 English C1/MUST, R3 Research in AI/NICE)
3. Verify cards are collapsed by default (single-line preview visible)
4. Click a card → verify it expands showing text editor and notes textarea
5. Type in the search bar → verify cards filter in real-time
6. Verify hovering a card highlights the corresponding lines in the source pane
7. Click "+ ADD" → verify a new blank card appears at the bottom
8. Verify COMMIT → MATCH button navigates to `/jobs/tu_berlin/999001/match`

---

## 8. Git Workflow

### Commit on phase close

```
feat(ui): implement C3 Extract Tagger enrichment

- toOffset() utility for character-level span tracking
- SourceTextPane: multi-req char highlights + text selection capture + tag hint
- RequirementItem: collapse/expand toggle + notes textarea
- RequirementList: search/filter input in header
- ExtractUnderstand: onSpanSelect handler + keyboard 1/2 tagging
```

### Changelog entry

```markdown
## 2026-MM-DD

- Implemented C3 Extract Tagger: ported character-level span highlighting,
  select-to-create requirements, keyboard priority tagging (1=MUST/2=NICE),
  collapse/expand cards, notes field, and search/filter from dev RichTextPane
  into ui-redesign ExtractUnderstand page.
```

### Checklist update

- [x] C3 Extract Tagger — char-level spans, select-to-create, keyboard priority tagging
