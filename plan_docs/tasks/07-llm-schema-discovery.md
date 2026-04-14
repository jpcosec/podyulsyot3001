# Task 07: LLM-based schema discovery for unknown portals

## Explanation
`PortalExtractor` currently returns `[]` when no schema is registered for a domain.
For fully autonomous navigation, the system should be able to extract structured data
from any page even without a pre-defined schema — by asking the LLM to propose selectors
from the live HTML, then caching the result so future visits are deterministic.

## What to change

### 1. `PortalExtractor` — LLM fallback path
When `portal_dictionary.get_strategy(schema_id)` returns `None`:
- Ask LLM: "Given this HTML, propose a CSS selector to extract {schema_id} items"
- Parse response into a `JsonCssExtractionStrategy`-compatible schema dict
- Run extraction immediately
- Write schema back to `PortalDictionary` via `portal_dictionary.register(schema_id, strategy)`

### 2. `PortalDictionary` — `register()` method + persistence
- Add `register(schema_id: str, schema_dict: dict)` that builds and caches a strategy
- Persist new schemas to `data/portals/{portal}/schemas/{schema_id}.json`
- `load()` reads existing schema files from that directory on startup

### 3. LLM prompt for selector discovery
- Send HTML excerpt (first 4000 chars) + schema_id as the "concept to extract"
- Expect JSON: `{"baseSelector": "...", "fields": [{"name": "...", "selector": "...", "type": "text|attribute"}]}`
- Validate response parses; on failure log a warning and return `[]`

## Depends on
- Task 06 (domain in state, PortalRegistry exists)
- `GeminiClient` already available in builder
- `PortalExtractor` needs `LLMClient` injected (add optional arg)

## Tests to add
- `tests/ariadne/extraction/test_portal_dictionary.py` — `register()` persists and reloads
- `tests/adapters/test_portal_extractor.py` — LLM fallback called when no schema; schema cached on success
