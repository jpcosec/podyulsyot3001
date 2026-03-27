# Scraping Refactor — Future Options

## Context

Current scraper (`src/core/scraping/`) uses a naive tag-strip (`html_to_text.py`) that
includes navigation, footers, and forms in the extracted text. This was acceptable for
structured job boards (Stepstone, TU Berlin) but produces noisy output for generic pages
like university admission docs.

## Options to Evaluate

### trafilatura
- Python library, extracts main content from any HTML page (articles, docs, job postings)
- Discards nav/sidebar/footer automatically using heuristic + ML signals
- Drop-in replacement for `extract_text()` in `src/core/scraping/extract/html_to_text.py`
- Minimal integration risk — one function swap, no new architecture
- Lightweight dependency (~5MB)
- Likely what crawl4ai uses internally for content extraction

### crawl4ai
- Full crawling framework designed for LLM pipelines
- Produces clean markdown output ready for LLM consumption
- LLM-powered extraction: pass a prompt to extract structured fields
- CSS/XPath declarative extraction strategies
- Async/batch: 100+ URLs in parallel
- Session persistence (login flows, multi-step navigation)
- Built-in caching
- Heavier integration — would require rethinking `service.py` and fetch layer

## Recommendation (pending evaluation)
- `trafilatura` is the low-risk surgical fix for the content extraction gap
- `crawl4ai` only makes sense if we need batch crawling or LLM-driven field extraction
- Evaluate both against UAB admission page and Stepstone to measure content quality delta

## Triggered by
- Attempt to scrape UAB master's admission page:
  `https://www.uab.cat/web/estudiar/official-master-s-degrees/admission/documentation/-1345808913953.html?param1=1345875379850`
- HTTP fetch succeeded (12k chars) but output was noisy (nav, forms, menus mixed in)
