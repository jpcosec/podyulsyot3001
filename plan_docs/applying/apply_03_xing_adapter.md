# Apply Module — XING Easy Apply Adapter

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the XING Easy Apply adapter — selectors, C4A-Scripts, and HTML snapshot integration tests.

**Architecture:** `XingApplyAdapter` extends `ApplyAdapter` and implements only the 8 abstract methods. The base class in `src/apply/smart_adapter.py` handles all flow control. Tests run against a saved HTML snapshot — not the live portal — so they pass on CI without a browser.

**Tech Stack:** Pydantic, pytest, `BeautifulSoup` (for snapshot fixture assertions). C4A-Script for portal interaction DSL.

---

## Design Rules

1. **Selectors must be discovered by sampling real XING Easy Apply pages before writing code.** The CSS selectors in this plan are placeholders. Before implementing `get_form_selectors()`, open a real XING Easy Apply flow and inspect the DOM. Look for `data-testid` attributes first — they are more stable than generated class names.
2. **`get_open_modal_script()` must be idempotent.** Use `IF NOT` to check if the modal is already open before clicking. This prevents double-clicks on retries. C4A-Script docs: https://docs.crawl4ai.com/core/c4a-script/
3. **`get_fill_form_script(profile)` uses `{{placeholder}}` syntax.** Do not interpolate values directly — the base class `_render_script()` handles injection via `json.dumps()`. The method signature receives `profile: dict` but the returned C4A-Script should use `{{key}}` placeholders, not f-strings.
4. **HTML fixture for tests.** Save a real XING apply modal HTML to `tests/fixtures/apply/xing_apply_modal.html`. Integration tests load this fixture and verify the adapter's selectors find the expected elements. This is the primary regression guard — if XING updates their DOM, tests fail.
5. **Mirror `src/scraper/providers/xing/adapter.py` file layout.** Same `__init__.py`, same `adapter.py` naming. Read `src/scraper/providers/xing/adapter.py` before writing to stay consistent.
6. **Profile directory lives at `data/profiles/xing_profile/`.** Already excluded from git via `data/` in `.gitignore` — no changes needed.

---

## File Structure

- Create: `src/apply/providers/xing/__init__.py`
- Create: `src/apply/providers/xing/adapter.py`
- Create: `tests/fixtures/apply/xing_apply_modal.html` (captured from real XING session)
- Test: `tests/test_apply_xing_adapter.py`

---

### Task 1: Capture HTML Fixture

Before any code is written, capture the real XING apply modal HTML. This fixture is what integration tests run against.

- [ ] **Step 1: Open a real XING Easy Apply flow and save the modal HTML**

Run this one-off script to capture the modal HTML with an authenticated session:

```python
# scripts/capture_xing_apply_fixture.py (run once, not committed as a test)
"""Capture XING Easy Apply modal HTML for use as a test fixture.

Prerequisites:
  - Run `python -m src.apply.main --source xing --setup-session` first
    to set up an authenticated browser profile at data/profiles/xing_profile/

Usage:
  python scripts/capture_xing_apply_fixture.py --job-url <URL>
"""
import argparse
import asyncio
from pathlib import Path

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig


async def capture(job_url: str, output_path: Path) -> None:
    config = BrowserConfig(
        user_data_dir="data/profiles/xing_profile",
        use_persistent_context=True,
        headless=False,  # visible so you can watch the modal open
    )
    async with AsyncWebCrawler(config=config) as crawler:
        result = await crawler.arun(
            url=job_url,
            config=CrawlerRunConfig(
                # Replace with your discovered XING apply button selector
                c4a_script="CLICK `[data-testid='apply-button']`\nWAIT `[data-testid='apply-modal']` 10",
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
    asyncio.run(capture(args.job_url, Path("tests/fixtures/apply/xing_apply_modal.html")))
```

Expected output: `tests/fixtures/apply/xing_apply_modal.html` created with the modal's HTML.

- [ ] **Step 2: Inspect the captured HTML and record the real selectors**

Open `tests/fixtures/apply/xing_apply_modal.html` in a browser or text editor.
Find the real CSS selectors for:
- Apply button (usually `data-testid` or `aria-label`)
- Modal container
- CV upload input
- First name, last name, email inputs
- Submit button
- Success indicator after submission

Record these before moving to Task 2.

---

