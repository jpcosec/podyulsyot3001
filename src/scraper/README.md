# 🕵️‍♂️ Scraper Adapter Framework

This Framework allows adding new job portals in a deterministic way using **Crawl4AI**. The logic is separated by **Responsibilities**.

## 🏗️ Adapter Architecture

Each adapter (e.g., `StepStoneAdapter`) must inherit from `SmartScraperAdapter` and implement these 4 milestones:

1.  **`supported_params` (Property)**:
    List of CLI flags that the portal knows how to handle (e.g., `['city', 'job_query']`).
    
2.  **`get_search_url(**kwargs)`**:
    Logic to inject the CLI filters (`city`, `job_query`, `categories`) into the portal's search URL.
    
3.  **`extract_links(crawl_result)`**:
    Receives the Crawl4AI result from the search results page and must return a list of absolute URLs of the found job postings.
    
4.  **`get_llm_instructions()`**:
    Specific instructions (prompts) per portal for the "LLM Rescue". (Note: The exact fields and structure to extract are centrally defined via the Pydantic model in `models.py`).

---

## 🚀 How to add a new Source

1.  Create the folder in `src/scraper/providers/{source_name}/`.
2.  Create the `adapter.py` file implementing the class.
3.  Register the instance in the `PROVIDERS` dictionary in `src/scraper/main.py`.

## ⚙️ CLI Usage

```bash
python -m src.scraper.main --source {tuberlin|stepstone} --job_query "Data Scientist" --overwrite
```

**Benefits:**
- **Painless:** The `SmartScraperAdapter` already handles file saving, Pydantic validations, CSS selector caching, dynamic fallback with the LLM, and Crawl4AI configuration (stealth mode and optimizations) for you.
- **Clean:** `main.py` knows nothing about specific selectors or URLs.

---

## 🛠️ Common Issues (Troubleshooting)

**1. "structured extraction failed. Error: [N] validation errors"**
- *Symptom:* The detailed scrape log (`scrape_meta.json`) reports that all Pydantic mandatory fields are failing or are returned as `None` by the LLM. When looking at `content.md`, you see generic texts or 404 messages instead of the job description.
- *Diagnosis:* The scraper might be downloading an invalid route (e.g., a **404 Not Found** page). This usually happens if `extract_links()` aggressively trims the original web URL (for instance, using regex that wrongly discards localization prefixes like `/en/` or strictly needed query filters).
- *Solution:* Verify the logic of `extract_links()` in your adapter. Avoid constructing URLs entirely from extracted numeric IDs unless absolutely necessary. Instead, safely append the exact `href` extracted from the crawled node (e.g., `https://domain.com` + `href`) to preserve the path structure Crawl4AI expects.
