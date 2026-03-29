# 🧠 Core Services

Modular infrastructure for data management, pipeline execution, and LangGraph API interaction.

---

## 🏗️ Architecture & Features

The core layer provides the glue between the high-level TUI/CLI and the low-level processing graphs.

- **`LangGraphAPIClient`**: `src/core/api_client.py` 
  - Handles thread discovery and state resumption via the `langgraph-sdk`.
  - **Dynamic Port Autodetection**: Automatically scans for running LangGraph processes (ports 8124, 8123, etc.) using `ps` and health checks.
- **`DataManager`**: `src/core/data_manager.py`
  - Centralizes workspace pathing, JSON artifact persistence, and job indexing.
- **`ProfileManager`**: `src/core/profile.py`
  - Manages the user's CV/profile data for matching.

---

## ⚙️ Configuration

Required environment variables:

```bash
# Optional: explicitly set API location (defaults to autodetection)
export LANGGRAPH_API_URL="http://localhost:8124"
```

---

## 🚀 CLI / Usage

Most core features are consumed by the unified CLI and the review TUI. The authoritative command definitions live in `src/cli/main.py`.

Direct usage of the API client:

```python
from src.core.api_client import LangGraphAPIClient

client = LangGraphAPIClient()  # Autodetects port
jobs = await client.list_jobs()
```

---

## 📝 Data Contract

The core layer exposes infrastructure contracts rather than product schemas:

- job artifact persistence and refs are defined by `src/core/data_manager.py` and documented in `docs/runtime/data_management.md`
- profile base data is validated by `src/core/profile.py`
- LangGraph thread metadata is normalized by `LangGraphAPIClient` for CLI/TUI consumption

---

## 🛠️ How to Add / Extend

1. **New API Action**: Add a method to `LangGraphAPIClient` using the underlying SDK client and keep CLI/TUI state mutations API-only.
2. **New Data Path**: Register the path in `DataManager` and update `docs/runtime/data_management.md`.
3. **New Profile Surface**: Add validation to `src/core/profile.py` rather than leaving raw profile blobs in callers.

---

## 💻 How to Use

Check the health of the API:

```bash
python -m src.cli.main api status
```

---

## 🚑 Troubleshooting

- **`LangGraph API not reachable`** -> Start it with `python -m src.cli.main api start` and confirm `python -m src.cli.main api status` returns a URL.
- **Permission denied during process scan** -> Ensure the current user can inspect their own processes, or set `LANGGRAPH_API_URL` explicitly.
