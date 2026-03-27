
# How to add a new Source to the Scraper

To add a new job portal (e.g., StepStone, XING) to the deterministic refactor:

### 1. Create a Provider Directory
Create a new folder under `src/scraper/providers/{source_name}/`.

### 2. Implement Search Logic (`search.py`)
Define how to build the filtered search URL. This module should handle keywords, location, and categorization logic for the specific provider.

### 3. Define Extraction Schemas (`detail.py`)
Map the CSS selectors/JSON schemas for `crawl4ai`.
- **Labels:** Use `:contains` or `-soup-contains` for anchor text.
- **Values:** Map to the core `JobPosting` data model (title, email, deadline, etc.).

### 4. Implement Pagination Crawler (`crawler.py`)
Logic to iterate through "Next page" links or calculate page parameters until no more results match the criteria.

### 5. Register in `main.py`
Add the new provider to the `ProviderManager` dictionary so the CLI can resolve `-source {name}`.

---
**Core Contract:**
Every source MUST output:
1. `raw_content.md` (FIT Markdown from Crawl4AI).
2. `extracted_data.json` (Structured JSON according to schema).
3. Saved under `data/source/{job_id}/`.
