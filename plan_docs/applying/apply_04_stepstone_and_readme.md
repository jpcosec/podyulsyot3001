# Apply Module — StepStone Adapter and README

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the StepStone Easy Apply adapter (same structure as XING, same discovery process) and write the module README.

**Architecture:** Identical to `apply_03_xing_adapter.md`. `StepStoneApplyAdapter` extends `ApplyAdapter`, implements 8 abstract methods, and gets integration tests against a real HTML snapshot. The README documents usage, session setup, dry-run mode, and artifact layout.

**Tech Stack:** Same as `apply_03` — Pydantic, pytest, BeautifulSoup, C4A-Script.

---

## Design Rules

Same rules as `apply_03_xing_adapter.md`:

1. **Selectors must be discovered from a real StepStone Easy Apply page.** StepStone's Easy Apply uses `data-at` attributes in many places. Prefer those over class names.
2. **`get_open_modal_script()` must be idempotent** — guard with `IF NOT` check.
3. **`get_fill_form_script()` uses `{{placeholder}}` syntax** — never raw f-string values.
4. **HTML fixture goes in `tests/fixtures/apply/stepstone_apply_modal.html`** — same capture pattern as XING.
5. **Mirror `src/scraper/providers/stepstone/adapter.py` file layout.** Read it before writing.
6. **Profile directory: `data/profiles/stepstone_profile/`** — already gitignored via `data/`.

---

## File Structure

- Create: `src/apply/providers/stepstone/__init__.py`
- Create: `src/apply/providers/stepstone/adapter.py`
- Create: `tests/fixtures/apply/stepstone_apply_modal.html` (from real session)
- Create: `src/apply/README.md`
- Test: `tests/test_apply_stepstone_adapter.py`

---

### Task 1: Capture StepStone HTML Fixture

Same process as XING — must be done before implementing selectors.

- [ ] **Step 1: Capture StepStone apply modal HTML**

```python
# scripts/capture_stepstone_apply_fixture.py (run once, not committed as a test)
"""Capture StepStone Easy Apply modal HTML for use as a test fixture.

Prerequisites:
  - Run `python -m src.apply.main --source stepstone --setup-session` first

Usage:
  python scripts/capture_stepstone_apply_fixture.py --job-url <URL>
"""
import argparse
import asyncio
from pathlib import Path

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


async def capture(job_url: str, output_path: Path) -> None:
    config = BrowserConfig(
        user_data_dir="data/profiles/stepstone_profile",
        use_persistent_context=True,
        headless=False,
    )
    async with AsyncWebCrawler(config=config) as crawler:
        result = await crawler.arun(
            url=job_url,
            config=CrawlerRunConfig(
                # Replace with real StepStone apply button selector after DOM inspection
                c4a_script="CLICK `[data-at='apply-button']`\nWAIT `[data-at='apply-modal']` 10",
                screenshot=True,
            ),
        )
        if result.success:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(result.cleaned_html or result.html or "", encoding="utf-8")
            print(f"Saved fixture to {output_path}")
        else:
            print(f"Failed: {result.error_message}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-url", required=True)
    args = parser.parse_args()
    asyncio.run(capture(args.job_url, Path("tests/fixtures/apply/stepstone_apply_modal.html")))
```

- [ ] **Step 2: Inspect captured HTML and record real StepStone selectors**

Open `tests/fixtures/apply/stepstone_apply_modal.html`. StepStone commonly uses:
- `data-at` attributes (e.g. `[data-at="apply-button"]`)
- Numeric job IDs in form field names

Record selectors for: apply button, modal container, CV upload, first/last name, email, submit button, success indicator.

---

### Task 2: StepStone Adapter Implementation

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_apply_stepstone_adapter.py
"""Integration tests for StepStoneApplyAdapter against HTML snapshots.

Same pattern as tests/test_apply_xing_adapter.py.

If the fixture file is missing, tests are skipped with a clear message.
Update the fixture by running: python scripts/capture_stepstone_apply_fixture.py
"""
from __future__ import annotations

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

FIXTURE_PATH = Path("tests/fixtures/apply/stepstone_apply_modal.html")


@pytest.fixture
def stepstone_html() -> str:
    if not FIXTURE_PATH.exists():
        pytest.skip(
            f"StepStone fixture not found at {FIXTURE_PATH}. "
            "Run: python scripts/capture_stepstone_apply_fixture.py --job-url <URL>"
        )
    return FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture
def adapter():
    from src.apply.providers.stepstone.adapter import StepStoneApplyAdapter
    return StepStoneApplyAdapter()


def test_source_name(adapter):
    assert adapter.source_name == "stepstone"


def test_session_profile_dir(adapter):
    assert "stepstone" in str(adapter.get_session_profile_dir()).lower()


def test_get_form_selectors_returns_all_mandatory(adapter):
    selectors = adapter.get_form_selectors()
    assert selectors.apply_button
    assert selectors.cv_upload
    assert selectors.submit_button
    assert selectors.success_indicator


