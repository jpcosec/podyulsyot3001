# Issue: Translation failures not logged in pipeline

## Symptom

Pipeline fails with "Translation failed after 2 attempts" but:
1. No translation error appears in `logs/langgraph_api.log`
2. No stack trace or detailed error context is available
3. It's impossible to diagnose why translation is failing

## Expected Behavior

Translation errors should be logged with:
- Full stack trace
- The text being translated
- Provider details (GoogletranslatorAdapter)
- Network/API errors if applicable

## Impact

Cannot debug translation failures in production pipeline runs.

## Proposed Fix

1. Add try/except with detailed logging in `ingestion.py:_recover_empty_job_kg` around the translator call
2. Log the actual exception and the requirement text being translated
3. Ensure translation errors propagate correctly to the CLI output
4. Optionally: add retry metadata to artifacts

## Location

- `src/core/ai/generate_documents_v2/nodes/ingestion.py` - translation call at line 147
- `src/core/tools/translator/base.py` - translator retry logic
