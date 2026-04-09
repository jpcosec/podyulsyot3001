# Gemini CLI — Project Context (Unified Automation)

This project is a high-performance **Browser Automation Worktree** utilizing the **Ariadne Semantic Layer** to provide a backend-neutral source of truth for all automation tasks (Scraping, Applying, and Session Management).

## Project Overview

-   **Core Architecture**: Uses the **Ariadne Semantic Layer** to separate **what** the automation intends to do (States, Tasks, Paths) from **how** it is executed by specific motors.
-   **Execution Motors**:
    -   **Crawl4AI**: Compiles Ariadne paths into procedural scripts for high-speed, headless automation (Playwright-based).
    -   **BrowserOS**: Uses an external runtime (AppImage) for resilient, fuzzy text-based interaction and human-in-the-loop (HITL) support.
    -   **OpenBrowser**: An LLM-based agent (LangGraph/Gemini) used to intelligently explore portals and record new automation flows.
-   **Primary Technologies**: Python 3.9+, Pydantic (Contracts), LangGraph (Agents), Playwright/Crawl4AI, FastAPI, and the BrowserOS MCP/CLI runtime.

## Building and Running

### Core CLI Commands
The main entry point is `src/automation/main.py`.

```bash
# 1. Scrape jobs from a portal (discovery)
python -m src.automation.main scrape --source <stepstone|xing|tuberlin> --limit 5

# 2. Apply to a job (Default: BrowserOS backend)
python -m src.automation.main apply --source <xing|stepstone|linkedin> --job-id <id> --cv <path>

# 3. Apply via Crawl4AI backend (High speed)
python -m src.automation.main apply --backend crawl4ai --source xing --job-id <id> --cv <path>

# 4. Dry-run (Validate path without submitting)
python -m src.automation.main apply --source xing --job-id <id> --cv <path> --dry-run

# 5. Verify BrowserOS Runtime
python -m src.automation.main browseros-check

# 6. Promote a recorded trace to a canonical portal map
python -m src.automation.main promote --trace-id <id> --portal <name>
```

### External Runtime: BrowserOS
BrowserOS is required for the `apply` and `browseros-check` commands.
-   **Launch**: `/home/jp/BrowserOS.AppImage --no-sandbox`
-   **Stable URL**: `http://127.0.0.1:9000` (Front door to MCP and Chat endpoints).

## Development Conventions

### 1. "Ariadne First" Principle
-   Every new portal flow MUST be defined as an `AriadnePortalMap` in JSON at `src/automation/portals/<portal>/maps/<flow>.json`.
-   Avoid hardcoding portal-specific logic in motor implementations.
-   Use `AriadneTarget` to provide both `css` (for Crawl4AI) and `text` (for BrowserOS fuzzy matching).

### 2. Coding Standards
-   **Types**: Rigorous use of Python type hints and `from __future__ import annotations`.
-   **Data Models**: All contracts must be Pydantic `BaseModel` classes (defined in `src/automation/ariadne/models.py` and `contracts.py`).
-   **Documentation**: Public methods should have clear docstrings. Architectural decisions are documented in `docs/automation/`.
-   **Logging**: Use the structured logging initialized in `src/automation/main.py`. Logs are stored in `logs/automation/`.

### 3. Testing Practices
Tests are split into `unit` and `integration` suites using `pytest`.
-   **Unit Tests**: `python -m pytest tests/unit/automation/`
-   **Specific Module**: `python -m pytest tests/unit/automation/ariadne/`
-   **Integration Tests**: `python -m pytest tests/integration/`

### 4. Scrape Pipeline & Normalization
The system follows a tiered extraction and normalization pipeline to ensure data integrity and backend neutrality:
- **Multi-Stage Persistence**: Scrape results are persisted in three distinct stages under `data/jobs/<source>/<job_id>/`:
  - `raw.json`: Direct, unmodified output from the extraction motor.
  - `cleaned.json`: The payload after semantic normalization and field recovery.
  - `extracted.json`: The final, validated `JobPosting` artifact.
- **Normalization Ownership**: All semantic cleanup (e.g., location normalization, employment type detection, bullet point mining) is strictly owned by Ariadne in `src/automation/ariadne/job_normalization.py`.
- **Motor Delegation**: Execution motors (Crawl4AI/BrowserOS) MUST delegate to the Ariadne normalization module. They should not implement their own portal-specific cleanup rules.
- **Field Recovery**: The normalization layer attempts to recover missing or "noisy" fields using listing metadata and hero-section markdown before failing validation.

## Key Directory Structure

-   `src/automation/ariadne/`: The "Brain" — Path normalization, navigation logic, and semantic models.
-   `src/automation/motors/`: The "Engines" — Crawl4AI and BrowserOS providers.
-   `src/automation/portals/`: The "Maps" — JSON definitions for job portal flows.
-   `data/jobs/`: Artifact storage for scraped jobs and application results (`apply_meta.json`).
-   `docs/automation/`: Deep-dive architectural documentation (Start with `ariadne_semantics.md`).

## Issue Management & Design Cycle

The project follows a pluggable design cycle for managing and resolving issues, centered around `plan_docs/issues/`.

### 1. The Design Cycle
- **Stage 1: Mapping**: Issues are documented as `.md` files in:
  - `plan_docs/issues/gaps/`: For existing but broken or incomplete features.
  - `plan_docs/issues/unimplemented/`: For designed but not-yet-built features.
- **Stage 2: Indexing**: Before work begins, `plan_docs/issues/Index.md` must be generated/updated via a process involving a legacy audit, atomization (splitting large tasks), contradiction checks, and dependency graphing.

### 2. Working Rules for Agents (Execution)
When assigned an issue from `Index.md`, follow these mandatory steps:
1.  **Validate**: Confirm the issue exists or the requirement is clear.
2.  **Implement**: Apply the fix/feature following project conventions.
3.  **Test**: Verify existing tests still pass; add new tests for the change.
4.  **Log**: Update `changelog.md` with the resolution.
5.  **Cleanup**: Delete the issue file from `plan_docs/issues/` and remove its entry from `Index.md`.
6.  **Commit**: Make a clean commit describing the fix.

## Extraction Fallbacks
Controlled by the environment variable `AUTOMATION_EXTRACTION_FALLBACKS`:
-   `browseros`: Uses BrowserOS `/chat` for semantic extraction (Rescue).
-   `llm`: Uses Crawl4AI Gemini rescue path (Requires `GOOGLE_API_KEY`).
