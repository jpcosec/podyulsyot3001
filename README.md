# 🚀 Project Postulator 3000 (Refactor)

This repository is a modernized, modular implementation of the job application and profile management pipeline. It is designed for high concurrency, deterministic rendering, and LLM-native skill matching.

---

## 🏗️ Architecture & Features

The system is split into four primary "Skills" and a central core, each residing in its own `src/` sub-package:

1.  **🕵️‍♂️ Scraper (`src/scraper`):** Canonical job ingestion via source discovery and single-target fetches.
2.  **🌐 Translator (`src/core/tools/translator`):** Modular field and document translation pipeline.
3.  **📄 Document Generation (`src/core/ai/generate_documents_v2`):** LangGraph-native CV, letter, and email generation from canonical job and profile artifacts.
4.  **📄 Render Pipeline (`src/core/tools/render`):** Typed, engine-agnostic document rendering (PDF/DOCX) via Pandoc and Jinja2.
5.  **🖥️ Review UI (`src/review_ui`):** Textual review surfaces and operator workflow tooling.

---

## ⚙️ Configuration

The project uses a `.env` file at the root for secrets and configuration.

### Required Environment Variables
```env
# AI & LLM
GOOGLE_API_KEY="your_gemini_key"
GEMINI_API_KEY="your_gemini_key"

# Browser (for Scraper)
PLAYWRIGHT_BROWSERS_PATH="0" # or your local path
```

---

## 🚀 CLI / Usage

The operator workflow is API-first. The unified CLI in `src/cli/main.py` is the entry point for search, batch execution, and review. Module-specific CLIs still exist for focused work, but the recommended control-plane flow is:

1. start or reuse the LangGraph API
2. ingest/search jobs across one or more sources
3. launch batch pipeline runs for selected ingested jobs
4. review paused jobs from the TUI explorer

Primary entry points:

- `python -m src.cli.main api start` — start or reuse the LangGraph API control plane
- `python -m src.cli.main search --sources xing stepstone --job-query "data scientist" --city berlin` — ingest jobs across multiple sources
- `python -m src.cli.main run-batch --sources xing stepstone --limit 5 --profile-evidence path/to/profile.json` — launch pipeline runs for recent ingested jobs
- `python -m src.cli.main review` — open the explorer TUI against the LangGraph API
- `python -m src.cli.main review --source xing --job-id 12345` — open direct review mode for one thread

---

## 📝 Data Contract

The system communicates via structured Pydantic models and persisted job artifacts:

- `JobPosting` — standardized job schema across scraper and translator flows; see `src/scraper/models.py`
- `RenderRequest` — unified request model for rendering; see `src/core/tools/render/request.py`
- pipeline state and job artifacts — persisted under `data/jobs/<source>/<job_id>/...`; see `docs/runtime/data_management.md`

The top-level control plane keeps only refs and routing signals in LangGraph state; heavy payloads stay on disk.

---

## 🛠️ How to Add / Extend

1. Extend the operator CLI in `src/cli/main.py` when adding a new control-plane action.
2. Put stateful LangGraph interactions behind `src/core/api_client.py`; do not add local graph fallbacks in CLI or TUI layers.
3. For new ingestion sources, follow `src/scraper/README.md` plus `docs/standards/code/crawl4ai_usage.md`.
4. For new runtime artifacts, register the path through `src/core/data_manager.py` and update `docs/runtime/data_management.md`.
5. Update the relevant module README and `changelog.md` whenever the operator workflow changes.

---

## 💻 How to Use

```bash
# 1. Start or reuse the API control plane
python -m src.cli.main api start

# 2. Search across multiple sources
python -m src.cli.main search --sources xing stepstone --job-query "data scientist" --city berlin --limit 3

# 3. Launch pipeline runs for recent ingested jobs
python -m src.cli.main run-batch --sources xing stepstone --limit 2

# 4. Open the review explorer
python -m src.cli.main review
```

Module-specific documentation:

- [Scraper Documentation](src/scraper/README.md)
- [Translator Documentation](src/core/tools/translator/README.md)
- [Document Generation Documentation](src/core/ai/generate_documents_v2/README.md)
- [Review UI Documentation](src/review_ui/README.md)
- [Render Pipeline Documentation](src/core/tools/render/README.md)

---

## 🚑 Troubleshooting

- **`postulator review` opens but shows no jobs** -> Ensure you started runs through the API-backed CLI first, for example `python -m src.cli.main run-batch --sources xing --limit 5`.
- **`run-batch` finds no jobs** -> Search/ingest first with `python -m src.cli.main search ...`, or pass explicit jobs through `--job` / `--stdin`.
- **Pandoc errors during render** -> Ensure `pandoc` and `texlive-full` (or equivalent) are installed for PDF rendering.
- **Timeout or rate-limit errors during search** -> Check `logs/` and reduce scrape breadth with `--limit` or narrower filters.
- **LLM failures** -> Ensure `GOOGLE_API_KEY` or `GEMINI_API_KEY` is valid and has sufficient quota.
