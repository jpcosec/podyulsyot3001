# Automation Runtime

## 🏗️ Architecture & Features

`src/automation/` is the runtime package for Ariadne-driven browser automation.

- `src/automation/main.py` is the CLI entrypoint for `apply`, `scrape`, and runtime checks.
- `src/automation/ariadne/` contains the graph orchestrator, contracts, modes, recording, and promotion logic.
- `src/automation/portals/` contains packaged portal maps and JSON-backed mode configuration.
- `src/automation/motors/` contains execution backends, resolved through `src/automation/motors/registry.py`.

For higher-level architecture, use `docs/ariadne/architecture_and_graph.md` and `docs/ariadne/execution_interfaces.md`.

## ⚙️ Configuration

Runtime behavior is configured through environment variables and local runtime services.

- `BROWSEROS_APPIMAGE_PATH`: path to the BrowserOS AppImage used for BrowserOS-backed flows.
- `BROWSEROS_BASE_URL`: BrowserOS base URL; defaults to `http://127.0.0.1:9000`.
- `GOOGLE_API_KEY` or `GEMINI_API_KEY`: enables Gemini-backed `DefaultMode` fallbacks.
- SQLite checkpoints and graph recordings are written under `data/ariadne/` at runtime.

## 🚀 CLI / Usage

Use `python -m src.automation.main ...` as the canonical entrypoint.

- CLI argument definitions live in `src/automation/main.py`.
- The current command parser implementation is the authoritative source for supported flags and defaults.
- Typical flows are `apply`, `scrape`, and `browseros-check`.

## 📝 Data Contract

The primary runtime contracts live in these files:

- `src/automation/contracts.py` for user/profile payloads.
- `src/automation/ariadne/models.py` for `AriadneMap`, `AriadneStateDefinition`, `AriadneEdge`, and `AriadneState`.
- `src/automation/ariadne/contracts/base.py` for executor, command, and execution-result contracts.
