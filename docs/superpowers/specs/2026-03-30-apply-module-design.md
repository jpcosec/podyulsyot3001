# Design Spec — `src/apply/` Auto-Application Module

**Date:** 2026-03-30
**Scope:** Standalone CLI module for automated job application via XING Easy Apply and StepStone Easy Apply. Reads from an existing ingested job artifact, fills and submits the application form using a persistent browser session.

---

## 1. Module Layout

```
src/apply/
  __init__.py
  main.py              # CLI entry point and provider registry
  smart_adapter.py     # ApplyAdapter ABC and shared execution logic
  models.py            # FormSelectors, ApplicationRecord, ApplyMeta
  providers/
    xing/adapter.py
    stepstone/adapter.py
  README.md
```

---

## 2. CLI

```bash
python -m src.apply.main \
  --source xing \
  --job-id 12345 \
  --cv path/to/cv.pdf \
  [--letter path/to/letter.pdf] \
  [--dry-run]
```

**Inputs:**
- `--source` + `--job-id`: locates the job. Reads `data/jobs/<source>/<job_id>/nodes/ingest/proposed/state.json` to get `application_url`, `job_title`, `company_name`.
- `--cv`: path to the CV PDF. Passed explicitly — the module does not search for it in artifacts.
- `--letter`: optional. If the portal does not request it, it is ignored.
- `--dry-run`: activates marcha blanca mode (see Section 5).

---

## 3. Models (`models.py`)

```python
class FormSelectors(BaseModel):
    """All CSS selectors the adapter depends on. Validated against the live DOM before interaction."""

    # Mandatory — absence raises PortalStructureChangedError
    apply_button: str
    cv_upload: str
    submit_button: str
    success_indicator: str

    # Optional — absence is logged as warning, interaction skipped
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    letter_upload: str | None = None
    error_indicator: str | None = None
    cv_select_existing: str | None = None  # for portals that prefer selecting a saved CV over uploading


class ApplicationRecord(BaseModel):
    source: str
    job_id: str
    job_title: str
    company_name: str
    application_url: str
    cv_path: str
    letter_path: str | None
    fields_filled: list[str]
    dry_run: bool
    submitted_at: str | None
    confirmation_text: str | None


class ApplyMeta(BaseModel):
    status: Literal["submitted", "dry_run", "failed", "portal_changed"]
    timestamp: str
    error: str | None = None
```

---

## 4. ABC — `ApplyAdapter` (`smart_adapter.py`)

Adapters provide **only** portal-specific knowledge. All flow control lives in the base class.

Portal-specific interaction sequences are expressed as **C4A-Script** — crawl4ai's human-readable DSL for web automation (`CLICK`, `SET`, `WAIT`, `IF/THEN`, `REPEAT`). This keeps each adapter file readable and maintainable without generating JS strings. File upload (`set_input_files`) remains the one exception handled via a Playwright hook, as C4A-Script has no file upload primitive.

```python
class PortalStructureChangedError(Exception):
    """Raised when a mandatory selector is absent from the live DOM."""


class ApplyAdapter(ABC):
    def __init__(self, data_manager: DataManager | None = None): ...

    @property
    @abstractmethod
    def source_name(self) -> str: ...

    @abstractmethod
    def get_form_selectors(self) -> FormSelectors:
        """Mandatory and optional selectors. Validated against the DOM before execution."""

    @abstractmethod
    def get_apply_script(self, profile: dict) -> str:
        """C4A-Script template for the full apply interaction sequence.

        Profile values are interpolated into the script by the base class.
        The script covers: open modal → fill fields → (submit or stop before submit).
        File upload steps are omitted here — handled by the Playwright hook.

        Example (XING Easy Apply):
            CLICK `[data-testid="apply-button"]`
            WAIT `input[name="firstName"]` 5
            SET `input[name="firstName"]` "{{first_name}}"
            SET `input[name="lastName"]` "{{last_name}}"
            SET `input[type="email"]` "{{email}}"
            IF `select[name="salutation"]` THEN
              SET `select[name="salutation"]` "{{salutation}}"
            END
        """

    @abstractmethod
    def get_submit_script(self) -> str:
        """C4A-Script for the submit step — separated so dry-run can stop before it."""

    @abstractmethod
    def get_success_text(self) -> str:
        """Text fragment expected in the confirmation state (second validation layer)."""

    @abstractmethod
    def get_session_profile_dir(self) -> Path:
        """Path to the persistent browser profile for this portal."""

    # All logic below lives in the base class:
    async def run(self, job_id, cv_path, letter_path, dry_run) -> ApplyMeta: ...
    async def _validate_selectors(self, result, selectors) -> None: ...
    async def _validate_success_text(self, result) -> bool: ...
```

---

## 5. Execution Flow

The flow uses crawl4ai natively throughout. Each step is a separate `arun()` call sharing the same `session_id`. Raw Playwright is used **only** for file uploads inside a hook, because `set_input_files` has no browser-JS equivalent for security reasons.

