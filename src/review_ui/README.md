# 🖥️ Review UI

Textual-based terminal UI for the match skill HITL review gate. Loads the persisted `ReviewSurface`, lets the operator make per-requirement decisions, and resumes the paused LangGraph thread via `MatchBus`.

---

## 🏗️ Architecture & Features

A thin Textual application wired to LangGraph and disk via a decoupled bus layer.

- Application root (`MatchReviewApp`): `src/review_ui/app.py`
- LangGraph + disk bridge (`MatchBus`): `src/review_ui/bus.py`
- HITL review screen (`ReviewScreen`): `src/review_ui/screens/review_screen.py`
- Per-requirement decision widget (`MatchRow`): `src/review_ui/widgets/match_row.py`

`MatchBus` has no Textual imports — it can be instantiated and tested without a running app. All blocking I/O (disk reads, `app.invoke`) runs in Textual worker threads so the event loop stays responsive.

Flow: `ReviewScreen` mounts → `MatchBus.load_current_review_surface()` loads `review/current.json` → one `MatchRow` per requirement → operator makes decisions → `ReviewScreen.action_submit()` builds `ReviewPayload` → `MatchBus.resume_with_review()` resumes the graph thread.

---

## ⚙️ Configuration

No environment variables. Requires:

```bash
pip install textual
```

The LangGraph app and `MatchArtifactStore` are passed in at construction — no config file needed.

---

## 🚀 CLI / UI / Usage

The TUI is launched through the unified CLI `review` command in `src/cli/main.py`, or programmatically by assembling a `MatchBus` and passing it to `MatchReviewApp`.

Keyboard bindings (active in `ReviewScreen`):

| Key | Action |
|-----|--------|
| `Ctrl+A` | Approve all rows |
| `Ctrl+R` | Reject all rows |
| `S` | Submit review |
| `Q` | Quit |

---

## 📝 Data Contract

Contracts are defined in `src/ai/match_skill/contracts.py` (the review UI consumes match_skill contracts directly):

- `ReviewSurface` / `ReviewSurfaceItem` — loaded from disk and rendered as rows
- `ReviewPayload` / `ReviewItemDecision` — built by the UI and sent back to the graph
- `ReviewDecision` — the per-item decision enum (`approve`, `reject`, `request_regeneration`)

`MatchBus` interface: `bus.py` — `load_current_review_surface(source, job_id)` and `resume_with_review(payload)`.

---

## 🛠️ How to Add / Extend

1. **New screen**: create `src/review_ui/screens/{name}.py` implementing `textual.screen.Screen`, then push it from `MatchReviewApp`.
2. **New widget**: create `src/review_ui/widgets/{name}.py` and mount it from the relevant screen.
3. **New bus action**: add a method to `MatchBus` in `src/review_ui/bus.py`. Keep it free of Textual imports so it remains testable in isolation.

---

## 💻 How to Use

```python
from src.ai.match_skill.graph import build_match_skill_graph
from src.ai.match_skill.storage import MatchArtifactStore
from src.review_ui.bus import MatchBus
from src.review_ui.app import MatchReviewApp
from langgraph.checkpoint.sqlite import SqliteSaver

store = MatchArtifactStore("output/match_skill")
with SqliteSaver.from_conn_string("output/match_skill/checkpoints.db") as checkpointer:
    app = build_match_skill_graph(artifact_store=store, checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "stepstone_12345"}}
    bus = MatchBus(store=store, app=app, config=config)
    MatchReviewApp(bus=bus, source="stepstone", job_id="12345").run()
```

---

## 🚑 Troubleshooting

- **`FileNotFoundError: No review surface found`** — run the match skill first (`src/ai/match_skill/main.py`) to generate `review/current.json` before launching the TUI.
- **Graph resume fails** — ensure the `thread_id` in `MatchBus.config` matches the thread started by `run_match_skill`.
