# Stage 2 — Cross-Portal Discovery & Auto-Application

**Why deferred:** Depends on Stage 1 producing reliable `application_url`, `application_method`, and generated CV/letter artifacts. Both sub-problems require significant integration work and live-portal testing.
**Last reviewed:** 2026-03-29

---

## Overview

Stage 1 scrapes, translates, matches, and generates application documents. Stage 2 closes two open loops:

1. **Cross-portal discovery** — a listing on StepStone or XING often links to the company's own ATS portal or careers page, where more open positions exist. We are currently not following those links.
2. **Auto-application** — once documents are generated, submitting the application still requires manual work. This stage aims to automate form submission for the two web-based paths (inline portal forms and company ATS forms). Email-based application is explicitly deferred to a later stage.

---

## Sub-problem 1: Cross-Portal Discovery

### Problem

The `application_url` field captured during scrape-time points to a company ATS (Workday, Greenhouse, Lever, SAP SuccessFactors, Taleo, etc.) or a company career sub-domain. We are not currently following these links to discover additional open positions at that company.

### Crawl4AI capabilities available

- `AdaptiveCrawler` with `digest()` — intelligently follows links on a careers page using information foraging: evaluates coverage, consistency, and saturation to stop automatically when all relevant job URLs have been found. Cheaper and faster than blind BFS for this use case.
- `DomainFilter(allowed_domains=[company_domain])` — scopes discovery to the company's ATS domain
- `URLPatternFilter` — filters to job-like URL patterns (`*/jobs/*`, `*/careers/*`, `*/stellenangebote/*`)
- `AsyncUrlSeeder(source="sitemap")` — if the company careers page exposes a sitemap, bulk-discovers all open positions instantly without crawling

### Proposed architecture

```
JobPosting.application_url
    ↓
CompanyPortalAdapter.discover(url)
    ↓  AdaptiveCrawler.digest(
    ↓      start_url=application_url,
    ↓      query="open job position requirements responsibilities"
    ↓  )  + URLPatternFilter(patterns=["*/jobs/*", "*/careers/*", "*/apply/*"])
    ↓
[list of job page URLs on company portal]
    ↓
SmartScraperAdapter (or new CompanyPortalAdapter)
    ↓
canonical ingest under data/jobs/<company_domain>/<job_id>/
```

`AdaptiveCrawler` stops automatically when saturation is high (no new job-like pages are being found), avoiding over-crawling. `AsyncUrlSeeder` is the preferred path when the target domain exposes a sitemap — faster and zero token cost.

A new `source` value (e.g. `"company:siemens.com"`) would distinguish company-portal-discovered jobs from aggregator-discovered ones.

### ATS detection and anti-bot strategy

Most major ATS platforms have recognizable URL patterns. A small lookup table maps domain patterns to known ATS types, which informs both the extraction schema and the bot-evasion config to use:

| ATS | URL pattern | Rendering | Bot protection |
|-----|-------------|-----------|---------------|
| Workday | `*.wd*.myworkdayjobs.com` | Heavy SPA | Cloudflare |
| Greenhouse | `boards.greenhouse.io/*` | Mostly static | Low |
| Lever | `jobs.lever.co/*` | Clean JSON-LD | Low |
| SAP SuccessFactors | `*.successfactors.com/*` | Complex SPA | Medium |
| Taleo | `*.taleo.net/*` | Legacy iframes | Low |

For portals with active bot protection (Workday, SAP), apply stealth mode:

```python
from crawl4ai import UndetectedAdapter, BrowserConfig

browser_config = BrowserConfig(
    enable_stealth=True,
    headless=False,  # required to defeat some DataDome checks
)
```

`enable_stealth=True` patches browser fingerprints. `headless=False` is sometimes required for Cloudflare/DataDome challenges that inspect rendering behavior. Use only when the portal is known to block headless crawlers — it is slower and more resource-intensive.

---

## Sub-problem 2: Auto-Application

### Overview

| Path | Crawl4AI feasibility | Deferred? |
|------|---------------------|-----------|
| **Email** (`application_method: email`) | N/A (SMTP, not browser) | Yes — deferred |
| **Inline portal form** (Easy Apply on XING/StepStone) | High | No |
| **Company portal form** (external ATS, no account) | Medium | No |
| **Company portal form** (external ATS, requires account) | Medium | Account creation = HITL once; session persisted via browser profile |

### Form interaction — two complementary tools

**Playwright hooks** (via `on_page_context_created`) — best for file uploads and multi-step flows:

