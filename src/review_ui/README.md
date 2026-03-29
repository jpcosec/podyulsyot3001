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
  - Bridges TUI events to the `LangGraphAPIClient` or local checkpoints.

---

## ⚙️ Configuration

Requires `textual` and `langgraph-sdk`.

The TUI uses the LangGraph API as its only stateful control plane. `postulator review` and `./scripts/postulator.sh` will start or reuse the API before opening the UI.

---

## 🚀 CLI / UI / Usage

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

- **State Discovery**: Consumes thread metadata from `LangGraphAPIClient.list_jobs()`.
- **HITL Payload**: `ReviewPayload` sent back to the graph to resume execution.

---

## 🛠️ How to Add / Extend

1. **New Screen**: Add to `src/review_ui/screens/` and register in `app.py`.
2. **New Column in Explorer**: Update `_populate_table` in `explorer_screen.py`.
3. **Advanced Filtering**: Implement a `FilterWidget` in `widgets/` and bind it to the Explorer's data table.

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

- **Explorer shows no jobs**: Ensure you have launched at least one job through the API-backed CLI, for example `python -m src.cli.main run-batch --sources xing --limit 5`.
- **Port Conflict**: If the TUI connects to the wrong API, explicitly set `export LANGGRAPH_API_URL="http://localhost:XXXX"`.
- **API Not Detected**: Check `logs/langgraph_api.log` if `postulator.sh` failed to start the server.
