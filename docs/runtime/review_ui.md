# Review UI (TUI)

The Review UI is a Terminal User Interface (TUI) built with [Textual](https://textual.textualize.io/) that provides human-in-the-loop (HITL) review for the generate_documents_v2 pipeline.

## Launch

```bash
python -m src.cli.main review --source xing --job-id 150542106
```

Or without arguments to browse pending reviews:
```bash
python -m src.cli.main review
```

## Architecture

```
src/review_ui/
├── app.py           # MatchReviewApp - main Textual application
├── bus.py           # MatchBus - bridge between TUI and LangGraph API
└── screens/
    ├── review_screen.py      # ReviewScreen - main review interface
    └── explorer_screen.py    # JobExplorerScreen - browse pending reviews
```

### Data Flow

```
LangGraph API (paused at HITL node)
         │
         ▼
MatchBus._pending_review_stage() ──► queries thread state, finds pending node
         │
         ▼
MatchBus.load_current_review_surface() ──► loads artifact from disk
    • match_edges → includes job_kg for requirement text
    • job_delta → additional context
         │
         ▼
ReviewScreen._render_surface() ──► populates UI with match cards
```

### Key Components

**MatchReviewApp** (`app.py`)
- Root Textual app, handles screen routing
- Two modes: direct access (`--source --job-id`) or explorer mode

**MatchBus** (`bus.py`)
- Bridge between Textual event loop and LangGraph API
- `load_current_review_surface()` - reads artifact from disk, enriches with job_kg
- `resume_with_review()` - sends approve/reject + patches back to LangGraph

**ReviewScreen** (`review_screen.py`)
- Main review interface showing match cards
- Handles keyboard shortcuts and button clicks

## UI Layout

```
┌─────────────────────────────────────────────────────────┐
│ [Header] Stage: Match Evidence Review · xing/150542106 │
├─────────────────────────────────────────────────────────┤
│ [Summary] Data Scientist · 2 strong · 1 weak · 6 total │
├─────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [R01]  90%  Strong Python experience required      │ │
│ │ Evidence: SKILL_Python, EXP001                      │ │
│ │ Reasoning: Profile shows Python + ML experience     │ │
│ │ [✓] [✗] [Edit]                                     │ │
│ └─────────────────────────────────────────────────────┘ │
│ ┌─────────────────────────────────────────────────────┐ │
│ │ [R02]  30%  Java experience nice to have            │ │
│ │ Evidence: SKILL_Java                                │ │
│ │ Reasoning: Java listed but not for data science    │ │
│ │ [✓] [✗] [Edit]                                     │ │
│ └─────────────────────────────────────────────────────┘ │
├─────────────────────────────────────────────────────────┤
│ [+ Approve All] [- Reject All] [Submit review »]        │
└─────────────────────────────────────────────────────────┘
```

## Keybindings

| Key | Action | Description |
|-----|--------|-------------|
| `j` | cursor_down | Move to next match |
| `k` | cursor_up | Move to previous match |
| `a` | approve | Approve all matches |
| `r` | reject | Reject all matches |
| `s` | submit | Submit review to LangGraph |
| `q` | quit | Exit the TUI |

Per-match buttons:
- `✓` - approve individual match
- `✗` - reject individual match  
- `Edit` - modify score/reasoning (placeholder)

## HITL Stages

The UI supports multiple review stages:

| Stage | Artifact | Title |
|-------|----------|-------|
| `hitl_1_match_evidence` | match_edges | Match Evidence Review |
| `hitl_2_blueprint_logic` | blueprint | Blueprint Review |
| `hitl_3_content_style` | markdown_bundle | Content And Style Review |
| `hitl_4_profile_updates` | profile_updater | Profile Update Review |

## Testing

Run unit tests:
```bash
python -m pytest tests/unit/review_ui -v
```

Tests cover:
- Bus data loading (job_kg enrichment)
- Screen bindings and CSS
- Initial state validation
