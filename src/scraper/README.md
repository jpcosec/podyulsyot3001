# 🕵️‍♂️ Scraper

Anti-bot resilient job portal crawler with LLM-rescue fallbacks. Extracts structured job postings validated against a shared Pydantic contract.

---

## 🏗️ Architecture & Features

Each portal adapter inherits from a shared base and plugs into a central dispatcher.

- Abstract base adapter (concurrent crawling, LLM schema generation, rescue fallback): `src/scraper/smart_adapter.py`
- CLI entry point and provider registry: `src/scraper/main.py`
- `JobPosting` Pydantic model: `src/scraper/models.py`
- Portal-specific adapters: `src/scraper/providers/`

Flow per run: search URL → extract job links → per-job CSS extraction (LLM-generated selectors, cached) → LLM rescue fallback if selectors fail → validate against `JobPosting`.

---

## ⚙️ Configuration

```env
GOOGLE_API_KEY="your_gemini_api_key_here"
PLAYWRIGHT_BROWSERS_PATH="0"
```

---

## 🚀 CLI / Usage

CLI arguments are defined in `src/scraper/main.py`. Run `python -m src.scraper.main --help` for the full reference.

---

## 📝 Data Contract

The output contract is `JobPosting` in `src/scraper/models.py`.

MANDATORY fields (extraction failure raises a validation error): `job_title`, `company_name`, `location`, `employment_type`, `posted_date`, `responsibilities`, `requirements`.

OPTIONAL fields (may be absent): `salary`, `remote_policy`, `benefits`, `company_description`, `company_industry`, `company_size`, `application_deadline`, `contact_info`.

---

## 🛠️ How to Add / Extend (New Portal)

1. Create a folder under `src/scraper/providers/{new_source}/`.
2. Implement `adapter.py` inheriting from `SmartScraperAdapter` in `src/scraper/smart_adapter.py`.
3. Implement the required abstract methods: `source_name`, `supported_params`, `get_search_url`, `extract_job_id`, `extract_links`, `get_llm_instructions`.
4. Register the adapter in the `PROVIDERS` dict in `src/scraper/main.py`.

---

## 💻 How to Use (Quickstart)

```bash
python -m src.scraper.main --source stepstone --limit 10
python -m src.scraper.main --source tuberlin --job_query "Data Scientist" --limit 5
```

---

## 🚑 Troubleshooting

- **"Structured extraction failed"** — `scrape_meta.json` indicates failure, `extracted_data.json` is empty. Verify `extract_links()` in your adapter, or delete the cached schema in `scrapping_schemas/` to trigger a re-learn.
- **Rate limited** — logs show 429 errors. Check `RateLimiter` settings in your adapter and ensure `simulate_user` is enabled.
- **Missing fields** — LLM rescue works but certain fields are null. Refine `get_llm_instructions()` in your adapter to target those fields explicitly.
