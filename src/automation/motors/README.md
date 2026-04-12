# Motors

Execution engines for browser automation. Each motor implements the `Executor` contract.

---

## 🏗️ Architecture & Features

- **`motors/browseros/`**: BrowserOS CLI executor (MCP-based)
- **`motors/crawl4ai/`**: Crawl4AI executor (Playwright-based)
- Resolved via `motors/registry.py`

## ⚙️ Configuration

- `BROWSEROS_BASE_URL` — defaults to `http://127.0.0.1:9000`

## 📝 Data Contract

- `src/automation/ariadne/contracts/base.py` — `Executor` contract