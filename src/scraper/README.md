# 🕵️ Scraper

Canonical job ingestion layer for source discovery and single-target fetches. The scraper discovers postings per `source`, preserves listing and detail artifacts, and writes the raw Crawl4AI surfaces directly into the schema-v0 job runtime.

## 🏗️ Architecture & Features

The scraper is an ingestion module, not a LangGraph-native skill. Discovery runs happen outside the per-job graph; the graph consumes canonical raw artifacts after ingestion.

- Shared discovery and single-job ingestion base: `src/scraper/smart_adapter.py`
- CLI entry point and provider registry: `src/scraper/main.py`
- Schema contract for extracted jobs: `src/scraper/models.py`
- Portal-specific adapters: `src/scraper/providers/`
- Cached CSS extraction schemas used by the adapters: `scrapping_schemas/README.md`
- Crawl4AI usage standard for this repository: `docs/standards/code/crawl4ai_usage.md`

Canonical ingest artifacts now preserve both the broad raw surfaces and the current best-effort structured payload:

- detail page markdown: `content.md`
- detail page raw HTML: `raw_page.html`
- detail page cleaned HTML: `cleaned_page.html`
- raw structured extraction output: `raw_extracted.json`
- listing-side context: `listing.json`, `listing_content.md`, `listing_page.html`, `listing_page.cleaned.html`
- job-scoped listing context: `listing_case.json`, `listing_case.md`, `listing_case.html`, `listing_case.cleaned.html`
- current validation/result metadata: `scrape_meta.json`

Runtime flow:

- discovery mode: source listing -> job links -> per-job extraction -> canonical ingest under `data/jobs/<source>/<job_id>/nodes/ingest/proposed/`
- on-demand mode: explicit job URL -> single fetch -> canonical ingest under the same runtime path

## ⚙️ Configuration

```env
GOOGLE_API_KEY="your_gemini_api_key_here"
PLAYWRIGHT_BROWSERS_PATH="0"
```

## 🚀 CLI / Usage

Arguments are defined in `build_parser()` in `src/scraper/main.py`.

Use this module for source-level discovery ingestion. Per-job processing happens later through the unified pipeline CLI.

## 📝 Data Contract

The downstream job contract is defined in `src/scraper/models.py` as `JobPosting`.

The cached selector schemas used to satisfy that contract are documented in `scrapping_schemas/README.md`.
This scraper stage also preserves the broader raw listing/detail surfaces so later stages can re-extract fields without depending on what the initial deterministic pass kept. The per-job payload in `state.json` now also carries `listing_case` when listing-side evidence exists for that specific job.
The contract now also includes optional application-routing fields such as `application_method`, `application_url`, `application_email`, and `application_instructions`.

## 🛠️ How to Add / Extend

1. Create a folder under `src/scraper/providers/{new_source}/`.
2. Implement `adapter.py` inheriting from `SmartScraperAdapter` in `src/scraper/smart_adapter.py`.
3. Implement the adapter contract: `source_name`, `supported_params`, `get_search_url`, `extract_job_id`, `extract_links`, and `get_llm_instructions`.
4. Register the adapter in `build_providers()` in `src/scraper/main.py`.
5. Verify the new source writes canonical artifacts under `data/jobs/<source>/<job_id>/nodes/ingest/proposed/`, including listing context plus detail markdown and HTML.
6. Follow the Crawl4AI integration standard in `docs/standards/code/crawl4ai_usage.md`: bootstrap with LLM when needed, then converge to saved deterministic schemas.

## 💻 How to Use

```bash
python -m src.scraper.main --source stepstone --limit 10
python -m src.scraper.main --source tuberlin --job-query "Data Scientist" --limit 5
```

## 🚑 Troubleshooting

- **Structured extraction fails** -> inspect `scrape_meta.json`, `raw_extracted.json`, `content.md`, and `raw_page.html` under the job's ingest folder; if the selector cache is stale, remove the matching file documented in `scrapping_schemas/README.md` and re-run.
- **A field exists in listing cards but not in detail pages** -> inspect `listing_case.json` and `listing_case.md` first; those are the job-scoped listing artifacts that should feed the next stage instead of the full listing page.
- **Rate limits or blocking** -> inspect scraper logs under `logs/`; reduce concurrency or tighten provider filters.
- **Fields still come back empty after rescue** -> refine `get_llm_instructions()` in the provider adapter and validate against `JobPosting` in `src/scraper/models.py`.