```python
async def on_page_context_created(page: Page, context: BrowserContext, **kwargs):
    await page.fill("input[name='firstname']", profile.first_name)
    await page.fill("input[name='email']", profile.email)
    await page.set_input_files("input[type='file'][accept='.pdf']", str(cv_path))
    await page.select_option("select[name='experience']", "5+ years")
    await page.click("button[type='submit']")
    await page.wait_for_selector(".application-confirmation", timeout=15000)
```

**`js_code` in `CrawlerRunConfig`** — preferred for React/Vue SPAs where Playwright events sometimes fail to trigger framework state updates. The LLM can generate the JS snippet as part of form analysis:

```python
config = CrawlerRunConfig(
    js_code=llm_generated_js,   # e.g. React-friendly value setters + submit trigger
    wait_for="css:.success-message"
)
```

Use hooks for file uploads (no JS equivalent) and `js_code` when the SPA does not respond to synthetic Playwright events.

### Form analyzer (the missing piece)

The key non-trivial component is mapping candidate profile data to the specific fields of an unknown form. Proposed approach:

1. **Crawl the apply page** with LLM extraction to produce a `FormFieldMap`:
   ```python
   class FormField(BaseModel):
       selector: str       # CSS selector to the input
       label: str          # Human-visible label text
       field_type: str     # text, select, file, textarea, checkbox
       semantic: str       # LLM-inferred: "first_name", "cv_upload", "cover_letter", etc.
       required: bool
   ```

2. **Profile mapper** resolves `semantic → profile value`:
   - `"first_name"` → `profile.first_name`
   - `"cv_upload"` → `artifacts/render/cv.pdf` or `.docx` depending on what the portal accepts
   - `"cover_letter"` → `artifacts/render/letter.pdf`
   - `"linkedin_url"` → `profile.linkedin`
   - Unknown semantics → flag for human review before submission

3. **Form filler** executes fills via Playwright hook or `js_code` depending on the detected SPA type.

4. **Confirmation verifier** waits for a success indicator and persists the submission artifact.

### Account-required portals

The problem decomposes into two independent concerns:

**1. Account creation — HITL step**

Account creation (email verification, captchas, profile setup) is a one-time-per-domain operation that is not worth automating. The pipeline detects that a domain requires an account, pauses, and surfaces a `create_account.md` review file with the registration URL and the profile data to use. The human creates the account manually and resumes. This only happens once per ATS domain.

**2. Session persistence — browser profile**

Once an account exists, there is no need to store or inject credentials. Crawl4AI supports persistent browser profiles natively:

```python
browser_config = BrowserConfig(
    user_data_dir="data/profiles/workday_profile",
    use_persistent_context=True,
)
```

The browser profile stores cookies and session tokens exactly as a real browser would. After the human completes the HITL login step with this profile directory open, every subsequent run reuses the live session. No credentials touch the code, the artifacts, or the repo.

| Scenario | Feasibility |
|----------|-------------|
| Account creation | HITL (one-time per domain) |
| Subsequent runs | High — profile reuse, no credential handling in code |
| Session expiry | Triggers a new HITL re-login prompt |

### Artifacts produced by auto-application

After successful submission, write under `data/jobs/<source>/<job_id>/nodes/apply/`:

```
proposed/
  application_record.json    # what was filled, when, confirmation URL/text
  form_field_map.json        # the LLM-inferred form field map
  confirmation.md            # human-readable confirmation surface
meta/
  apply_meta.json            # success flag, method, timestamp, error if any
```

### Submission safety rules

- **Human approval gate before first submission to any new domain.** The system proposes the `FormFieldMap` and mapped values; a human confirms before the form is actually submitted. This gate can be relaxed per domain after first successful use.
- **Dry-run mode**: fills the form but does not submit (`skip_submit=True` flag). Produces a screenshot artifact for review.
- **No submitting the same job twice.** Check `apply_meta.json` existence before proceeding.

---

## Open Questions

- Should company-portal-discovered jobs be treated as a new `source` value or as a sub-source under the originating aggregator?
- Which ATS platforms to prioritize first? Greenhouse and Lever are the cleanest; Workday is the most common but hardest (SPA + Cloudflare).
- What is the right HITL gate for auto-application? Per-domain once for form approval, per-job always for final submission confirmation, or opt-in per run?
- File formats: some portals only accept `.docx`, others only `.pdf`. The render pipeline already supports both — this needs to be wired into the form analyzer's `cv_upload` resolution.
- Where do browser profiles live? `data/profiles/` is convenient but should not be committed. Add to `.gitignore`.

## Linked TODOs

None yet — this is a planning-phase document. Inline TODOs will be added when implementation begins.