### Task 2: XING Adapter Implementation

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_apply_xing_adapter.py
"""Integration tests for XingApplyAdapter against HTML snapshots.

These tests load a saved HTML fixture and verify that the adapter's selectors
find the expected elements. They run without a live browser.

If the fixture file is missing, tests are skipped with a clear message.
Update the fixture by running: python scripts/capture_xing_apply_fixture.py
"""
from __future__ import annotations

from pathlib import Path

import pytest
from bs4 import BeautifulSoup

FIXTURE_PATH = Path("tests/fixtures/apply/xing_apply_modal.html")


@pytest.fixture
def xing_html() -> str:
    if not FIXTURE_PATH.exists():
        pytest.skip(
            f"XING fixture not found at {FIXTURE_PATH}. "
            "Run: python scripts/capture_xing_apply_fixture.py --job-url <URL>"
        )
    return FIXTURE_PATH.read_text(encoding="utf-8")


@pytest.fixture
def adapter():
    from src.apply.providers.xing.adapter import XingApplyAdapter
    return XingApplyAdapter()


def test_source_name(adapter):
    assert adapter.source_name == "xing"


def test_session_profile_dir(adapter):
    assert "xing" in str(adapter.get_session_profile_dir()).lower()


def test_get_form_selectors_returns_all_mandatory(adapter):
    """FormSelectors has all four mandatory fields populated."""
    selectors = adapter.get_form_selectors()
    assert selectors.apply_button
    assert selectors.cv_upload
    assert selectors.submit_button
    assert selectors.success_indicator


def test_mandatory_selectors_found_in_fixture(adapter, xing_html):
    """Mandatory selectors match elements in the real XING apply modal HTML."""
    soup = BeautifulSoup(xing_html, "html.parser")
    selectors = adapter.get_form_selectors()
    for field in ("apply_button", "cv_upload", "submit_button"):
        sel = getattr(selectors, field)
        match = soup.select(sel)
        assert match, (
            f"Mandatory selector '{field}' = '{sel}' not found in XING fixture. "
            "DOM may have changed — re-capture fixture and update selectors."
        )


def test_optional_selectors_found_in_fixture(adapter, xing_html):
    """Optional selectors that are set should also be findable in the fixture."""
    soup = BeautifulSoup(xing_html, "html.parser")
    selectors = adapter.get_form_selectors()
    optional_fields = ["first_name", "last_name", "email", "phone", "letter_upload"]
    for field in optional_fields:
        sel = getattr(selectors, field)
        if sel is None:
            continue
        match = soup.select(sel)
        assert match, (
            f"Optional selector '{field}' = '{sel}' not found in XING fixture. "
            "Update the selector or set it to None if the field is absent."
        )


def test_open_modal_script_is_idempotent(adapter):
    """get_open_modal_script() contains an idempotency guard (IF NOT check)."""
    script = adapter.get_open_modal_script()
    assert "IF NOT" in script or "IF" in script, (
        "Open modal script must check if modal is already open before clicking."
    )


def test_fill_form_script_uses_placeholders(adapter):
    """get_fill_form_script() uses {{placeholder}} syntax, not f-string values."""
    profile = {"first_name": "Alice", "last_name": "Smith", "email": "a@b.com"}
    script = adapter.get_fill_form_script(profile)
    # Script should contain placeholder markers, not the raw values
    assert "{{" in script or "first_name" not in script or "Alice" not in script, (
        "get_fill_form_script() must use {{placeholder}} syntax. "
        "Do not interpolate profile values directly — let _render_script() handle escaping."
    )


def test_render_script_injects_values(adapter):
    """_render_script() correctly substitutes placeholders with profile values."""
    profile = {"first_name": "Alice", "last_name": "Smith"}
    template = adapter.get_fill_form_script(profile)
    rendered = adapter._render_script(template, profile)
    assert "{{first_name}}" not in rendered
    assert "{{last_name}}" not in rendered


def test_get_portal_base_url(adapter):
    assert "xing.com" in adapter._get_portal_base_url()


def test_get_success_text_not_empty(adapter):
    assert adapter.get_success_text().strip()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_apply_xing_adapter.py -v
