# 🚀 Project Postulator 3000 (Refactor)

This repository is a modernized, modular implementation of the job application and profile management pipeline. It is designed for high concurrency, deterministic rendering, and LLM-native skill matching.

---

## 🏗️ Architecture & Features

The system is split into four primary "Skills" and a central core, each residing in its own `src/` sub-package:

1.  **🕵️‍♂️ Scraper (`src/ai/scraper`):** Anti-bot resilient job crawling with LLM-rescue fallbacks.
2.  **🌐 Translator (`src/tools/translator`):** Modular field and document translation pipeline.
3.  **⚖️ Match Skill (`src/ai/match_skill`):** LangGraph-native human-in-the-loop matching engine.
4.  **📄 Document Generation (`src/ai/generate_documents`):** LangGraph-native CV, letter, and email generation from approved matches.
5.  **📄 Render Pipeline (`src/tools/render`):** Typed, engine-agnostic document rendering (PDF/DOCX) via Pandoc and Jinja2.

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

## 💻 How to Use (Quickstart)

To run a full pipeline from scratch:

1.  **Scrape:** `python -m src.ai.scraper.main --source stepstone --limit 5`
2.  **Translate:** `python -m src.tools.translator.main --source stepstone`
3.  **Match:** `python -m src.ai.match_skill.main --source stepstone --job-id <ID>`
4.  **Generate:** `python -m src.ai.generate_documents.main --source stepstone --job-id <ID>`
5.  **Render:** `python -m src.tools.render.main cv --source stepstone --job-id <ID> --language en`

---

## 🚀 CLI / Usage

Each module provides its own CLI. Refer to the specific module READMEs for detailed arguments:

- [Scraper Documentation](src/ai/scraper/README.md)
- [Translator Documentation](src/tools/translator/README.md)
- [Match Skill Documentation](src/ai/match_skill/README.md)
- [Render Pipeline Documentation](src/tools/render/README.md)

---

## 📝 The Data Contract

The system communicates via structured Pydantic models:
- **`JobPosting`**: Standardized job schema across all scapers and translators.
- **`MatchState`**: LangGraph state for the matching loop.
- **`RenderRequest`**: Unified request model for the document coordinator.

---

## 🛠️ How to Add / Extend

Detailed guides for extending specific components can be found in:
- `docs/standards/docs/documentation_and_planning_guide.md`
- `src/ai/scraper/README.md`
- `src/tools/render/README.md`

---

## 🚑 Troubleshooting

- **Pandoc Errors:** Ensure `pandoc` and `texlive-full` (or equivalent) are installed for PDF rendering.
- **Timeout Errors:** The scraper may hit rate limits; check `logs/` for details and adjust concurrency if needed.
- **LLM Failures:** Ensure your `GOOGLE_API_KEY` is valid and has sufficient quota.
