# 🕵️‍♂️ Scraper Adapter Framework

This framework provides a deterministic, highly concurrent, and anti-bot resilient way to scrape job portals using **Crawl4AI**. It separates the logic by **Responsibilities** and enforces a strict data contract using Pydantic, falling back to an LLM if the layout changes.

---

## 🏗️ Architecture & Features

Each portal adapter (e.g., `StepStoneAdapter`, `TUBerlinAdapter`, `XingAdapter`) inherits from `SmartScraperAdapter`. The framework handles all the heavy lifting:

- **Concurrent Crawling:** Uses `arun_many` with `SemaphoreDispatcher` and `RateLimiter` to scrape multiple jobs at once while avoiding rate limits.
- **Anti-Bot Stealth:** Simulates human behavior (`simulate_user`, `magic`, `override_navigator`).
- **LLM-First Schema Generation:** Automatically generates CSS selectors using an LLM on the first run, caching them for blazing-fast subsequent runs.
- **LLM Rescue Fallback:** If the cached CSS selectors fail to extract valid data, the scraper elegantly falls back to sending the markdown content directly to Google Gemini Flash.
- **Strict Data Contract:** All extracted data must strictly adhere to the `JobPosting` Pydantic model (found in `models.py`), ensuring your downstream pipelines always receive clean, predictable data.

---

## ⚙️ Configuration

The framework relies on a `.env` file located at the root of your project.

### Environment Variables
You must configure the following variable for the LLM schema generation and "LLM Rescue" fallback to work:
```env
GOOGLE_API_KEY="your_gemini_api_key_here"
```

*Note: The framework defaults to `gemini/gemini-2.5-flash` for fast and cheap extraction via LiteLLM.*

---

## 🚀 CLI Usage

You can run the scraper directly from the command line using `main.py`:

```bash
python -m src.scraper.main --source {tuberlin|stepstone|xing} [OPTIONS]
```

### CLI Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--source` | **(Required)** The job portal to crawl (e.g., `tuberlin`, `stepstone`, `xing`). Must be registered in `main.py`. | |
| `--drop_repeated` | Skip jobs that have already been crawled and exist in the `data/` folder. | `True` |
| `--overwrite` | Ignore existing data folders and re-download/re-extract everything. | `False` |
| `--categories` | Job categories to filter by (space separated). | |
| `--city` | City or location to search in. | |
| `--job_query` | Text search for specific professional roles or keywords. | |
| `--max_days` | Maximum days since the job was posted. | |
| `--limit` | Limit the maximum number of job postings to scrape in this run. | |

**Handling Unsupported Parameters:**
Because different portals support different filters (e.g., TU Berlin might not support a `city` filter), `SmartScraperAdapter` defines `supported_params`. If you pass a `--city` to a portal that doesn't support it, the CLI will safely ignore it and emit a warning in the logs.

---

## 📂 Output & Storage

The framework automatically manages where and how data is saved. 

### 1. Extracted Job Data
All successfully discovered jobs are saved under `data/source/{source_name}/{job_id}/`.
Inside each job's folder, you will find:

- `extracted_data.json`: The parsed JSON data perfectly matching the `JobPosting` Pydantic schema. If both CSS and LLM extraction fail, this will be an empty object `{}`.
- `content.md`: The cleaned, optimized Markdown content of the job posting page (useful for downstream LLM analysis or manual review).
- `scrape_meta.json`: A detailed metadata log of the extraction attempt. Contains timestamp, success boolean, the extraction method used (`css`, `llm`, or `none`), and any error messages.
- `raw_page.html`: (Optional) The cleaned HTML of the page, if `save_html=True` is enabled in the code.

### 2. Logs
Every run automatically generates a log file in the `logs/` directory, formatted as:
`logs/scraper_{source}_YYYYMMDD_HHMMSS.log`

This log captures CLI warnings, connection errors, rate limit triggers, and the success/failure of each individual step (CSS vs LLM rescue).

### 3. Schema Cache
Auto-generated CSS selectors are cached in `scrapping_schemas/{source_name}_schema.json`. If you want the LLM to learn the page structure again (e.g., if the portal changed its UI), simply delete this file.

---

## 📝 The Data Contract (`JobPosting` Schema)

All scraped jobs are uniformly mapped to the `JobPosting` class in `models.py`. 

- **Mandatory Fields:** `job_title`, `company_name`, `location`, `employment_type`, `posted_date`, `responsibilities`, `requirements`
- **Optional Fields:** `salary`, `remote_policy`, `benefits`, `company_description`, `company_industry`, `company_size`, `application_deadline`, `reference_number`, `contact_info`

If any of the mandatory fields are missing after the CSS extraction, the framework considers it a failure and automatically triggers the "LLM Rescue" on the markdown content to fill in the gaps.

---

## 🛠️ How to Add a New Job Portal

Adding a new module is extremely structured:

1. Create a new folder: `src/scraper/providers/{new_source}/`.
2. Create an `adapter.py` file inside it.
3. Create a class that inherits from `SmartScraperAdapter`, and implement the required abstract methods:
   - `source_name`: The slug for the folder name.
   - `supported_params`: A list of strings matching the CLI arguments this portal supports.
   - `get_search_url(**kwargs)`: Logic to construct the URL with the provided filters.
   - `extract_job_id(url)`: Extract the unique ID from a job post URL.
   - `extract_links(crawl_result)`: Logic to find absolute URLs of all job posts on the listing page.
   - `get_llm_instructions()`: Short, specific prompts to help the LLM if it needs to rescue data on this portal.
4. Import and register your new class in the `PROVIDERS` dictionary located in `src/scraper/main.py`.

---

## 🚑 Troubleshooting

**1. "structured extraction failed. Error: [N] validation errors"**
- *Symptom:* `scrape_meta.json` says extraction failed. `content.md` shows generic text or a "404 Not Found" message. `extracted_data.json` is empty.
- *Diagnosis:* The scraper downloaded an invalid URL. Usually, `extract_links()` in the adapter built the URL incorrectly (e.g., missing a language prefix like `/en/`).
- *Solution:* Check the `extract_links()` implementation for your portal. Ensure it uses the exact `href` attribute from the crawled page instead of manually trying to reconstruct URLs from IDs.
