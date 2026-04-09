# BrowserOS Agent Schema Generation Fallback Missing

**Explanation:** When CSS extraction schemas fail on real portals, there is no fallback to use a BrowserOS agent to dynamically generate working extraction selectors. The current pipeline has:
1. CSS extraction via `JsonCssExtractionStrategy` with cached schemas
2. LLM rescue via `LLMExtractionStrategy` (requires `GOOGLE_API_KEY` in the current implementation)

But there is no third path: use a BrowserOS agent (port 9200) to navigate to the page, analyze the DOM, and output selectors that can extract the `JobPosting` fields. This is critical because:
- LLM rescue may not be configured in the environment at all
- CSS schemas are portal-specific and become stale when portal HTML changes
- BrowserOS agent can use computer vision and semantic understanding to find fields

**Reference:**
- `src/automation/motors/crawl4ai/scrape_engine.py` — `_extract_payload()`, `get_fast_schema()`
- `src/automation/motors/browseros/agent/provider.py` — Agent motor provider
- `src/automation/ariadne/models.py` — `JobPosting` fields

**What to add:** A BrowserOS-based fallback path that:
1. Is invoked after CSS + LLM rescue both fail
2. Spins up a BrowserOS agent session
3. Sends a prompt like "Extract job title, company, location, employment type, responsibilities, requirements from this page"
4. Parses agent output into CSS selectors or a mini-JSON schema
5. Re-runs extraction with the new schema

**How to do it:**
1. Create `SchemaGenerationFallback` in `src/automation/motors/crawl4ai/schema_fallback.py`
2. Add method `async def generate_schema(crawler, url) -> dict | None`
3. Integrate into `_extract_payload()` after LLM rescue fails
4. Add tests using a mock BrowserOS agent response
5. Validate on real XING/StepStone pages

**Depends on:** `plan_docs/issues/gaps/crawl4ai-live-portal-extraction-normalization.md`, `plan_docs/issues/gaps/browseros-runtime-is-not-reachable-and-endpoints-are-inconsistent.md`