def test_mandatory_selectors_found_in_fixture(adapter, stepstone_html):
    soup = BeautifulSoup(stepstone_html, "html.parser")
    selectors = adapter.get_form_selectors()
    for field in ("apply_button", "cv_upload", "submit_button"):
        sel = getattr(selectors, field)
        match = soup.select(sel)
        assert match, (
            f"Mandatory selector '{field}' = '{sel}' not found in StepStone fixture. "
            "DOM may have changed — re-capture fixture and update selectors."
        )


def test_optional_selectors_found_in_fixture(adapter, stepstone_html):
    soup = BeautifulSoup(stepstone_html, "html.parser")
    selectors = adapter.get_form_selectors()
    for field in ["first_name", "last_name", "email", "phone", "letter_upload"]:
        sel = getattr(selectors, field)
        if sel is None:
            continue
        match = soup.select(sel)
        assert match, (
            f"Optional selector '{field}' = '{sel}' not found in StepStone fixture."
        )


def test_open_modal_script_is_idempotent(adapter):
    script = adapter.get_open_modal_script()
    assert "IF NOT" in script


def test_fill_form_script_uses_placeholders(adapter):
    profile = {"first_name": "Alice", "last_name": "Smith", "email": "a@b.com"}
    script = adapter.get_fill_form_script(profile)
    assert "{{" in script, (
        "get_fill_form_script() must use {{placeholder}} syntax. "
        "Do not interpolate profile values directly — let _render_script() handle escaping."
    )
    assert "Alice" not in script
    assert "Smith" not in script


def test_render_script_injects_values(adapter):
    profile = {"first_name": "Alice", "last_name": "Smith"}
    template = adapter.get_fill_form_script(profile)
    rendered = adapter._render_script(template, profile)
    assert "{{first_name}}" not in rendered
    assert "{{last_name}}" not in rendered


def test_get_portal_base_url(adapter):
    assert "stepstone" in adapter._get_portal_base_url().lower()


def test_get_success_text_not_empty(adapter):
    assert adapter.get_success_text().strip()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_apply_stepstone_adapter.py -v
```

Expected: `ImportError: cannot import name 'StepStoneApplyAdapter'`

- [ ] **Step 3: Create `src/apply/providers/stepstone/__init__.py`**

```python
```

(empty file)

- [ ] **Step 4: Create `src/apply/providers/stepstone/adapter.py`**

> **Important:** Replace placeholder selectors with real selectors discovered from the HTML fixture in Task 1.

```python
"""StepStone Easy Apply adapter.

Design reference: `src/apply/README.md` and `plan_docs/applying/applying_feature_design.md`

Selector discovery: inspect tests/fixtures/apply/stepstone_apply_modal.html
  - Prefer data-at attributes — StepStone commonly uses these for test targeting
  - The selectors below are placeholders — update them after DOM inspection

C4A-Script docs: https://docs.crawl4ai.com/core/c4a-script/
"""
from __future__ import annotations

from pathlib import Path

from src.apply.models import FormSelectors
from src.apply.smart_adapter import ApplyAdapter


class StepStoneApplyAdapter(ApplyAdapter):
    """Adapter for StepStone Easy Apply inline application flow."""

    @property
    def source_name(self) -> str:
        return "stepstone"

    def _get_portal_base_url(self) -> str:
        return "https://www.stepstone.de"

    def get_session_profile_dir(self) -> Path:
        return Path("data/profiles/stepstone_profile")

    def get_form_selectors(self) -> FormSelectors:
        """CSS selectors for the StepStone Easy Apply modal.

        Discovered by inspecting tests/fixtures/apply/stepstone_apply_modal.html.
        Update these selectors if StepStone updates their DOM (tests will fail first).

        Prefer data-at selectors over class names.
        """
        return FormSelectors(
            # Mandatory — update with real selectors from fixture
            apply_button="[data-at='apply-button']",
            cv_upload="input[type='file']",
            submit_button="[data-at='submit-button']",
            success_indicator="[data-at='application-success']",
            # Optional — set to None if not present in StepStone Easy Apply flow
            first_name="input[name='firstName']",
            last_name="input[name='lastName']",
            email="input[type='email']",
            phone="input[name='phone']",
            letter_upload=None,  # StepStone may or may not request a cover letter
            cv_select_existing=None,
        )

    def get_open_modal_script(self) -> str:
        """Open the Easy Apply modal. Idempotent: checks if modal already open."""
        return """
IF NOT `[data-at="apply-modal"]` THEN
  CLICK `[data-at="apply-button"]`
  WAIT `[data-at="apply-modal"]` 10
END
"""

    def get_fill_form_script(self, profile: dict) -> str:
        """C4A-Script to fill the StepStone Easy Apply form text fields.

        Uses {{placeholder}} syntax — _render_script() injects values via json.dumps().
        Update field selectors to match real StepStone form structure.
        """
        return """
SET `input[name="firstName"]` "{{first_name}}"
SET `input[name="lastName"]` "{{last_name}}"
SET `input[type="email"]` "{{email}}"
IF `input[name="phone"]` THEN
  SET `input[name="phone"]` "{{phone}}"
END
"""

    def get_submit_script(self) -> str:
        """C4A-Script to click submit. Separated from fill for dry-run support."""
        return """
CLICK `[data-at="submit-button"]`
WAIT `[data-at="application-success"]` 15
"""

    def get_success_text(self) -> str:
        """Expected text fragment in the confirmation page after submission.

        Update with actual StepStone confirmation copy once discovered.
        Common German patterns: 'Bewerbung gesendet', 'Erfolgreich beworben', etc.
        """
        return "Bewerbung"