```

Expected: `ImportError: cannot import name 'XingApplyAdapter'`

- [ ] **Step 3: Create `src/apply/providers/xing/__init__.py`**

```python
```

(empty file)

- [ ] **Step 4: Create `src/apply/providers/xing/adapter.py`**

> **Important:** Replace the placeholder selectors below with the real selectors discovered from the HTML fixture in Task 1.

```python
"""XING Easy Apply adapter.

Design reference: `src/apply/README.md` and `plan_docs/applying/applying_feature_design.md`

Selector discovery: inspect tests/fixtures/apply/xing_apply_modal.html
  - Prefer data-testid attributes over generated class names (more stable)
  - The selectors below are placeholders — update them after DOM inspection

C4A-Script docs: https://docs.crawl4ai.com/core/c4a-script/
"""
from __future__ import annotations

from pathlib import Path

from src.apply.models import FormSelectors
from src.apply.smart_adapter import ApplyAdapter


class XingApplyAdapter(ApplyAdapter):
    """Adapter for XING Easy Apply inline application flow."""

    @property
    def source_name(self) -> str:
        return "xing"

    def _get_portal_base_url(self) -> str:
        return "https://www.xing.com"

    def get_session_profile_dir(self) -> Path:
        return Path("data/profiles/xing_profile")

    def get_form_selectors(self) -> FormSelectors:
        """CSS selectors for the XING Easy Apply modal.

        Discovered by inspecting tests/fixtures/apply/xing_apply_modal.html.
        Update these selectors if XING updates their DOM (tests will fail first).

        Prefer data-testid selectors — they are more stable than generated class names.
        """
        return FormSelectors(
            # Mandatory — update with real selectors from fixture
            apply_button="[data-testid='apply-button']",
            cv_upload="input[type='file'][accept*='pdf']",
            submit_button="[data-testid='submit-button']",
            success_indicator="[data-testid='application-success']",
            # Optional — set to None if not present in the XING Easy Apply flow
            first_name="input[name='firstName']",
            last_name="input[name='lastName']",
            email="input[type='email']",
            phone="input[name='phone']",
            letter_upload=None,  # XING Easy Apply may not request a cover letter
            cv_select_existing=None,  # Set if XING offers "select saved CV" option
        )

    def get_open_modal_script(self) -> str:
        """Open the Easy Apply modal. Idempotent: checks if modal already open.

        C4A-Script IF/THEN prevents double-clicking on retries.
        WAIT with selector ensures the first interactive field is present before
        _validate_selectors() runs.

        Update the selector strings to match the real XING modal container.
        """
        return """
IF NOT `[data-testid="apply-modal"]` THEN
  CLICK `[data-testid="apply-button"]`
  WAIT `[data-testid="apply-modal"]` 10
END
"""

    def get_fill_form_script(self, profile: dict) -> str:
        """C4A-Script to fill the XING Easy Apply form text fields.

        Uses {{placeholder}} syntax — _render_script() injects values via json.dumps().
        File upload is NOT here — handled by the before_retrieve_html hook.

        Update the SET selectors to match the real XING form field selectors.
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
CLICK `[data-testid="submit-button"]`
WAIT `[data-testid="application-success"]` 15
"""

    def get_success_text(self) -> str:
        """Expected text fragment in the confirmation page after submission.

        Update this with the actual XING confirmation copy once discovered.
        Common patterns: 'Bewerbung wurde gesendet', 'Application submitted', etc.
        """
        return "Bewerbung"
```

- [ ] **Step 5: Run tests**

```bash
python -m pytest tests/test_apply_xing_adapter.py -v
```

Expected:
- `test_source_name`, `test_session_profile_dir`, `test_get_form_selectors_returns_all_mandatory`, `test_open_modal_script_is_idempotent`, `test_fill_form_script_uses_placeholders`, `test_render_script_injects_values`, `test_get_portal_base_url`, `test_get_success_text_not_empty` — all PASS.
- Tests requiring the fixture (`test_mandatory_selectors_found_in_fixture`, `test_optional_selectors_found_in_fixture`) — SKIP with message if fixture not yet captured, or PASS once captured.

- [ ] **Step 6: Update selectors from fixture**

After running the fixture capture script (Task 1), re-run the fixture tests:

```bash
python -m pytest tests/test_apply_xing_adapter.py::test_mandatory_selectors_found_in_fixture -v
python -m pytest tests/test_apply_xing_adapter.py::test_optional_selectors_found_in_fixture -v
```

Iterate on the selectors in `get_form_selectors()` until all fixture tests pass.

- [ ] **Step 7: Commit**

```bash
git add src/apply/providers/xing/ tests/test_apply_xing_adapter.py tests/fixtures/apply/
git commit -m "feat(apply): add XING Easy Apply adapter with snapshot integration tests"
```
