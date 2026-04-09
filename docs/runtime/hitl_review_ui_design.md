# HITL Review UI — Design Specification

Design decisions made during the review UI redesign. Covers all four HITL stages, interaction
models, and what is and is not achievable with Textual.

---

## Background

The current `ReviewScreen` only supports HITL 1 (match evidence). Stages 2–4 have no
meaningful UI — reviewers see raw JSON or an empty screen (tracked in
[#7](https://github.com/jpcosec/podyulsyot3001/issues/7)).

Each HITL stage exposes a different artifact and requires a different interaction model.
This document defines the design for each.

---

## HITL Stages Overview

| Stage | Node | Artifact | Outcome key | Regen target |
|-------|------|----------|-------------|--------------|
| 1 | `hitl_1_match_evidence` | `matches` (list) | `match_outcome` | `alignment_engine` |
| 2 | `hitl_2_blueprint_logic` | `blueprint` (dict) | `blueprint_outcome` | `conciliator` |
| 3 | `hitl_3_content_style` | `markdown_bundle` (dict of docs) | `bundle_outcome` | `stage_4_microplanning` |
| 4 | `hitl_4_profile_updates` | `pending_profile_updates` (list) | `profile_update_outcome` | — (binary) |

---

## HITL 1 — Match Evidence

**What the reviewer does:** Scan each requirement-to-profile match, judge whether the
evidence and reasoning are credible, approve or reject per match or in bulk.

### Layout: master-detail

```
┌──────────────┬──────────────────────────────────────────────┐
│  [R01] ✓ 92% │  Requirement                                 │
│  [R02] ○ 78% │  5+ years Python backend development         │
│  [R03] ✗ 41% │                                              │
│  [R04] ○ 83% │  Evidence                                    │
│  [R05] ○ 55% │  EXP-03, PROJ-07                             │
│              │                                              │
│              │  Reasoning                                   │
│              │  Candidate has 7 years Python at Acme…       │
│              │                                              │
│              │  [✓ Approve (y)]  [✗ Reject (n)]  [↔ (spc)] │
└──────────────┴──────────────────────────────────────────────┘
│  [Approve All (a)]  [Reject All (r)]  [Submit (s)]  [q]    │
```

- Left panel: scrollable index — one row per match with score badge and current state icon
- Right panel: full detail of the selected match
- Selection syncs between keyboard (`j`/`k`) and mouse click on left panel

### Keybindings

| Key | Action |
|-----|--------|
| `j` / `k` | Next / prev match |
| `y` | Approve selected |
| `n` | Reject selected |
| `space` | Toggle selected |
| `a` / `r` | Approve / reject all |
| `s` | Submit |
| `q` | Quit / back |

### Patch serialization

Each outcome in `_match_outcomes` maps to a `GraphPatch`:
```python
GraphPatch(action="approve"|"reject", target_id=req_id)
```
The bulk sentinel `GraphPatch(action=..., target_id="__review__")` is appended last.

---

## HITL 2 — Blueprint Logic

**What the reviewer does:** Verify the proposed section structure makes sense for this
job. Edit section emphasis, reorder sections, or drop a section entirely.

### Layout: section list + detail

```
┌──────────────┬──────────────────────────────────────────────┐
│  Sections    │  Section: experience                         │
│              │  Strategy: highlight_recent                  │
│  ▶ experience│                                              │
│    skills    │  Emphasis                                    │
│    education │  [ Python backend, distributed systems    ]  │
│    summary   │                                              │
│    projects  │  Matched Requirements                        │
│    languages │  · R01 (92%)  Python 5+ years               │
│              │  · R04 (78%)  Microservices experience       │
│              │                                              │
│              │  [✓ Keep]  [✗ Drop]  [✎ Edit emphasis (e)]  │
└──────────────┴──────────────────────────────────────────────┘
│  [Approve (a)]  [Reject (r)]  [Regenerate (g)]  [Submit (s)]│
```

- Left: section list, `j`/`k` to navigate, `shift+j`/`shift+k` to reorder
- Right: section detail. `e` opens an `Input` pre-filled with the emphasis string
- `x` drops the section (adds a `reject` patch for that section id)

### Patch serialization

`blueprint` has shape `{application_id, strategy_type, sections: [...]}`.
`_apply_modify` on a dict sets `blueprint[target_id] = new_value`, so section-level
patches must target the top-level `"sections"` key with the full modified list.

`BlueprintReviewScreen` maintains the sections list as local state, applies edits and
drops in-place, then sends the whole list as one patch at submit time:

```python
# All section edits + drops in one patch
GraphPatch(action="modify", target_id="sections", new_value=[...modified_sections_list...])

# Bulk sentinel
GraphPatch(action="approve", target_id="__review__")
```

This avoids any need to modify the patch engine.

---

## HITL 3 — Content & Style

**What the reviewer does:** Read the generated CV / letter / email markdown. Select
ranges of lines, annotate them (delete, replace, comment), then submit or request a
regen.

### Interaction model: Vim visual mode

Inspired by Vim's `V` (line-wise visual) mode. The reviewer navigates the rendered
document with `j`/`k`, enters selection mode with `v`, extends the selection, then
acts on it.

```
NORMAL ──v──► VISUAL ──j/k──► extend selection
                 │
                 ├──d──► Delete modal      → annotation added → NORMAL
                 ├──c──► Replace TextArea  → annotation added → NORMAL
                 ├──r──► Comment Input     → annotation added → NORMAL
                 ├──i──► Insert TextArea   → annotation added → NORMAL
                 └──Esc──────────────────────────────────────► NORMAL
```

### Layout

```
┌───────────────────────────────────────────────────────────────┐
│  [cv]  [letter]  [email]                   NORMAL  3 annots  │
├───────────────────────────────────────────────────────────────┤
│  ## Experience                                                │
│  ┃                                                           │
│  ┃ Senior Backend Engineer · Acme Corp · 2019–2024           │  ← cursor line (highlighted)
│  ┃ Designed and maintained distributed Python services       │
│  ┃ handling high-scale traffic. Led migration from           │  ← selected range (v mode)
│  ┃ monolith to microservices.                                │
│  ┃                                                           │
│  ## Skills                                                    │
│  Python · Go · PostgreSQL · Kafka · Docker                   │
│                                                               │
├───────────────────────────────────────────────────────────────┤
│  Annotations                                                  │
│  [1] ✗ delete   L3–5  "Designed and maintained…"             │
│  [2] ↔ replace  L9    "Python · Go · …"  →  "Python, Go…"   │
│  [3] 💬 comment  L1    "## Experience"   →  "Confirm title"  │
└───────────────────────────────────────────────────────────────┘
│  [Approve (a)]  [Content Regen (g)]  [Submit (s)]  [q]       │
```

### Mode state

```python
@dataclass
class EditorMode:
    mode: Literal["NORMAL", "VISUAL"] = "NORMAL"
    cursor: int = 0          # current line index
    anchor: int = 0          # selection start in VISUAL mode

    @property
    def selection(self) -> tuple[int, int]:
        lo, hi = sorted([self.anchor, self.cursor])
        return lo, hi
```

### Line widget

Each line is a `Static` widget with an id (`line-{n}`). CSS classes drive state:

```css
.line-cursor {
    border-left: heavy $accent;
    background: $boost;
}

.line-selected {
    border-left: solid $warning;
    background: $panel;
}
```

In NORMAL mode only the cursor line gets `line-cursor`. In VISUAL mode all lines in
`[anchor, cursor]` get `line-selected`, cursor line additionally keeps `line-cursor`.

### Annotation data

```python
@dataclass
class LineAnnotation:
    start_line: int
    end_line: int
    kind: Literal["delete", "replace", "comment", "insert"]
    original_text: str
    replacement: str | None = None   # replace / insert
    comment: str | None = None       # comment
```

Annotations are displayed in a bottom panel sorted by `start_line`. `x` on a selected
annotation removes it.

### Document tabs

`markdown_bundle` is a dict with keys `cv`, `letter`, `email`. Tabs switch the active
document; each document maintains its own `EditorMode` and annotation list.

### Annotation modals

| Key (in VISUAL) | Widget | Pre-filled with |
|---|---|---|
| `d` | Confirmation prompt | Selected lines (read-only) |
| `c` | `TextArea` modal | Selected lines as editable text |
| `r` | `Input` modal | Empty (user types comment) |
| `i` | `TextArea` modal | Empty (user types text to insert after) |

All modals use `push_screen(modal, callback)` → `screen.dismiss(result)` pattern.

### Patch serialization

The patch engine's `_apply_modify` operates on the top-level keys of `markdown_bundle`
(`cv_full_md`, `letter_full_md`, `email_body_md`). It has no concept of segments.

`ContentReviewScreen` must **reconstruct the full modified markdown string** from the
annotation list before building patches, then send one patch per modified document:

```python
# One patch per document that has at least one annotation
GraphPatch(action="modify", target_id="cv_full_md",    new_value=modified_cv_text)
GraphPatch(action="modify", target_id="letter_full_md", new_value=modified_letter_text)
```

The screen owns the reconstruction: iterate segments in order, apply delete/replace/insert
annotations to each segment's `raw_text`, re-join with `\n\n`.  Documents with no
annotations send no patch (their content is unchanged).

The bulk sentinel is appended last:
```python
GraphPatch(action="approve", target_id="__review__")
```

### Keybindings (HITL 3 specific)

| Key | Mode | Action |
|-----|------|--------|
| `j` / `k` | NORMAL + VISUAL | Move cursor / extend selection |
| `v` | NORMAL | Enter VISUAL mode |
| `Esc` | VISUAL | Back to NORMAL |
| `d` | VISUAL | Annotate: delete |
| `c` | VISUAL | Annotate: replace |
| `r` | VISUAL | Annotate: comment |
| `i` | VISUAL | Annotate: insert after |
| `Tab` / `shift+tab` | NORMAL | Switch document tab |
| `a` | NORMAL | Approve and submit |
| `g` | NORMAL | Request content regen |
| `s` | NORMAL | Submit with annotations |
| `q` | NORMAL | Quit / back |

---

## HITL 4 — Profile Updates

**What the reviewer does:** See exactly what fields would change in the profile JSON.
Approve or reject the whole batch — no per-field editing.

### Layout: diff view

```
┌───────────────────────────────────────────────────────────────┐
│  Profile Update Review  ·  3 proposed changes                 │
├───────────────────────────────────────────────────────────────┤
│  skills.languages                           from: HITL 1     │
│    WAS  ["Python", "Go"]                                      │
│    NOW  ["Python", "Go", "Rust"]                              │
│                                                               │
│  experience[0].highlights                   from: HITL 3     │
│    WAS  "Led backend team"                                    │
│    NOW  "Led backend team of 8 engineers"                     │
│                                                               │
│  summary.tagline                            from: HITL 3     │
│    WAS  (empty)                                               │
│    NOW  "Senior Python Engineer, 7 years"                     │
└───────────────────────────────────────────────────────────────┘
│  ⚠ Approving writes to profile JSON on disk                  │
│  [Approve & Write (a)]          [Reject All (r)]              │
```

- Read-only diff using `Static` with Rich markup (`[red]WAS[/]` / `[green]NOW[/]`)
- Single binary decision — no per-field editing
- Warning label before the action bar

---

## What Textual can and cannot do

| Feature | Textual |
|---------|---------|
| Master-detail layout | `Horizontal` + fixed-width left + `1fr` right |
| Scrollable index list | `ListView` or `Vertical` with `ScrollableContainer` |
| Tabbed documents | `TabbedContent` / `Tabs` |
| Markdown rendering | `Markdown` widget |
| Line-wise cursor + selection | Custom widget with line `Static`s + CSS classes |
| Modal overlays | `ModalScreen` via `push_screen(..., callback)` |
| Multi-line editing | `TextArea` |
| Per-character span annotation | **Not possible** (terminal has no DOM / hit-testing) |
| Drag-and-drop reorder | **Not possible** — use shift+j/k instead |

### Why span-level annotation is out of scope for Textual

Span-level annotation (select any word within a sentence, like plannotator's
`web-highlighter`) requires the runtime to know the screen coordinates of each
character so a highlight layer can be overlaid. Browsers have this; terminals do not.
Textual's widget tree operates on a character grid with no equivalent primitive.

Line-wise selection covers the practical needs for CV/letter review. Most edits are
paragraph-level ("rewrite this sentence", "cut this bullet").

---

## Data wrangling per stage

### HITL 1 — `match_edges`

```json
{ "matches": [{ "requirement_id", "profile_evidence_ids", "match_score", "reasoning" }] }
```

Requirement **text** is absent — only `requirement_id`. The text lives in
`job_kg.hard_requirements[].text` and `job_kg.soft_context[].text`.
`MatchBus.load_current_review_surface()` already enriches the payload with
`job_kg` and `job_delta`; `ReviewScreen` builds a `_requirement_lookup` dict
from it. No new wrangling needed.

### HITL 2 — `blueprint`

```json
{
  "application_id", "strategy_type", "chosen_strategy", "job_title", "source",
  "sections": [{ "section_id", "logical_train_of_thought", "section_intent", ... }]
}
```

Two things to handle in the UI:

- `logical_train_of_thought` is a **mixed list**: requirement refs (`"R01"`),
  evidence refs (`"EXP001"`), and free-form tags (`"SOFT_SKILL_LEARNING"`).
  Render them as-is rather than trying to resolve them all.
- The `sections` list is **flat across all documents** — CV sections
  (`summary`, `experience`, `skills`) and letter sections
  (`letter_intro`, `letter_core`, `letter_close`) and email (`email_body`) are
  in the same array. Group or label by document prefix in the UI.

### HITL 3 — `markdown_bundle`

```json
{ "cv_full_md": "...", "letter_full_md": "...", "email_body_md": "...", "rendering_metadata": {} }
```

All three fields are **flat strings** — the `DraftedDocument.sections_md` dict
is collapsed by assembly time. Each field requires different splitting:

**CV** (`cv_full_md`): uses Pandoc fenced div syntax for structured blocks:

```
::: {.job role="Data Scientist" org="Acme" dates="2020-01 - Present" location=""}
- Built and deployed ML pipelines.
:::
```

Text outside fences (summary, skills bullets) is plain markdown separated by
`\n\n`. The parser identifies three segment types: `paragraph`, `job`,
`education`.

**Letter / email**: plain text split on `\n\n` → `paragraph` segments only.

#### DocumentSegment

Implemented in `src/review_ui/document_parser.py`:

```python
@dataclass
class DocumentSegment:
    segment_id: str          # stable patch target: "cv:job:0", "letter:paragraph:2"
    doc_type: DocType        # "cv" | "letter" | "email"
    segment_type: SegmentType  # "paragraph" | "job" | "education"
    raw_text: str            # original text (used in patch payloads)
    display_lines: list[str] # human-readable lines for the editor widget
    line_start: int          # index in ParsedDocument.all_lines
    line_end: int            # inclusive
    meta: dict               # fence attrs for job/education, empty for paragraph
```

Job/education fence blocks are humanised to readable header lines:
```
Data Scientist  ·  Acme Corp  ·  2020-01 - Present
  - Built and deployed ML pipelines.
```

#### Segment IDs as patch targets

`segment_id` is used directly as `GraphPatch.target_id`. There are no
pre-existing section IDs in `markdown_bundle` — IDs are generated at parse
time and are stable as long as the bundle content does not change.

#### Entry point

```python
from src.review_ui.document_parser import parse_bundle

parsed = parse_bundle(surface.payload)  # dict[DocType, ParsedDocument]
cv_doc = parsed["cv"]
seg = cv_doc.segment_for_line(cursor_line)    # None if out of range
segs = cv_doc.segments_in_range(anchor, cursor)  # for visual selection
```

### HITL 4 — `profile_updater`

```json
{ "updates": [{ "field_path", "old_value", "new_value", "source_stage", "approved" }] }
```

`field_path` is a dot-separated path into the profile JSON
(e.g. `"skills.languages"`). Render as a two-column diff
(`[red]WAS[/]` / `[green]NOW[/]`). No wrangling beyond
`ProfileUpdateRecord` validation.

---

## Screen routing

```
MatchReviewApp.on_mount()
    │
    ├── source + job_id given ──► load surface ──► route by surface.stage
    │       hitl_1 ──► MatchReviewScreen   (new master-detail, replaces ReviewScreen)
    │       hitl_2 ──► BlueprintReviewScreen
    │       hitl_3 ──► ContentReviewScreen  (vim visual editor)
    │       hitl_4 ──► ProfileDiffScreen
    │
    └── no args ──► JobExplorerScreen
                        └── row selected with review pending ──► same routing
```

`MatchBus.load_current_review_surface()` already resolves the stage; the app uses
`surface.stage` to pick the screen class.

### HITL 1 screen: replace, don't refactor

The existing `ReviewScreen` has a fundamentally different layout (single scrolling card
list) and a submit bug (#5). Rather than patching it in-place, implement a new
`MatchReviewScreen` with the master-detail layout and correct patch serialization.
`ReviewScreen` can be deleted once the new class is wired in.

---

## Open issues

- [#5](https://github.com/jpcosec/podyulsyot3001/issues/5) Per-match outcomes not sent to LangGraph
- [#7](https://github.com/jpcosec/podyulsyot3001/issues/7) No UI for stages 2, 3, 4
- [#8](https://github.com/jpcosec/podyulsyot3001/issues/8) `style_regen` unimplemented
