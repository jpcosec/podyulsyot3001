# 🖥️ Unified Job Manager TUI

Textual-based terminal workstation for the job application pipeline. Provides a centralized "Explorer" for fleet management and a focused "Review" screen for HITL gates.

---

## 🏗️ Architecture & Features

A multi-screen Textual application decoupled from the backend via an async bus.

- **Unified Entry Point (`MatchReviewApp`)**: `src/review_ui/app.py`
- **Job Explorer Screen**: `src/review_ui/screens/explorer_screen.py`
  - Lists all threads from the LangGraph API.
  - Displays dynamic status, source, and metadata.
- **Review Screen**: `src/review_ui/screens/review_screen.py`
  - Focused HITL gate for approving/rejecting match proposals.
- **Communication Bus (`MatchBus`)**: `src/review_ui/bus.py`
  - Bridges TUI events to the review artifact store and the current control-plane client.

---

## ⚙️ Configuration

Requires `textual` and `langgraph-sdk`.

The TUI uses the LangGraph API as its only stateful control plane. `postulator review` and `./scripts/postulator.sh` will start or reuse the API before opening the UI.

---

## 🚀 CLI / UI / Usage

Launch the workstation. The CLI parser and direct review entry points live in `src/cli/main.py`.

Launch the workstation:

```bash
./scripts/postulator.sh
python -m src.cli.main review
```

Keyboard bindings (Explorer):
- `ENTER`: Open the selected job for review.
- `R`: Refresh the job list.
- `Q`: Quit.

Keyboard bindings (Review):
- `Ctrl+A`: Approve all rows.
- `S`: Submit and continue.
- `ESC`: Return to Explorer.

---

## 📝 Data Contract

The review UI depends on typed contracts from the match skill module and API metadata from the control plane:

- review-specific contracts are consumed through `src/review_ui/bus.py` and `src/review_ui/screens/review_screen.py`
- thread/job metadata is consumed by `src/review_ui/screens/explorer_screen.py`
- persisted review artifacts live under `data/jobs/<source>/<job_id>/nodes/match_skill/review/`

---

## 🛠️ How to Add / Extend

1. **New Screen**: Add it under `src/review_ui/screens/` and register it from `src/review_ui/app.py`.
2. **New Explorer Metadata**: Extend the control-plane client consumed by `src/review_ui/bus.py`, then render it in `src/review_ui/screens/explorer_screen.py`.
3. **New Review Actions**: Route them through `MatchBus` in `src/review_ui/bus.py`; do not mutate LangGraph state locally.

---

## 💻 How to Use

```bash
# Normal workflow
./scripts/postulator.sh
```

To review a specific job directly bypassing the explorer:
```bash
python -m src.cli.main review --source xing --job-id 12345
```

To start the API explicitly:

```bash
python -m src.cli.main api start
```

---

## 🚑 Troubleshooting

- **Explorer shows no jobs** -> No API-backed runs exist yet. Start them with `python -m src.cli.main run-batch --sources xing --limit 5`, then reopen the TUI.
- **Direct review mode fails with missing thread** -> The thread was never created through the API, or the `source/job_id` pair is wrong. Verify it appears in explorer mode first.
- **TUI connects to the wrong server** -> Export `LANGGRAPH_API_URL="http://localhost:XXXX"` before launching `postulator review`.
- **API fails to start from the helper script** -> Inspect `logs/langgraph_api.log` and retry with `python -m src.cli.main api start` to isolate the control-plane startup path.
