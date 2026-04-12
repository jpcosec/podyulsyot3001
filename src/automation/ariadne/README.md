# Ariadne

The semantic layer for browser automation. Provides the graph orchestrator, models, modes, and execution interfaces.

---

## 🏗️ Architecture & Features

- **`ariadne/graph/`**: LangGraph orchestration (`orchestrator.py`, `nodes/agent.py`)
- **`ariadne/models.py`**: `AriadneMap`, `AriadneState`, `AriadneEdge`
- **`ariadne/contracts/base.py`**: `AriadneIntent`, `AriadneTarget`, `Executor` contracts
- **`ariadne/modes/`**: Mode system (`DefaultMode`, portal-specific modes)
- **`ariadne/capabilities/`**: Hinting, recording

See `docs/ariadne/` for architecture docs.

## ⚙️ Configuration

- `GEMINI_API_KEY` or `GOOGLE_API_KEY` for `DefaultMode`
- Modes defined in `src/automation/portals/modes/`

## 📝 Data Contract

- `src/automation/ariadne/models.py` — canonical models
- `src/automation/ariadne/contracts/base.py` — executor contracts