```
read ingest artifact → get application_url, job_title, company_name
    ↓
idempotency check: if apply_meta.json status=submitted → abort with warning
    ↓
build BrowserConfig(user_data_dir=profile_dir, use_persistent_context=True)
    ↓  session carries prior login cookies — no credential handling in code
    ↓  if session expired → portal redirects to login → PortalStructureChangedError
    ↓  (human re-logs in via --setup-session and retries)
    ↓
[try block starts here]
    ↓
Step 1 — navigate + open apply modal (C4A-Script):
  CrawlerRunConfig(
    c4a_script=adapter.get_apply_script(profile),  ← portal-specific DSL
    wait_for=f"css:{selectors.cv_upload or selectors.first_name}",  ← first interactable field
    session_id="apply_{job_id}",
  )
    ↓  C4A-Script handles: CLICK apply button, WAIT, SET fields, IF/THEN for optional fields
    ↓
_validate_selectors(result, selectors)   ← runtime check #1
    ↓ missing mandatory selector → PortalStructureChangedError
    ↓
Step 2 — file upload (Playwright hook — only exception to crawl4ai-native):
  CrawlerRunConfig(
    js_only=True,
    hooks={"on_page_context_created": _file_upload_hook(cv_path, letter_path, selectors)},
    session_id="apply_{job_id}",
  )
    ↓  hook uses page.set_input_files() — no browser-JS equivalent exists
    ↓
  cv fallback: if cv_upload absent but cv_select_existing present →
    C4A-Script: CLICK `{selectors.cv_select_existing}`
    ↓
Step 3 — screenshot before submit (always):
  CrawlerRunConfig(
    js_only=True,
    screenshot=True,
    session_id="apply_{job_id}",
  )
  → proposed/screenshot.png
    ↓
[dry-run] → write ApplicationRecord + ApplyMeta(status=dry_run) → exit
    ↓
[auto] Step 4 — submit + verify (C4A-Script):
  CrawlerRunConfig(
    c4a_script=adapter.get_submit_script(),
    wait_for=f"css:{selectors.success_indicator}",
    screenshot=True,
    session_id="apply_{job_id}",
  )
    ↓
_validate_success_text(result)           ← runtime check #2
    ↓ text not found → LogTag.WARN only (copy changes are common)
    ↓
write ApplicationRecord + ApplyMeta(status=submitted)

[except block]
    → CrawlerRunConfig(js_only=True, screenshot=True, session_id=...) → error_state.png
    → write ApplyMeta(status=portal_changed or failed, error=str(exc))
    → raise
```

### Why C4A-Script for portal-specific behavior

Each adapter's `get_apply_script()` and `get_submit_script()` are readable, self-documenting sequences. `IF/THEN` handles conditional fields (e.g. salutation dropdowns that only appear on certain locales) without Python branching. `WAIT` with element readiness avoids the flaky "element in DOM but not interactive" problem naturally. `EVAL` is available as escape hatch for edge cases that need raw JS.

---

## 6. Session Management

Session persistence is handled via crawl4ai's native `BrowserConfig`:

```python
BrowserConfig(
    user_data_dir=str(adapter.get_session_profile_dir()),
    use_persistent_context=True,
    headless=True,
)
```

Profile directories:
```
data/profiles/
  xing_profile/
  stepstone_profile/
```

These directories are `.gitignore`d — they contain live session cookies, never committed.

**First-time setup (HITL):** User runs `python -m src.apply.main --source xing --setup-session`, which opens a visible browser pointing at the profile dir. User logs in manually and closes. Subsequent runs reuse the session headlessly. When the session expires, the portal redirects to login and `_validate_selectors` raises `PortalStructureChangedError` with a message indicating session refresh is needed.

---

## 7. Runtime Validation — Two Layers

### Layer 1 — `_validate_selectors(selectors)` (after Step 1, before file upload)

Runs a dedicated `arun()` call with `js_only=True` and a `js_code` snippet that queries every non-None selector and returns a presence map:

```javascript
JSON.stringify({
    apply_button: !!document.querySelector('...'),
    cv_upload: !!document.querySelector('...'),
    submit_button: !!document.querySelector('...'),
    // ... all selectors
})
```

The base class parses `result.extracted_content`, checks the map:
- **Mandatory selector absent** → `PortalStructureChangedError` with full list of missing selectors → error screenshot → `apply_meta.json` with `status=portal_changed`
- **Optional selector absent** → `LogTag.WARN`, field skipped, execution continues

### Layer 2 — `_validate_success_text(result)` (after submit)

Checks `result.markdown` or `result.cleaned_html` for the `get_success_text()` fragment:
- Not found → `LogTag.WARN` only (copy changes are common, not structural failures)
- Found → confirms submission is complete

Both results are persisted in `apply_meta.json` and visible in logs with structured tags.

---

## 8. Artifacts Written

```
data/jobs/<source>/<job_id>/nodes/apply/
  proposed/
    application_record.json   # filled fields, cv path, submitted_at, confirmation text
    screenshot.png            # state just before submit (dry-run and auto)
    error_state.png           # written only on exception — for debugging
  meta/
    apply_meta.json           # status, timestamp, error
```

---

## 9. Provider Implementations

Each provider implements only:
- `source_name` property
- `get_form_selectors()` — CSS selectors discovered by sampling real apply pages
- `get_apply_script(profile)` — C4A-Script for opening modal + filling text fields
- `get_submit_script()` — C4A-Script for the submit action (separated for dry-run support)
- `get_success_text()` — expected confirmation copy
- `get_session_profile_dir()` — path to the persistent browser profile

**Precondition:** The C4A-Script and selectors for XING and StepStone Easy Apply must be discovered by sampling real apply pages before implementation. This sampling step is also what produces the HTML fixtures needed for integration tests.

---

## 10. Tests

- **Unit tests** with `AsyncMock` Playwright page: verify `_validate_selectors` raises on missing mandatory selectors, warns on missing optional ones.
- **Integration tests** against saved HTML snapshots of real apply forms (not live portals). These are the primary regression guard against DOM changes.
- Snapshot fixtures are stored under `tests/fixtures/apply/` and refreshed manually when portals update their UI.
- The `error_state.png` mechanism makes live debugging tractable without test infrastructure on CI.

---

## 11. Out of Scope (this version)

- Email-based application
- Company ATS portals (Workday, Greenhouse, etc.) — future stage
- Cross-portal discovery — separate future module
- CV/letter generation — caller's responsibility; module receives paths
- Selecting between multiple CVs / cover letter variants
