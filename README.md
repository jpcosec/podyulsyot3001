# Browser Automation Worktree (Unified Automation)

This worktree is focused on the browser automation pipeline, utilizing the **Ariadne Semantic Layer** to provide a backend-neutral source of truth for all automation tasks.

---

## Architecture

All runtime automation code lives under `src/automation/`:

- **`src/automation/ariadne/`**: The semantic layer (Models, Compilers, and Serializers).
- **`src/automation/portals/`**: Portal-specific intent (Unified Maps in JSON).
- **`src/automation/motors/`**: Execution engines (Crawl4AI, BrowserOS CLI).

Crawl4AI is configured to run inside the **BrowserOS** browser instance via CDP (Port 9101) by default, ensuring all automation benefits from BrowserOS's persistent session and anti-detection capabilities.

For a detailed architectural overview, see `docs/automation/ariadne_semantics.md`.

---

## Configuration

The worktree uses a root `.env` file for runtime secrets and environment setup.

### Common Environment Variables
```env
PLAYWRIGHT_BROWSERS_PATH="0"
GOOGLE_API_KEY="your_gemini_key"
GEMINI_API_KEY="your_gemini_key"
BROWSEROS_BASE_URL="http://127.0.0.1:9000"
AUTOMATION_EXTRACTION_FALLBACKS="browseros,llm"
```

### BrowserOS Startup

BrowserOS is an external runtime, not a Python server shipped by this repo.

```bash
# Launch the local BrowserOS runtime
/home/jp/BrowserOS.AppImage --no-sandbox

# Verify the stable local front door
curl http://127.0.0.1:9000/mcp
```

Use `http://127.0.0.1:9000` as the preferred local BrowserOS base URL on this
machine. Backend ports may rotate, but the repo runtime defaults to the stable
front door.

For the full BrowserOS reference index, start with
`docs/reference/external_libs/browseros/readme.txt`.

For setup and session workflow, see `docs/automation/browseros_setup.md`.

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

### Extraction Fallbacks

Scrape extraction now has an explicit fallback order configured through
`AUTOMATION_EXTRACTION_FALLBACKS`.

- `browseros` uses BrowserOS `/chat` as a semantic extraction fallback.
- `browseros` uses BrowserOS MCP as the scrape rescue path.
- `llm` uses the Crawl4AI Gemini rescue path and requires `GOOGLE_API_KEY`.

Examples:

```bash
# Prefer BrowserOS, then allow Gemini rescue
export AUTOMATION_EXTRACTION_FALLBACKS="browseros,llm"

# Use only BrowserOS rescue
export AUTOMATION_EXTRACTION_FALLBACKS="browseros"

# Force only Gemini rescue
export AUTOMATION_EXTRACTION_FALLBACKS="llm"
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
2. Ensure the map contains both `css` and `text` targets for cross-motor compatibility.
3. If a new interaction type is needed, add it to `AriadneIntent` and update the motor compilers (e.g., `src/automation/motors/crawl4ai/compiler/`).
4. Update `src/automation/main.py` to register the new portal choice.

---

## Troubleshooting

- **`RuntimeError: already submitted`**: Delete `apply_meta.json` in the job's artifact directory to force a retry.
- **Compilation Errors**: Check `src/automation/ariadne/compiler/` and the portal map JSON for schema violations.
- **Motor Failures**: Inspect the logs under `logs/` and check motor-specific documentation.