```

- [ ] **Step 5: Run tests**

```bash
python -m pytest tests/test_apply_stepstone_adapter.py -v
```

Expected: structural tests PASS, fixture tests SKIP (or PASS if fixture captured).

- [ ] **Step 6: Update selectors from fixture, re-run fixture tests**

```bash
python -m pytest tests/test_apply_stepstone_adapter.py::test_mandatory_selectors_found_in_fixture -v
python -m pytest tests/test_apply_stepstone_adapter.py::test_optional_selectors_found_in_fixture -v
```

Iterate on selectors until all fixture tests pass.

- [ ] **Step 7: Commit adapter**

```bash
git add src/apply/providers/stepstone/ tests/test_apply_stepstone_adapter.py tests/fixtures/apply/
git commit -m "feat(apply): add StepStone Easy Apply adapter with snapshot integration tests"
```

---

### Task 3: Module README

- [ ] **Step 1: Create `src/apply/README.md`**

```markdown
# src/apply — Auto-Application Module

Standalone CLI module for automated job application via XING Easy Apply and StepStone Easy Apply.

Reads from an existing ingested job artifact, fills and submits the application form using a persistent browser session.

**Design references:** `src/apply/README.md`, `plan_docs/applying/applying_feature_design.md`

---

## Usage

### First-time session setup (run once per portal)

```bash
python -m src.apply.main --source xing --setup-session
python -m src.apply.main --source stepstone --setup-session
```

This opens a visible browser at the portal URL. Log in manually, then press Enter. Session cookies are saved to `data/profiles/<portal>_profile/` and reused headlessly on all subsequent runs.

### Apply to a job

```bash
# Dry-run (fills form, takes screenshot, does NOT submit)
python -m src.apply.main \
  --source xing \
  --job-id 12345 \
  --cv path/to/cv.pdf \
  --dry-run

# Auto mode (submits the application)
python -m src.apply.main \
  --source xing \
  --job-id 12345 \
  --cv path/to/cv.pdf \
  --letter path/to/letter.pdf
```

The `--job-id` must match an already-ingested job under `data/jobs/xing/12345/`. The module reads `nodes/ingest/proposed/state.json` to get `application_url`, `job_title`, and `company_name`.

### Check apply status

```bash
cat data/jobs/xing/12345/nodes/apply/meta/apply_meta.json
```

---

## Idempotency

| Prior status | Behaviour |
|---|---|
| `submitted` | Blocked — application already sent |
| `dry_run` | Allowed — dry-run artifacts overwritten |
| `failed` | Allowed — retry |
| `portal_changed` | Allowed — retry after fixing selectors |
| missing | Allowed — first run |

---

## Artifacts

```
data/jobs/<source>/<job_id>/nodes/apply/
  proposed/
    application_record.json   # filled fields, cv path, submitted_at
    screenshot.png            # state just before submit (dry-run and auto)
    screenshot_submitted.png  # state after submit (auto only)
    error_state.png           # written only on exception — for debugging
  meta/
    apply_meta.json           # status, timestamp, error
```

---

## When the portal changes

If XING or StepStone updates their DOM, `_validate_selectors()` raises `PortalStructureChangedError` and writes `apply_meta.json` with `status=portal_changed`.

Fix process:
1. Run the fixture capture script to get fresh HTML
2. Compare with the old fixture
3. Update selectors in `src/apply/providers/<portal>/adapter.py`
4. Re-run integration tests: `python -m pytest tests/test_apply_<portal>_adapter.py -v`

---

## Adding a new portal

1. Create `src/apply/providers/<name>/__init__.py` and `adapter.py`
2. Extend `ApplyAdapter` and implement the 8 abstract methods
3. Capture HTML fixture with a one-off script (see `apply_03_xing_adapter.md` Task 1 for pattern)
4. Write integration tests against the fixture
5. Register the adapter in `src/apply/main.py:build_providers()`
```

- [ ] **Step 2: Run the full apply test suite**

```bash
python -m pytest tests/test_apply_models.py tests/test_apply_base_adapter.py tests/test_apply_xing_adapter.py tests/test_apply_stepstone_adapter.py -v
```

Expected: All non-fixture tests PASS. Fixture tests PASS (if fixtures captured) or SKIP (if not yet captured).

- [ ] **Step 3: Run the full project test suite to check for regressions**

```bash
python -m pytest tests/ -q
```

Expected: No regressions. New tests pass or skip.

- [ ] **Step 4: Final commit**

```bash
git add src/apply/README.md
git commit -m "docs(apply): add module README with usage, artifacts, and portal change guide"
```
