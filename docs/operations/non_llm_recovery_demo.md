# Non-LLM Recovery Demo (Human-Review Friendly)

## Purpose

This document demonstrates that the recovered non-LLM code paths are working:

- bounded-nondeterministic translation helpers,
- bounded-nondeterministic scraping helpers,
- fail-closed error behavior.

## What was validated

1. Translation no-op when source and target languages are equal.
2. Translation retry then success (first call fails, second succeeds).
3. Translation fail-closed behavior raises `ToolFailureError`.
4. Field-level translation only affects selected fields.
5. Job ID extraction from listing HTML.
6. Listing crawl returns discovered/known/new IDs correctly.
7. Language heuristic flags English vs German markers.
8. Source markdown extraction produces reviewable text snapshot.

## Test status

Command:

```bash
python -m pytest tests/core/tools -q
```

Observed result:

```text
10 passed in 0.03s
```

## Live demo run

Command used:

```bash
python - <<'PY'
from src.core.tools.translation.service import translate_text, translate_fields
from src.core.tools.scraping.service import (
    extract_job_ids_from_listing_html,
    crawl_listing,
    detect_english_status,
    extract_source_text_markdown,
)
from src.core.tools.errors import ToolFailureError

print('=== translation_noop ===')
print(translate_text('Hallo Welt', source_lang='de', target_lang='de'))

print('=== translation_retry_success ===')
calls = {'count':0}
class FlakyTranslator:
    def translate(self, text: str) -> str:
        calls['count'] += 1
        if calls['count'] == 1:
            raise RuntimeError('temporary backend error')
        return 'EN:' + text

def factory(_s: str, _t: str):
    return FlakyTranslator()

print(translate_text('Guten Tag', source_lang='de', target_lang='en', translator_factory=factory, max_attempts=2))
print(f"attempts={calls['count']}")

print('=== translation_fail_closed ===')
class BrokenTranslator:
    def translate(self, text: str) -> str:
        raise RuntimeError('backend down')

def broken_factory(_s: str, _t: str):
    return BrokenTranslator()

try:
    translate_text('Hola', source_lang='es', target_lang='en', translator_factory=broken_factory, max_attempts=2)
except ToolFailureError as exc:
    print(type(exc).__name__)

print('=== translate_fields ===')
payload = {'title':'Hallo', 'description':'Beschreibung', 'count':3}
class PrefixTranslator:
    def translate(self, text: str) -> str:
        return 'EN:' + text

def prefix_factory(_s: str, _t: str):
    return PrefixTranslator()

print(translate_fields(payload, fields=['title'], source_lang='de', target_lang='en', translator_factory=prefix_factory))

print('=== scraping_extract_ids ===')
html = '<a href="/en/job-postings/12345">A</a><a href="/job-postings/67890">B</a>'
print(sorted(extract_job_ids_from_listing_html(html)))

print('=== scraping_crawl_listing ===')
pages = {
    'https://example.com/jobs?page=1': '<a href="/job-postings/100">A</a><a href="/job-postings/101">B</a>',
    'https://example.com/jobs?page=2': '<a href="/job-postings/101">B</a><a href="/job-postings/102">C</a>',
    'https://example.com/jobs?page=3': '',
}
def fake_fetch(url: str) -> str:
    return pages[url]
res = crawl_listing('https://example.com/jobs', known_job_ids={'100'}, fetch_html_fn=fake_fetch)
print(res)

print('=== scraping_language_check ===')
print(detect_english_status('Application deadline and requirements'))
print(detect_english_status('Bewerbungsfrist und Anforderungen'))

print('=== scraping_markdown_extraction_preview ===')
sample_html = '<html><body><h1>Research Assistant</h1><p>Application deadline: 01.04.2026</p></body></html>'
md = extract_source_text_markdown(sample_html, url='https://example.com/jobs/42')
print('\n'.join(md.splitlines()[:8]))
PY
```

Observed output excerpt:

```text
=== translation_noop ===
Hallo Welt
=== translation_retry_success ===
EN:Guten Tag
attempts=2
=== translation_fail_closed ===
ToolFailureError
=== translate_fields ===
{'title': 'EN:Hallo', 'description': 'Beschreibung', 'count': 3}
=== scraping_extract_ids ===
['12345', '67890']
=== scraping_crawl_listing ===
ListingCrawlResult(discovered_ids=['100', '101', '102'], known_ids=['100'], new_ids=['101', '102'])
=== scraping_language_check ===
{'is_english': True, 'marker_hits': 0, 'has_umlaut': False}
{'is_english': False, 'marker_hits': 3, 'has_umlaut': False}
=== scraping_markdown_extraction_preview ===
# Scraped Source Text

- URL: https://example.com/jobs/42
- Retrieved UTC: <timestamp>

## Main Content
Research Assistant
Application deadline: 01.04.2026
```

## Reviewer checklist

- [ ] No-op translation does not call external service path.
- [ ] Retry path performs bounded retry and recovers if backend returns.
- [ ] Fail-closed path raises explicit tool error, not empty success payload.
- [ ] Scraping extractor detects IDs across localized URLs.
- [ ] Crawl result partitions IDs correctly (`discovered`, `known`, `new`).
- [ ] Language heuristic output is explicit and machine-readable.
- [ ] Markdown extraction creates readable source snapshot.
