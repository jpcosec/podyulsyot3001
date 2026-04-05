# Crawl4AI Motor Contracts

Date: 2026-04-05
Status: design-only

## Purpose

Contracts between the Ariadne Crawl4AI translator and the Crawl4AI executor.
These define the translator's output — the motor-specific plan that the
executor consumes.

## Translator output

### CrawlPlan

The full execution plan for one AriadnePath, compiled for Crawl4AI.

```python
class CrawlPlan(BaseModel):
    path_id: str
    phases: list[CrawlPhase]
    browser_config: CrawlBrowserConfig
```

### CrawlPhase

One `arun()` call. A path compiles into multiple phases (navigate, fill, submit).

```python
class CrawlPhase(BaseModel):
    name: str                            # "navigate", "fill", "submit", etc.
    url: str | None = None               # only for navigation phases
    c4a_script: str | None = None        # compiled C4A-Script for this phase
    wait_for: str | None = None          # CSS or text wait condition
    js_only: bool = False                # in-session call (no navigation)
    screenshot: bool = False             # capture screenshot after phase
    session_id: str | None = None        # session continuity key
    hooks: list[CrawlHook] = []          # Playwright hooks (file uploads, DOM validation)
```

### CrawlHook

A Playwright hook that cannot be expressed in C4A-Script.

```python
class CrawlHook(BaseModel):
    event: Literal["before_retrieve_html"]
    hook_type: Literal["file_upload", "dom_validation"]
    config: dict                         # hook-specific config
```

**File upload hook config:**
```python
{
    "selector": "input[type=file]",      # CSS selector for the file input
    "file_path": "{{cv_path}}",          # template, resolved at execution time
}
```

**DOM validation hook config:**
```python
{
    "selectors": {"field_name": "css_selector", ...},
    "mandatory": ["apply_button", "cv_upload", "submit_button"],
}
```

### CrawlBrowserConfig

Browser settings for the Crawl4AI session.

```python
class CrawlBrowserConfig(BaseModel):
    headless: bool = True
    text_mode: bool = False              # True for scraping, False for apply
    user_data_dir: str | None = None     # persistent session profile
    use_persistent_context: bool = False
```

## Scraping-specific contracts

The Crawl4AI motor also handles scraping (discovery + extraction), which does
not go through Ariadne paths. These contracts are motor-internal.

### CrawlExtractionConfig

Configuration for a scraping run.

```python
class CrawlExtractionConfig(BaseModel):
    source: str
    search_url: str
    schema_path: Path | None = None      # cached CSS extraction schema
    llm_config: dict | None = None       # LLM rescue configuration
    limit: int | None = None
    drop_repeated: bool = True
```

### CrawlExtractionResult

Result of extracting one job posting.

```python
class CrawlExtractionResult(BaseModel):
    job_id: str
    url: str
    extraction_method: Literal["css", "llm", "none"]
    valid_data: dict | None = None       # validated JobPosting payload
    merged_payload: dict | None = None   # raw merged payload (listing + detail)
    extraction_error: str | None = None
    scraped_at: str
```

## Current equivalents

| Contract | Current code | Location |
|---|---|---|
| `CrawlPlan` | (implicit in `ApplyAdapter.run()` flow) | `src/apply/smart_adapter.py` |
| `CrawlPhase` | (implicit — each `arun()` call) | same |
| `CrawlHook` | `_build_file_upload_hook()` return | same |
| `CrawlBrowserConfig` | `BrowserConfig(...)` inline construction | same |
| `CrawlExtractionConfig` | (implicit in `SmartScraperAdapter.run()` args) | `src/scraper/smart_adapter.py` |
| `CrawlExtractionResult` | (implicit — `_extract_payload()` return tuple) | same |

The current code has no explicit contract types — configuration and results are
passed as raw dicts, tuples, and inline `CrawlerRunConfig` construction. These
contracts make the implicit boundaries explicit.
