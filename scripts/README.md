# 📜 Operational Scripts

Automation and entry point scripts for the job application pipeline.

---

## 🏗️ Architecture & Features

These scripts wrap the core library and CLI to provide a more ergonomic or automated experience.

- **`postulator.sh`**: The main workstation entry point.
  - Performs health checks on the LangGraph API.
  - Auto-launches the API server if missing.
  - Launches the Job Manager TUI in Explorer mode.
- **`launch_api.sh`**: Dedicated script to start the LangGraph development server.
  - Features smart port detection to avoid conflicts.
- **`run_pipelines.py`**: Batch processing script for running multiple job pipelines sequentially.

---

## ⚙️ Configuration

Requires `langgraph` CLI for the API server.

```bash
pip install langgraph-cli
```

---

## 🚀 CLI / Usage

These scripts are wrappers around the API-first CLI. The authoritative control-plane logic lives in `src/cli/main.py`.

Launch the full workstation:

```bash
./scripts/postulator.sh
```

Launch only the API:

```bash
./scripts/launch_api.sh
```

Equivalent CLI entry point:

```bash
python -m src.cli.main api start
```

---

## 📝 Data Contract

These scripts do not define their own schemas. They delegate to:

- `LangGraphAPIClient` in `src/core/api_client.py` for API startup and thread control
- `MatchReviewApp` in `src/review_ui/app.py` for the review workstation
- `DataManager` in `src/core/data_manager.py` for job artifact paths where applicable

---

## 🛠️ How to Add / Extend

1. **New Automation**: Create a `.sh` or `.py` script and add it to this directory.
2. **Metadata Enrichment**: If a script interacts with the API, use the `LangGraphAPIClient` from `src.core.api_client`.

---

## 💻 How to Use

```bash
# Start or reuse the API
./scripts/launch_api.sh

# Open the workstation
./scripts/postulator.sh
```

---

## 🚑 Troubleshooting

- **`Permission denied`** -> Ensure scripts have execute permissions (`chmod +x scripts/*.sh`).
- **API still does not come up** -> Run `python -m src.cli.main api start` directly to isolate whether the problem is in the shell wrapper or the Python control plane.
- **Wrong API URL** -> Export `LANGGRAPH_API_URL` explicitly before calling the script.
