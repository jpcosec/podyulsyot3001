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

Launch the full workstation:

```bash
./scripts/postulator.sh
```

Launch only the API:

```bash
./scripts/launch_api.sh
```

---

## 🛠️ How to Add / Extend

1. **New Automation**: Create a `.sh` or `.py` script and add it to this directory.
2. **Metadata Enrichment**: If a script interacts with the API, use the `LangGraphAPIClient` from `src.core.api_client`.

---

## 🚑 Troubleshooting

- **`Permission denied`**: Ensure scripts have execute permissions (`chmod +x scripts/*.sh`).
- **`Port already in use`**: The scripts will attempt to find an open port, but you can override by setting `export LANGGRAPH_API_URL`.
