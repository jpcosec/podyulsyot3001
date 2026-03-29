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

Most core features are consumed by the CLI or TUI. 

Direct usage of the API client:

```python
from src.core.api_client import LangGraphAPIClient

client = LangGraphAPIClient()  # Autodetects port
jobs = await client.list_jobs()
```

---

## 📝 Data Contract

- `ThreadState` — Extracted from LangGraph state dicts to provide clean metadata (`job_id`, `status`, `source`).
- `Checkpoint` — Pydantic-validated representation of point-in-time graph state.

---

## 🛠️ How to Add / Extend

1. **New API Action**: Add a method to `LangGraphAPIClient` using the underlying `self.client` (LangGraph SDK).
2. **New Data Path**: Register the path in `DataManager` to ensure it is governed by the workspace standards.

---

## 💻 How to Use

Check the health of the API:

```bash
# Via postulator.sh health check logic
lsof -i:8124
```

---

## 🚑 Troubleshooting

- **`[❌] LangGraph API not found`**: Ensure `langgraph dev` is running. `postulator.sh` will attempt to start it on port 8124 if missing.
- **Permission Denied (ps scan)**: Ensure the user has permissions to see their own processes for port autodetection.
