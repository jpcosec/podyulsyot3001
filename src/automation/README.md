# `src/automation/` — Unified Automation Package

## 🏗️ Architecture & Features

This package provides a unified, semantic-driven browser automation system. It decouples **Path Knowledge** from **Execution Engines**, allowing for high resilience and cross-motor replay.

- **Semantic Layer (`src/automation/ariadne/`)**: Backend-neutral models for States, Tasks, and Paths.
- **AriadneSession (`src/automation/ariadne/session.py`)**: Orchestrates the apply loop, resolves portal routing, dispatches to motors, and persists results.
- **Unified Maps (`src/automation/portals/`)**: Single source of truth for portal logic in JSON.
- **Portal Routing (`src/automation/portals/*/routing.py`)**: Portal-specific branching that decides whether a job stays onsite, redirects to an ATS, or hands off to email.
- **Execution Motors (`src/automation/motors/`)**: Replayers for Crawl4AI and BrowserOS.
- **Persistence (`src/automation/storage.py`)**: Centralized artifact and metadata management.

## ⚙️ Configuration

Requires a `.env` file in the root directory with the following variables:

```env
GOOGLE_API_KEY=...       # Gemini API access
GEMINI_API_KEY=...       # Same as above
PLAYWRIGHT_BROWSERS_PATH=0
```

## 🚀 CLI / Usage

The unified CLI entry point handles both discovery and application.

```bash
# Scrape jobs
python -m src.automation.main scrape --source <portal> --limit 5

# Apply to jobs
python -m src.automation.main apply --source <portal> --job-id <id> --cv <path> --dry-run
```

Arguments are defined in the `build_parser()` function in `src/automation/main.py`.

## 📝 Data Contract

All automation models are strictly typed via Pydantic:
- **`AriadnePortalMap`**: Defines the portal's semantic landscape. See `src/automation/ariadne/models.py`.
- **`ApplyMeta`**: Records the result of an application attempt. See `src/automation/ariadne/models.py`.
- **`CandidateProfile`** and **`ExecutionContext`**: Define the runtime apply context shared by the CLI, storage, and motors. See `src/automation/contracts.py`.

## 🛠️ How to Add / Extend

1. **Map the Portal**: Create a JSON map in `src/automation/portals/<portal>/maps/easy_apply.json` using the `AriadnePortalMap` schema.
2. **Add Portal Routing**: Implement `src/automation/portals/<portal>/routing.py` so enriched ingest state resolves to an onsite Ariadne path or an explicit external/email handoff.
3. **Instantiate AriadneSession**: In the CLI or integration point, create `AriadneSession(portal_name)`.
4. **Pick a Motor**: Pass `C4AIMotorProvider` or `BrowserOSMotorProvider` to `session.run(...)`.
5. **Register Source**: Add the portal name to the CLI choices in `src/automation/main.py` if the portal is user-selectable there.

## 💻 How to Use

```bash
# Verify a portal map by running a dry-run application
python -m src.automation.main apply --source linkedin --job-id 123 --cv my_cv.pdf --dry-run
```

## 🚑 Troubleshooting

- **`State Mismatch`**: The navigator found a different state than expected. Check if the portal DOM changed and update the Map's `presence_predicate`.
- **`TargetNotFound`**: A CSS or Text selector in the Map no longer matches. Inspect the `error_state.png` in the job's artifact folder.
- **`Motor Session Error`**: The selected motor could not observe or execute a step. Check the backend-specific implementation under `src/automation/motors/`.
