# 🕵️‍♂️ Scraper Adapter Framework

This framework provides a deterministic, highly concurrent, and anti-bot resilient way to scrape job portals using **Crawl4AI**. It separates logic by **Responsibilities** and enforces a strict data contract using Pydantic, with automatic LLM-rescue fallbacks.

---

## 🏗️ Architecture & Features

Each portal adapter (e.g., `StepStone`, `TUBerlin`, `Xing`) inherits from `SmartScraperAdapter`:

- **Concurrent Crawling**: Uses `arun_many` with `SemaphoreDispatcher` and `RateLimiter` to scrape multiple jobs while avoiding rate limits.
- **Anti-Bot Stealth**: Simulates human behavior (`simulate_user`, `magic`, `override_navigator`).
- **LLM-First Schema Generation**: Automatically generates CSS selectors using an LLM on the first run, then caches them for performance.
- **LLM Rescue Fallback**: If CSS selectors fail, the engine falls back to direct Markdown extraction via Google Gemini.
- **Strict Data Contract**: All extracted data is validated against the `JobPosting` Pydantic model.

---

## ⚙️ Configuration

The framework relies on the root `.env` file:
```env
# Required for LLM schema generation and rescue fallback
GOOGLE_API_KEY="your_gemini_api_key_here"

# Optional: Path to Playwright browsers
PLAYWRIGHT_BROWSERS_PATH="0"
```

---

## 💻 How to Use (Quickstart)

Scrape a portal for the latest jobs:
```bash
# Full crawl of StepStone
python -m src.scraper.main --source stepstone --limit 10

# Targeted crawl for TU Berlin
python -m src.scraper.main --source tuberlin --job_query "Data Scientist" --limit 5
```

---

## 🚀 CLI / Usage

| Argument | Description | Default |
|---|---|---|
| `--source` | **(Required)** Job portal to crawl (e.g., `tuberlin`, `stepstone`, `xing`). | |
| `--limit` | Maximum number of job postings to scrape in this run. | |
| `--job_query` | Text search for specific professional roles or keywords. | |
| `--categories` | Job categories to filter by (space separated). | |
| `--city` | City or location to search in. | |
| `--drop_repeated` | Skip jobs that have already been crawled. | `True` |
| `--overwrite` | Force re-download and re-extraction of existing data. | `False` |

---

## 📝 The Data Contract

All scraped jobs are uniformly mapped to the **`JobPosting`** model in `models.py`:
- **Mandatory Fields**: `job_title`, `company_name`, `location`, `employment_type`, `posted_date`, `responsibilities`, `requirements`
- **Optional Fields**: `salary`, `remote_policy`, `benefits`, `company_description`, `company_industry`, `company_size`, `application_deadline`, `contact_info`

---

## 🛠️ How to Add / Extend (New Portal)

1.  Create a folder under `src/scraper/providers/{new_source}/`.
2.  Implement `adapter.py` by inheriting from `SmartScraperAdapter`.
3.  Define the required abstract methods: `source_name`, `supported_params`, `get_search_url`, `extract_job_id`, `extract_links`, and `get_llm_instructions`.
4.  Register your new adapter in the `PROVIDERS` dictionary in `src/scraper/main.py`.

---

## 🚑 Troubleshooting

- **"Structured extraction failed"**:
    - *Symptom:* `scrape_meta.json` indicates failure and `extracted_data.json` is empty.
    - *Diagnosis:* The URL was invalid or the layout changed.
    - *Solution:* Verify `extract_links()` in your adapter or delete the cached schema in `scrapping_schemas/` to trigger a re-learn.
- **Rate Limited**:
    - *Symptom:* Scraper stops or logs 429 errors.
    - *Solution:* Check your `RateLimiter` settings and ensure `simulate_user` is enabled.
- **Missing Fields**:
    - *Symptom:* LLM rescue works but certain fields are still null.
    - *Solution:* Refine `get_llm_instructions()` in your adapter to focus on those specific missing fields.
