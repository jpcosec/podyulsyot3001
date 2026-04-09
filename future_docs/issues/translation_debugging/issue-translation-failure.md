# Issue: Translation failing after 2 attempts in ingestion recovery

## Symptom

Pipeline fails at `ingestion.py` with "Translation failed after 2 attempts" during the `_recover_empty_job_kg` recovery step.

The error occurs when:
1. The LLM fails to extract requirements from job listing
2. The fallback tries to translate the raw requirements from the job bundle
3. The `GoogleTranslatorAdapter.translate_text()` fails after 2 retry attempts

## Context

This is a separate issue from the logging problem - we need to understand WHY translation is failing:
- Is it a network issue?
- Is the API key invalid?
- Is the text malformed?
- Is there a rate limit?

## Impact

Pipeline cannot process jobs when LLM extraction fails, even though the raw data exists.

## Proposed Fix

1. First, fix the logging issue (see `translation_logging.md`) to get error details
2. Once we have proper logging, diagnose the actual cause:
   - Check API key validity
   - Check network connectivity
   - Check if the text being translated is valid
3. Consider adding a third fallback (use raw text in original language) if translation continues to fail

## Location

- `src/core/ai/generate_documents_v2/nodes/ingestion.py` - line 147
- `src/core/tools/translator/base.py` - translator retry logic
- `src/core/tools/translator/providers/google/adapter.py` - Google translator adapter
