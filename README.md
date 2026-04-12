# Browser Automation Worktree (Unified Automation)

This worktree is focused on the browser automation pipeline, utilizing the **Ariadne Semantic Layer** to provide a backend-neutral source of truth for all automation tasks.

---

## README Indexation System

This repo uses README files as an **indexation system** to avoid context overload and drift:

1. **`README.md` (root)** → points to module READMEs
2. **Module READMEs** (`src/automation/README.md`, `docs/README.md`) → point to definitive source files
3. **Source files** (`src/automation/*.py`, `docs/ariadne/*.md`) → the actual source of truth

READMEs are NOT comprehensive documentation. They are navigation hints. Do not duplicate content from source files into READMEs.

---

## 🏗️ Architecture & Features

All runtime automation code lives under `src/automation/`:

- **`src/automation/ariadne/`**: The semantic layer (Models, Compilers, and Serializers).
- **`src/automation/portals/`**: Portal-specific intent (Unified Maps in JSON).
- **`src/automation/motors/`**: Execution engines (Crawl4AI, BrowserOS CLI).

Crawl4AI is configured to run inside the **BrowserOS** browser instance via CDP (Port 9101) by default, ensuring all automation benefits from BrowserOS's persistent session and anti-detection capabilities.

For a detailed architectural overview, see `docs/ariadne/architecture_and_graph.md` and `src/automation/README.md`.

---

## ⚙️ Configuration

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
# Configure and launch the local BrowserOS runtime
export BROWSEROS_APPIMAGE_PATH="/path/to/BrowserOS.AppImage"
"$BROWSEROS_APPIMAGE_PATH" --no-sandbox

# Verify the stable local front door
curl http://127.0.0.1:9000/mcp
```

Use `http://127.0.0.1:9000` as the preferred local BrowserOS base URL on this
machine. Backend ports may rotate, but the repo runtime defaults to the stable
front door.

For runtime behavior and package boundaries, start with `src/automation/README.md`.

---

## 🚀 CLI / Usage

The unified automation CLI is the primary entry point. The authoritative command surface lives in `src/automation/main.py`.

```bash
# Scrape jobs from a source
python -m src.automation.main scrape --source stepstone --limit 5

# Apply to a job (Crawl4AI backend - Default)
python -m src.automation.main apply --source xing --job-id 12345 --cv path/to/cv.pdf --dry-run

# Apply via BrowserOS backend
python -m src.automation.main apply --backend browseros --source linkedin --job-id 99 --cv path/to/cv.pdf
```

---

## 📝 Data Contract

- The canonical runtime contracts live in `src/automation/ariadne/models.py`, `src/automation/ariadne/contracts/base.py`, and `src/automation/contracts.py`.
- Runtime artifacts are stored under `data/jobs/<source>/<job_id>/` and `data/ariadne/`.

---

## How to Add / Extend

1. Define a new portal flow map under `src/automation/portals/<portal>/maps/<flow>.json`.
2. Ensure the map contains both `css` and `text` targets for cross-motor compatibility.
3. If a new interaction type is needed, add it to `AriadneIntent` and update the translator/executor path used by the active motor.
4. Update `src/automation/main.py` to register the new portal choice.

---

## Troubleshooting

- **`RuntimeError: already submitted`**: Delete `apply_meta.json` in the job's artifact directory to force a retry.
- **Map Orchestration Errors**: Check `src/automation/ariadne/graph/orchestrator.py` and the portal map JSON for schema violations.
- **Motor Failures**: Inspect `data/jobs/` and `data/ariadne/` runtime artifacts.
