# `src/automation/motors/` — Motor Adapter Layer

## 🏗️ Architecture

This package contains backend-specific execution adapters.

- `crawl4ai/` — Unified Replayer for the Crawl4AI engine.
- `browseros/cli/` — Unified Replayer for the BrowserOS (MCP) engine.
- `browseros/agent/` — (Conceptual) Agentic control of BrowserOS.
- `os_native_tools/` — (Conceptual) Stub for OS-level native automation.
- `vision/` — (Conceptual) Stub for vision-first/AI-vision automation.
- Each backend exposes a `MotorProvider` that opens a backend-specific `MotorSession`.
- Motors execute steps and observations; they do not load maps or decide navigation policy.

## ⚙️ Configuration

- Crawl4AI motor configuration is assembled in `crawl4ai/browser_config.py`.
- BrowserOS motor configuration is handled by `browseros/cli/client.py` and the local BrowserOS runtime.
- Motor selection is done through `--backend` in `src/automation/main.py`.

## 📚 External References

- `docs/reference/external_libs/browseros/readme.txt` — BrowserOS interface index
- `docs/reference/external_libs/browseros/recording_for_ariadne.md` — BrowserOS recording strategy for Ariadne
- `docs/reference/external_libs/crawl4ai/readme.txt` — Crawl4AI reference index

## 🚀 CLI / Usage

```bash
python -m src.automation.main apply --backend browseros --source xing --job-id 123 --cv cv.pdf --dry-run
python -m src.automation.main apply --backend crawl4ai --source linkedin --job-id 123 --cv cv.pdf --dry-run
```

## 📝 Data Contract

- Motors consume `AriadneStep` plus a replay context from the Ariadne layer.
- Motors must satisfy the `MotorProvider` and `MotorSession` protocols from `src/automation/ariadne/motor_protocol.py`.
- Motors return control to `AriadneSession`, which persists `ApplyMeta`.

## 🛠️ How to Add / Extend

1. Implement a provider class that satisfies `MotorProvider`.
2. Implement a session class that satisfies `MotorSession.observe()` and `MotorSession.execute_step()`.
3. Keep portal knowledge in JSON maps and Ariadne models; do not hardcode portal flow logic in the motor.
4. Add tests under `tests/unit/automation/motors/` for observation and step execution behavior.

## 💻 How to Use

```python
from src.automation.motors.crawl4ai.apply_engine import C4AIMotorProvider
from src.automation.motors.browseros.cli.backend import BrowserOSMotorProvider

c4ai = C4AIMotorProvider()
browseros = BrowserOSMotorProvider()
```

Pass either provider into `AriadneSession.run()`.

## 🚑 Troubleshooting

- If a motor cannot find targets, verify the corresponding map target includes the selector type that backend supports.
- If BrowserOS replay fails on the first step, confirm the page was opened and navigation happened in the current session.
- If Crawl4AI observation returns empty data, inspect session reuse and injected hooks in the active replay path.
