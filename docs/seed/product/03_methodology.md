# Documentation and Development Methodology: PhD 2.0

## 1. Design Philosophy: "Determinism and Decoupling"

The system is governed by absolute data transparency and interface independence.

### Progressive Interface Architecture (CLI > API > UI)

- All functionality must be born in Backend/CLI as a deterministic function.
- The API acts exclusively as a data bridge to the filesystem.
- The UI is a visualization and correction layer, never the primary business logic.

### Separation of Functions

- **Deterministic Functions**: File processing, I/O, PDF rendering, and provenance handling (`src/core/`).
- **AI-Based Functions**: LangGraph nodes that interact with LLMs (`src/nodes/`). Must be replaceable and isolated from persistence logic.
- **Anti-Hardcoding**: Strict use of Contracts (`contract.py`) in each node to define inputs and outputs, allowing the pipeline to be modular and scalable.

## 2. Documentation Structure and "Lateral Links"

Documentation is organized as a graph where context flows in a controlled manner.

### Folder Hierarchy

- `docs/runtime/`: Current technical truth. What the code does today.
- `plan/`: Target state design. References `docs/` to propose changes.

### Link Rules

- **Temporal Unidirectionality**: `plan/` → references to `docs/` (allowed). `docs/` → references to `plan/` (prohibited, to avoid contaminating current truth).
- **Lateral Context**: Encouraged links between domains (e.g., a UI doc in `docs/ui/` can link to DB spec in `docs/architecture/`) to give complete context to developers.

### "Hard" vs. "Soft" Documentation

- Detailed technical documentation lives close to code in local `README.md` files.
- Conceptual maps and `canonical_map.md` live at `docs/` root as hierarchical entry points.

## 3. Stage-Based Pipeline and Human Review (HITL)

The workflow is a LangGraph where success depends on human validation at "semantic gates".

### Stage as Minimum Unit

- Each pipeline step is a node with a clear state file.

### UI Review Gates

- "Extraction" and "Matching" stages require an explicit decision (approve/reject) saved to disk before advancing to document generation.

### Comment System

- The interface must allow attaching `feedback.md` at each stage. This file is consumed by the pipeline when requesting "Regeneration".

## 4. Local Persistence and State Management

The "Database" is the filesystem (Local-First).

### Persistent DB in Files

- All application data resides in `data/jobs/<source>/<job_id>/`. This ensures portability and easy debugging.

### State Synchronization

- Pipeline state (`state.json`) is managed by LangGraph.
- Any manual edit in the UI (JSON or Markdown) overwrites the file in `data/`, triggering a state update in the backend for the next execution.
