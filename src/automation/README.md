# `src/automation/` — Unified Automation Package

## 🏗️ Architecture & Features

This package provides a unified, semantic-driven browser automation system. It decouples **Path Knowledge** from **Execution Engines**, allowing for high resilience and cross-motor replay.

- **Semantic Layer (`src/automation/ariadne/`)**: Backend-neutral models for States, Tasks, and Paths.
- **Unified Maps (`src/automation/portals/`)**: Single source of truth for portal logic in JSON.
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

## 🛠️ How to Add / Extend

1. **Map the Portal**: Create a JSON map in `src/automation/portals/<portal>/maps/easy_apply.json` using the `AriadnePortalMap` schema.
2. **Implement Adapter**: (Optional) If custom logic is needed, add an adapter in `src/automation/motors/crawl4ai/portals/`.
3. **Register Source**: Add the portal name to the choices in `src/automation/main.py`.

## 💻 How to Use

```bash
# Verify a portal map by running a dry-run application
python -m src.automation.main apply --source linkedin --job-id 123 --cv my_cv.pdf --dry-run
```

## 🚑 Troubleshooting

- **`State Mismatch`**: The navigator found a different state than expected. Check if the portal DOM changed and update the Map's `presence_predicate`.
- **`TargetNotFound`**: A CSS or Text selector in the Map no longer matches. Inspect the `error_state.png` in the job's artifact folder.
- **`Compilation Error`**: The compiler failed to turn the Map into a script. Validate the Map JSON against `src/automation/ariadne/models.py`.
