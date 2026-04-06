# Browser Automation Worktree (Unified Automation)

This worktree is focused on the browser automation pipeline, utilizing the **Ariadne Semantic Layer** to provide a backend-neutral source of truth for all automation tasks.

---

## Architecture

All runtime automation code lives under `src/automation/`:

- **`src/automation/ariadne/`**: The semantic layer (Models, Compilers, and Serializers).
- **`src/automation/portals/`**: Portal-specific intent (Unified Maps in JSON).
- **`src/automation/motors/`**: Execution engines (Crawl4AI, BrowserOS CLI).

For a detailed architectural overview, see `docs/automation/ariadne_semantics.md`.

---

## Configuration

The worktree uses a root `.env` file for runtime secrets and environment setup.

### Common Environment Variables
```env
PLAYWRIGHT_BROWSERS_PATH="0"
GOOGLE_API_KEY="your_gemini_key"
GEMINI_API_KEY="your_gemini_key"
```

---

## CLI / Usage

The unified automation CLI is the primary entry point:

```bash
# Scrape jobs from a source
python -m src.automation.main scrape --source stepstone --limit 5

# Apply to a job (Crawl4AI backend - Default)
python -m src.automation.main apply --source xing --job-id 12345 --cv path/to/cv.pdf --dry-run

# Apply via BrowserOS backend
python -m src.automation.main apply --backend browseros --source linkedin --job-id 99 --cv path/to/cv.pdf
```

---

## Data Contract

- **`AriadnePortalMap`**: The unified semantic map for each portal.
- **`JobPosting`**: Standardized extraction output from scraping.
- **`ApplyMeta`**: Status artifact for application attempts.
- Artifacts are stored under `data/jobs/<source>/<job_id>/nodes/`.

---

## How to Add / Extend

1. Define a new portal flow map under `src/automation/portals/<portal>/maps/<flow>.json`.
2. Add a motor-specific translator if needed (e.g., in `src/automation/motors/crawl4ai/portals/`).
3. Update `src/automation/main.py` to register the new portal/adapter.

---

## Troubleshooting

- **`RuntimeError: already submitted`**: Delete `apply_meta.json` in the job's artifact directory to force a retry.
- **Compilation Errors**: Check `src/automation/ariadne/compiler/` and the portal map JSON for schema violations.
- **Motor Failures**: Inspect the logs under `logs/` and check motor-specific documentation.
