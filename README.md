# 🚀 Project Postulator 3000 (Refactor)

This repository is a modernized, modular implementation of the job application and profile management pipeline. It is designed for high concurrency, deterministic rendering, and LLM-native document generation.

---

## 🏗️ Architecture & Features

The system is split into primary skills and a central core, each residing in its own `src/` sub-package:

1.  **🌐 Translator (`src/core/tools/translator`):** Modular field and document translation pipeline.
2.  **📄 Document Generation (`src/core/ai/generate_documents_v2`):** LangGraph-native CV, letter, and email generation from canonical job and profile artifacts.
3.  **📄 Render Pipeline (`src/core/tools/render`):** Typed, engine-agnostic document rendering (PDF/DOCX) via Pandoc and Jinja2.
4.  **🖥️ Review UI (`src/review_ui`):** Textual review surfaces and operator workflow tooling.

---

## ⚙️ Configuration

The project uses a `.env` file at the root for secrets and configuration.

### Required Environment Variables
```env
# AI & LLM
GOOGLE_API_KEY="your_gemini_key"
GEMINI_API_KEY="your_gemini_key"

# Logging
LOG_DIR=logs
```

---

## 🚀 CLI / Usage

The operator workflow is API-first. The unified CLI in `src/cli/main.py` is the entry point for batch execution and review. The recommended control-plane flow is:

1. start or reuse the LangGraph API
2. launch batch pipeline runs for selected jobs
3. review paused jobs from the TUI explorer

Primary entry points:

- `python -m src.cli.main api start` — start or reuse the LangGraph API control plane
- `python -m src.cli.main run-batch --sources xing stepstone --limit 5 --profile-evidence path/to/profile.json` — launch pipeline runs for jobs
- `python -m src.cli.main review` — open the explorer TUI against the LangGraph API
- `python -m src.cli.main review --source xing --job-id 12345` — open direct review mode for one thread

---

## 📝 Data Contract

The system communicates via structured Pydantic models and persisted job artifacts:

- `JobKG` / `JobDelta` — staged job-understanding contracts for document generation; see `src/core/ai/generate_documents_v2/contracts/`
- `RenderRequest` — unified request model for rendering; see `src/core/tools/render/request.py`
- pipeline state and job artifacts — persisted under `data/jobs/<source>/<job_id>/...`; see `docs/runtime/data_management.md`

The top-level control plane keeps only refs and routing signals in LangGraph state; heavy payloads stay on disk.

---

## 🛠️ How to Add / Extend

1. Extend the operator CLI in `src/cli/main.py` when adding a new control-plane action.
2. Put stateful LangGraph interactions behind `src/core/api_client.py`; do not add local graph fallbacks in CLI or TUI layers.
3. For new runtime artifacts, register the path through `src/core/data_manager.py` and update `docs/runtime/data_management.md`.
4. Update the relevant module README and `changelog.md` whenever the operator workflow changes.

---

## 💻 How to Use

```bash
# 1. Start or reuse the API control plane
python -m src.cli.main api start

# 2. Launch pipeline runs for jobs
python -m src.cli.main run-batch --sources xing stepstone --limit 2

# 3. Open the review explorer
python -m src.cli.main review
```

Module-specific documentation:

- [Translator Documentation](src/core/tools/translator/README.md)
- [Document Generation Documentation](src/core/ai/generate_documents_v2/README.md)
- [Review UI Documentation](src/review_ui/README.md)
- [Render Pipeline Documentation](src/core/tools/render/README.md)

---

## 🚑 Troubleshooting

- **`postulator review` opens but shows no jobs** → Ensure you started runs through the API-backed CLI first, for example `python -m src.cli.main run-batch --limit 5`.
- **`run-batch` finds no jobs** → Pass explicit jobs through `--job` / `--stdin`.
- **Pandoc errors during render** → Ensure `pandoc` and `texlive-full` (or equivalent) are installed for PDF rendering.
- **LLM failures** → Ensure `GOOGLE_API_KEY` or `GEMINI_API_KEY` is valid and has sufficient quota.
