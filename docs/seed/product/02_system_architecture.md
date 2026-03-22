# System Architecture

The system follows the "Local-First" principle, where the database is the filesystem.

## A. Data Layer (Local Filesystem)

- **Source of Truth**: `data/jobs/` folder. Each job is an independent folder containing its own history, node states, and error traces.
- **Formats**: Mainly JSON (for logical states) and Markdown (for textual content).

## B. Backend (Python Services & API)

- **LangGraph Orchestrator**: The engine that executes stages. Agnostic to whether called via CLI or API.
- **FastAPI Server**: Acts as a bridge (Data Bridge). Its function is not to manage a DB, but to read/write to the local filesystem and expose it to the UI.
- **Provenance Service**: Responsible for tracking where each piece of data comes from (link between original text and extraction).

## C. UI (React Workbench)

- **Portfolio Management**: Dashboard to view status of all applications and their metrics.
- **Job Workspace**: The "command center" for a specific application, where you navigate through the stage timeline.
- **Specialized Editors**:
  - Node Editor: For structured JSON data.
  - Text Tagger / Markdown Editor: To review evidence and edit documents.

## D. CLI (Operator Entrypoint)

- **Function**: Execution of heavy processes (massive scraping, migrations, or initial pipeline execution).
- **Synchronization**: By writing to the same files as the API, the UI updates automatically on refresh, enabling a hybrid flow (terminal for running, browser for reviewing).
