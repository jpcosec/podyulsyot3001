# generate_documents_v2: `_google_api_key()` duplicated across node files

**Why deferred:** Harmless at runtime; requires creating a shared utility module which touches all node files — a larger coordinated change.
**Last reviewed:** 2026-03-31

## Problem

`_google_api_key()` is copy-pasted identically into all five node files:

- `src/core/ai/generate_documents_v2/nodes/ingestion.py:28`
- `src/core/ai/generate_documents_v2/nodes/requirement_filter.py:20`
- `src/core/ai/generate_documents_v2/nodes/alignment.py:28`
- `src/core/ai/generate_documents_v2/nodes/blueprint.py:23`
- `src/core/ai/generate_documents_v2/nodes/drafting.py:21`

The function is identical in every file:

```python
def _google_api_key() -> str | None:
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
```

## Why It Matters

If the key resolution logic ever changes (e.g. adding a third env var, reading from a secrets manager), all five copies must be updated in sync. A missed update silently falls back to the demo chain in production.

## Proposed Direction

1. Create `src/core/ai/generate_documents_v2/nodes/_chain_utils.py` with the shared helper.
2. Replace each inline definition with `from src.core.ai.generate_documents_v2.nodes._chain_utils import _google_api_key`.

## Linked TODOs

- `src/core/ai/generate_documents_v2/nodes/ingestion.py:28`
- `src/core/ai/generate_documents_v2/nodes/requirement_filter.py:20`
- `src/core/ai/generate_documents_v2/nodes/alignment.py:28`
- `src/core/ai/generate_documents_v2/nodes/blueprint.py:23`
- `src/core/ai/generate_documents_v2/nodes/drafting.py:21`

All marked: `# TODO(future): extract to shared helper — see future_docs/issues/generate_documents_v2_google_api_key_duplication.md`
