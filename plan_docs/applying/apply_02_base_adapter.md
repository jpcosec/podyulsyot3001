# Apply Module — Base Adapter (ApplyAdapter ABC)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement `src/apply/smart_adapter.py` — the ABC and all shared execution logic. Provider adapters in the next plans will only implement the abstract methods.

**Architecture:** All flow control (navigate, validate, fill, upload, submit, error capture) lives in the base class. Adapters supply portal-specific knowledge only. Mirrors `src/scraper/smart_adapter.py` base class pattern.

**Tech Stack:** crawl4ai (`AsyncWebCrawler`, `BrowserConfig`, `CrawlerRunConfig`), Pydantic, asyncio. The one direct Playwright call is `page.set_input_files()` inside a `before_retrieve_html` hook — there is no browser-JS/C4A-Script equivalent for file uploads.

---

## Design Rules

1. **All run flow lives in the base class.** Adapters implement only: `source_name`, `get_form_selectors()`, `get_open_modal_script()`, `get_fill_form_script(profile)`, `get_submit_script()`, `get_success_text()`, `get_session_profile_dir()`, `_get_portal_base_url()`.
2. **C4A-Script for all portal interaction.** Never use `js_code` for interaction scripts. `c4a_script` in `CrawlerRunConfig` is the correct field. Docs: https://docs.crawl4ai.com/core/c4a-script/
3. **`_render_script(template, profile)` uses `json.dumps()` to escape values.** This handles apostrophes (O'Connor), quotes, and special characters safely before injection into C4A-Script strings.
4. **Three `arun()` calls sharing one `session_id`.** `session_id=f"apply_{source}_{job_id}"` links calls in the same browser tab. Docs: https://docs.crawl4ai.com/api/parameters/ (CrawlerRunConfig section).
5. **`before_retrieve_html` hook exposes `page: Page` (raw Playwright).** This is the ONLY place raw Playwright is used — for `page.set_input_files()` and `page.evaluate()`. Docs: https://docs.crawl4ai.com/advanced/hooks-auth/
6. **Split pure logic from I/O for testability.** `_check_selector_results(results_dict, selectors)` is pure Python (no crawl4ai) — test it directly. `_validate_selectors(session_id, selectors)` calls crawl4ai and is not tested in unit tests.
7. **Idempotency:** only `status=submitted` blocks re-execution. `dry_run`, `failed`, `portal_changed` all allow retry. Missing `apply_meta.json` means first run.
8. **`DataManager`** is at `src/core/data_manager.py`. Use `artifact_path(source, job_id, node_name="apply", stage="proposed"|"meta", filename=...)` for screenshot paths. Use `write_json_artifact(...)` and `read_json_artifact(...)` for JSON artifacts.
9. **`LogTag`** is at `src/shared/log_tags.py`. Use `LogTag.FAST`, `LogTag.OK`, `LogTag.WARN`, `LogTag.FAIL` — never write emoji strings.
10. **Error screenshot always captured.** In the `except` block, attempt a `CrawlerRunConfig(js_only=True, screenshot=True, session_id=...)` call to capture `error_state.png` before re-raising.
11. **Ingest artifact location.** The apply run reads `data/jobs/<source>/<job_id>/nodes/ingest/proposed/state.json` to get `application_url`, `job_title`, `company_name`. Use `read_json_artifact(source, job_id, node_name="ingest", stage="proposed", filename="state.json")`.

---

## File Structure

- Create: `src/apply/smart_adapter.py`
- Test: `tests/test_apply_base_adapter.py`

---

### Task 1: Pure Logic Helpers (TDD first)

**Files:**
- Create: `src/apply/smart_adapter.py` (skeleton + pure methods)
- Test: `tests/test_apply_base_adapter.py`

- [ ] **Step 1: Write the failing tests for pure helper methods**

```python
# tests/test_apply_base_adapter.py
"""Unit tests for ApplyAdapter pure logic helpers.

These tests do NOT import crawl4ai. They test only the pure methods
that can be called without browser infrastructure.
"""
from __future__ import annotations

import pytest

from src.apply.models import FormSelectors
from src.apply.smart_adapter import ApplyAdapter, PortalStructureChangedError


class _ConcreteAdapter(ApplyAdapter):
    """Minimal concrete implementation for testing the base class."""

    @property
    def source_name(self) -> str:
        return "test_portal"

    def get_form_selectors(self) -> FormSelectors:
        return FormSelectors(
            apply_button="button.apply",
            cv_upload="input.cv",
            submit_button="button.submit",
            success_indicator=".success",
            first_name="input[name='firstName']",
            email="input[name='email']",
        )

    def get_open_modal_script(self) -> str:
        return "CLICK `button.apply`\nWAIT `.modal` 5"

    def get_fill_form_script(self, profile: dict) -> str:
        return 'SET `input[name="firstName"]` "{{first_name}}"\nSET `input[name="email"]` "{{email}}"'

    def get_submit_script(self) -> str:
        return "CLICK `button.submit`"

    def get_success_text(self) -> str:
        return "Application submitted"

    def get_session_profile_dir(self):
        from pathlib import Path
        return Path("data/profiles/test_profile")

    def _get_portal_base_url(self) -> str:
        return "https://test.example.com"


class TestCheckSelectorResults:
    def test_all_present_passes(self):
        """No exception when all mandatory selectors present."""
        adapter = _ConcreteAdapter()
        selectors = adapter.get_form_selectors()
        results = {
            "apply_button": True,
            "cv_upload": True,
            "submit_button": True,
            "success_indicator": True,
            "first_name": True,
            "email": True,
        }
        adapter._check_selector_results(results, selectors)  # no exception

    def test_missing_mandatory_raises(self):
        """Missing mandatory selector raises PortalStructureChangedError."""
        adapter = _ConcreteAdapter()
        selectors = adapter.get_form_selectors()
        results = {
            "apply_button": True,
            "cv_upload": False,  # mandatory, missing
            "submit_button": True,
            "success_indicator": True,
        }
        with pytest.raises(PortalStructureChangedError) as exc_info:
            adapter._check_selector_results(results, selectors)
        assert "cv_upload" in str(exc_info.value)

    def test_missing_optional_does_not_raise(self):
        """Missing optional selector logs a warning but does not raise."""
        adapter = _ConcreteAdapter()
        selectors = adapter.get_form_selectors()
        results = {
            "apply_button": True,
            "cv_upload": True,
            "submit_button": True,
            "success_indicator": True,
            "first_name": False,  # optional, missing — should not raise
            "email": True,
        }
        adapter._check_selector_results(results, selectors)  # no exception

    def test_multiple_missing_mandatory_listed(self):
        """Error message lists all missing mandatory selectors."""
        adapter = _ConcreteAdapter()
        selectors = adapter.get_form_selectors()
        results = {
            "apply_button": False,
            "cv_upload": False,
            "submit_button": True,
            "success_indicator": False,
        }
        with pytest.raises(PortalStructureChangedError) as exc_info:
            adapter._check_selector_results(results, selectors)
        msg = str(exc_info.value)
        assert "apply_button" in msg
        assert "cv_upload" in msg
        assert "success_indicator" in msg


class TestRenderScript:
    def test_basic_interpolation(self):
        """_render_script substitutes {{placeholders}} with json.dumps values."""
        adapter = _ConcreteAdapter()
        template = 'SET `input` "{{first_name}}"'
        result = adapter._render_script(template, {"first_name": "Alice"})
        assert result == 'SET `input` "Alice"'

    def test_apostrophe_escaped(self):
        """Values with apostrophes are safely escaped via json.dumps."""
        adapter = _ConcreteAdapter()
        template = 'SET `input` "{{name}}"'
        result = adapter._render_script(template, {"name": "O'Connor"})
        # json.dumps("O'Connor") = '"O\'Connor"' — apostrophe safe in C4A-Script
        assert "O'Connor" in result or "O\\u0027Connor" not in result

    def test_unused_placeholder_preserved(self):
        """Placeholders with no matching profile key are left as-is."""
        adapter = _ConcreteAdapter()
        template = 'SET `input` "{{first_name}}" "{{unknown}}"'
        result = adapter._render_script(template, {"first_name": "Alice"})
        assert "Alice" in result
        assert "{{unknown}}" in result

    def test_none_value_becomes_empty_string(self):
        """None profile values become empty strings, not the word 'None'."""
        adapter = _ConcreteAdapter()
        template = 'SET `input` "{{phone}}"'
        result = adapter._render_script(template, {"phone": None})
        assert "None" not in result
        assert '""' in result


class TestIdempotency:
    def test_check_idempotency_no_prior_artifact(self, tmp_path):
        """No exception when no prior apply_meta.json exists."""
        from src.core.data_manager import DataManager
        adapter = _ConcreteAdapter(DataManager(tmp_path / "data" / "jobs"))
        adapter._check_idempotency("99999")  # no exception

    def test_check_idempotency_submitted_raises(self, tmp_path):
        """RuntimeError raised when prior apply was submitted."""
        from src.core.data_manager import DataManager
        manager = DataManager(tmp_path / "data" / "jobs")
        manager.write_json_artifact(
            source="test_portal",
            job_id="99999",
            node_name="apply",
            stage="meta",
            filename="apply_meta.json",
            data={"status": "submitted", "timestamp": "2026-03-30T00:00:00Z", "error": None},
        )
        adapter = _ConcreteAdapter(manager)
        with pytest.raises(RuntimeError, match="already submitted"):
            adapter._check_idempotency("99999")

    def test_check_idempotency_dry_run_allows_retry(self, tmp_path):
        """dry_run status allows re-execution (no exception)."""
        from src.core.data_manager import DataManager
        manager = DataManager(tmp_path / "data" / "jobs")
        manager.write_json_artifact(
            source="test_portal",
            job_id="99999",
            node_name="apply",
            stage="meta",
            filename="apply_meta.json",
            data={"status": "dry_run", "timestamp": "2026-03-30T00:00:00Z", "error": None},
        )
        adapter = _ConcreteAdapter(manager)
        adapter._check_idempotency("99999")  # no exception

    def test_check_idempotency_failed_allows_retry(self, tmp_path):
        """failed status allows re-execution (no exception)."""
        from src.core.data_manager import DataManager
        manager = DataManager(tmp_path / "data" / "jobs")
        manager.write_json_artifact(
            source="test_portal",
            job_id="99999",
            node_name="apply",
            stage="meta",
            filename="apply_meta.json",
            data={"status": "failed", "timestamp": "2026-03-30T00:00:00Z", "error": "network error"},
        )
        adapter = _ConcreteAdapter(manager)
        adapter._check_idempotency("99999")  # no exception
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_apply_base_adapter.py -v
```

Expected: `ImportError: cannot import name 'ApplyAdapter' from 'src.apply.smart_adapter'`

- [ ] **Step 3: Create `src/apply/smart_adapter.py` with ABC definition and pure helpers**

```python
"""Shared base class for auto-application adapters.

Adapters provide portal-specific knowledge only (selectors, C4A-Scripts, profile dir).
All flow control lives here: navigate → validate → fill → upload → submit → persist.

Spec reference: docs/superpowers/specs/2026-03-30-apply-module-design.md Sections 4-8

Crawl4AI docs:
  C4A-Script DSL:    https://docs.crawl4ai.com/core/c4a-script/
  CrawlerRunConfig:  https://docs.crawl4ai.com/api/parameters/
  Hooks:             https://docs.crawl4ai.com/advanced/hooks-auth/
  Session mgmt:      https://docs.crawl4ai.com/advanced/session-management/
"""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from src.apply.models import ApplicationRecord, ApplyMeta, FormSelectors
from src.core.data_manager import DataManager
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class PortalStructureChangedError(Exception):
    """Raised when one or more mandatory selectors are absent from the live DOM."""


class ApplyAdapter(ABC):

    def __init__(self, data_manager: DataManager | None = None) -> None:
        self.data_manager = data_manager or DataManager()

    # ── Abstract interface — adapters implement these ────────────────────────

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Portal identifier (e.g. 'xing', 'stepstone')."""

    @abstractmethod
    def get_form_selectors(self) -> FormSelectors:
        """CSS selectors for the apply form. Validated against live DOM before use."""

    @abstractmethod
    def get_open_modal_script(self) -> str:
        """C4A-Script that clicks the apply button and waits for the modal container.

        Must be idempotent: if the modal is already open, the script must not
        click again. Use IF/THEN to guard the click.

        Example:
            IF NOT `[data-testid="apply-modal"]` THEN
              CLICK `[data-testid="apply-button"]`
              WAIT `[data-testid="apply-modal"]` 5
            END
        """

    @abstractmethod
    def get_fill_form_script(self, profile: dict) -> str:
        """C4A-Script for filling text fields and dropdowns.

        Use {{placeholder}} syntax for profile values — _render_script() will
        inject them using json.dumps() before this script runs, so apostrophes
        and quotes are always safely escaped.

        File uploads are NOT included here — handled by the before_retrieve_html hook
        in the same arun() call that executes this script.

        Example:
            SET `input[name="firstName"]` "{{first_name}}"
            SET `input[name="lastName"]` "{{last_name}}"
            IF `select[name="salutation"]` THEN
              SET `select[name="salutation"]` "{{salutation}}"
            END
        """

    @abstractmethod
    def get_submit_script(self) -> str:
        """C4A-Script for the submit action (separated so dry-run can stop before it)."""

    @abstractmethod
    def get_success_text(self) -> str:
        """Text fragment expected in the confirmation page content."""

    @abstractmethod
    def get_session_profile_dir(self) -> Path:
        """Path to the persistent browser profile directory for this portal."""

    @abstractmethod
    def _get_portal_base_url(self) -> str:
        """Portal base URL — used by setup_session() for initial navigation."""

    # ── Pure helpers — tested directly without crawl4ai ─────────────────────

    def _render_script(self, template: str, profile: dict) -> str:
        """Inject profile values into a C4A-Script template.

        Each value is escaped via json.dumps() before injection to handle
        apostrophes, quotes, and other special characters safely.
        """
        result = template
        for key, value in profile.items():
            placeholder = "{{" + key + "}}"
            if placeholder in result:
                safe_value = json.dumps(str(value) if value is not None else "")
                # json.dumps wraps in quotes — strip outer quotes, keep inner escapes
                # so that the C4A-Script's own quotes remain as delimiters
                inner = safe_value[1:-1]  # strip the json.dumps outer quotes
                result = result.replace(placeholder, inner)
        return result

    def _check_selector_results(
        self, results: dict[str, bool], selectors: FormSelectors
    ) -> None:
        """Raise PortalStructureChangedError if any mandatory selector is absent.

        Called by _validate_selectors() after querying the live DOM.
        This method is pure (no crawl4ai dependency) and directly unit-testable.
        """
        mandatory = {"apply_button", "cv_upload", "submit_button", "success_indicator"}
        missing = [field for field in mandatory if not results.get(field, False)]
        if missing:
            raise PortalStructureChangedError(
                f"Mandatory selectors absent from DOM on {self.source_name}: {missing}"
            )
        optional = {
            "first_name", "last_name", "email", "phone",
            "letter_upload", "error_indicator", "cv_select_existing",
        }
        for field in optional:
            if getattr(selectors, field) is not None and not results.get(field, False):
                logger.warning(
                    "%s Optional selector '%s' absent from DOM on %s; skipping.",
                    LogTag.WARN, field, self.source_name,
                )

    def _check_idempotency(self, job_id: str) -> None:
        """Block re-execution only when prior status is 'submitted'.

        dry_run / failed / portal_changed all allow retry.
        Missing apply_meta.json means first run — always allowed.
        """
        try:
            meta = self.data_manager.read_json_artifact(
                source=self.source_name,
                job_id=job_id,
                node_name="apply",
                stage="meta",
                filename="apply_meta.json",
            )
        except (FileNotFoundError, KeyError):
            return  # First run
        if meta.get("status") == "submitted":
            raise RuntimeError(
                f"Job {job_id} ({self.source_name}) was already submitted. "
                "Delete apply_meta.json to force re-apply."
            )
        logger.warning(
            "%s Prior apply attempt found for %s with status=%s; retrying.",
            LogTag.WARN, job_id, meta.get("status"),
        )

    # ── crawl4ai helpers ─────────────────────────────────────────────────────

    def _browser_config(self, headless: bool = True) -> BrowserConfig:
        """Persistent session browser config.

        BrowserConfig docs: https://docs.crawl4ai.com/api/parameters/ (BrowserConfig section)
        Persistent sessions: https://docs.crawl4ai.com/advanced/session-management/
        """
        return BrowserConfig(
            user_data_dir=str(self.get_session_profile_dir()),
            use_persistent_context=True,
            headless=headless,
        )

    async def _validate_selectors(
        self, session_id: str, selectors: FormSelectors
    ) -> dict[str, bool]:
        """Query the live DOM for all non-None selectors and validate.

        Uses a before_retrieve_html hook with page.evaluate() to get presence map.
        Raises PortalStructureChangedError on missing mandatory selectors.

        Hook docs: https://docs.crawl4ai.com/advanced/hooks-auth/
        """
        selector_map = {
            field: getattr(selectors, field)
            for field in FormSelectors.model_fields
            if getattr(selectors, field) is not None
        }
        js_checks = ", ".join(
            f'"{field}": !!document.querySelector({json.dumps(sel)})'
            for field, sel in selector_map.items()
        )
        js_code = f"return JSON.stringify({{{js_checks}}});"

        presence: dict[str, bool] = {}

        async def _check_hook(page: Any, **kwargs: Any) -> Any:
            raw = await page.evaluate(js_code)
            presence.update(json.loads(raw))
            return page

        async with AsyncWebCrawler(config=self._browser_config()) as crawler:
            await crawler.arun(
                url="about:blank",
                config=CrawlerRunConfig(
                    js_only=True,
                    session_id=session_id,
                    hooks={"before_retrieve_html": _check_hook},
                ),
            )
        self._check_selector_results(presence, selectors)
        return presence

    def _build_file_upload_hook(
        self,
        cv_path: Path,
        letter_path: Path | None,
        selectors: FormSelectors,
    ):
        """Return a before_retrieve_html hook that uploads files via raw Playwright.

        page.set_input_files() is the one direct Playwright call in this module —
        there is no browser-JS or C4A-Script equivalent for security reasons.

        If cv_upload selector is absent but cv_select_existing is present,
        click it instead and wait 500ms for DOM stabilization.

        Hook docs: https://docs.crawl4ai.com/advanced/hooks-auth/
        """
        async def _hook(page: Any, **kwargs: Any) -> Any:
            if selectors.cv_upload:
                await page.set_input_files(selectors.cv_upload, str(cv_path))
            elif selectors.cv_select_existing:
                await page.click(selectors.cv_select_existing)
                await page.wait_for_timeout(500)  # stabilize DOM after click
            if letter_path and selectors.letter_upload:
                await page.set_input_files(selectors.letter_upload, str(letter_path))
            return page

        return _hook

    def _validate_success_text(self, result: Any) -> bool:
        """Check result content for expected success text fragment.

        Returns True if found. Logs a warning (not error) if absent —
        copy changes are common and non-fatal.
        """
        expected = self.get_success_text().lower()
        content = ""
        if result.markdown:
            content = (
                getattr(result.markdown, "raw_markdown", None)
                or str(result.markdown)
            )
        if not content and result.cleaned_html:
            content = result.cleaned_html
        found = expected in content.lower()
        if not found:
            logger.warning(
                "%s Success text '%s' not found on %s. "
                "Portal copy may have changed (non-fatal).",
                LogTag.WARN, self.get_success_text(), self.source_name,
            )
        return found

    # ── Artifact I/O ─────────────────────────────────────────────────────────

    def _read_ingest_artifact(self, job_id: str) -> dict:
        return self.data_manager.read_json_artifact(
            source=self.source_name,
            job_id=job_id,
            node_name="ingest",
            stage="proposed",
            filename="state.json",
        )

    def _write_apply_meta(self, job_id: str, meta: ApplyMeta) -> None:
        self.data_manager.write_json_artifact(
            source=self.source_name,
            job_id=job_id,
            node_name="apply",
            stage="meta",
            filename="apply_meta.json",
            data=meta.model_dump(),
        )

    def _write_application_record(self, job_id: str, record: ApplicationRecord) -> None:
        self.data_manager.write_json_artifact(
            source=self.source_name,
            job_id=job_id,
            node_name="apply",
            stage="proposed",
            filename="application_record.json",
            data=record.model_dump(),
        )

    def _save_screenshot(self, screenshot_bytes: bytes, job_id: str, filename: str) -> None:
        path = self.data_manager.artifact_path(
            source=self.source_name,
            job_id=job_id,
            node_name="apply",
            stage="proposed",
            filename=filename,
        )
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(screenshot_bytes)

    # ── Session setup (HITL) ─────────────────────────────────────────────────

    async def setup_session(self) -> None:
        """Open a visible browser for manual login. Cookies persist to profile dir.

        This is a one-time human-in-the-loop step per portal. Subsequent runs
        reuse the session headlessly. When the session expires, _validate_selectors
        will raise PortalStructureChangedError — re-run --setup-session to refresh.
        """
        self.get_session_profile_dir().mkdir(parents=True, exist_ok=True)
        async with AsyncWebCrawler(config=self._browser_config(headless=False)) as crawler:
            await crawler.arun(
                url=self._get_portal_base_url(),
                config=CrawlerRunConfig(wait_for="body"),
            )
            input(
                f"\n[{self.source_name}] Log in manually in the browser. "
                "Press Enter when done.\n"
            )
        logger.info(
            "%s Session saved to %s", LogTag.OK, self.get_session_profile_dir()
        )

    # ── Main execution flow ──────────────────────────────────────────────────

    def _build_profile(self, ingest_data: dict) -> dict:
        """Build the profile dict used for C4A-Script placeholder injection."""
        return {
            "job_title": ingest_data.get("job_title", ""),
            "company_name": ingest_data.get("company_name", ""),
            "application_url": ingest_data.get("application_url", ""),
        }

    async def run(
        self,
        job_id: str,
        cv_path: Path,
        letter_path: Path | None,
        dry_run: bool,
    ) -> ApplyMeta:
        """Execute the full apply flow. Returns ApplyMeta with final status.

        Execution flow (spec Section 5):
          1. Idempotency check — block if already submitted
          2. Read ingest artifact — get application_url, job_title, company_name
          3. Step 1: Navigate + open modal (C4A-Script, get_open_modal_script)
          4. Step 2: Validate selectors (_validate_selectors)
          5. Step 3: Fill form + upload CV in single arun() call
          6. [dry_run] Write artifacts, return status=dry_run
          7. Step 4: Submit + verify (C4A-Script, get_submit_script)
          8. Write final artifacts, return status=submitted
          On exception: capture error_state.png, write status=failed/portal_changed, re-raise
        """
        self._check_idempotency(job_id)

        ingest_data = self._read_ingest_artifact(job_id)
        application_url = ingest_data.get("application_url") or ingest_data.get("url")
        if not application_url:
            raise ValueError(f"No application_url in ingest artifact for {job_id}")

        selectors = self.get_form_selectors()
        session_id = f"apply_{self.source_name}_{job_id}"
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            async with AsyncWebCrawler(config=self._browser_config()) as crawler:
                # Step 1: Navigate to job page + open apply modal
                logger.info("%s Opening apply modal for %s/%s", LogTag.FAST, self.source_name, job_id)
                first_field = selectors.cv_upload or selectors.first_name or selectors.apply_button
                open_result = await crawler.arun(
                    url=application_url,
                    config=CrawlerRunConfig(
                        c4a_script=self.get_open_modal_script(),
                        wait_for=f"css:{first_field}",
                        session_id=session_id,
                    ),
                )
                if not open_result.success:
                    raise RuntimeError(
                        f"Failed to navigate/open modal for {job_id}: {open_result.error_message}"
                    )

                # Step 2: Validate selectors against live DOM
                await self._validate_selectors(session_id, selectors)

                # Step 3: Fill form + upload files in a single arun() call.
                # C4A-Script handles text fields; before_retrieve_html hook handles file upload.
                # They share the same browser state — no re-navigation between them.
                profile = self._build_profile(ingest_data)
                fill_script = self._render_script(
                    self.get_fill_form_script(profile), profile
                )
                fill_result = await crawler.arun(
                    url=application_url,
                    config=CrawlerRunConfig(
                        js_only=True,
                        c4a_script=fill_script,
                        hooks={
                            "before_retrieve_html": self._build_file_upload_hook(
                                cv_path, letter_path, selectors
                            )
                        },
                        screenshot=True,
                        session_id=session_id,
                    ),
                )
                if fill_result.screenshot:
                    self._save_screenshot(fill_result.screenshot, job_id, "screenshot.png")

                # Dry-run stops before submit
                if dry_run:
                    logger.info("%s Dry-run complete for %s; not submitting.", LogTag.OK, job_id)
                    record = self._build_application_record(
                        ingest_data=ingest_data,
                        job_id=job_id,
                        application_url=application_url,
                        cv_path=cv_path,
                        letter_path=letter_path,
                        profile=profile,
                        dry_run=True,
                        submitted_at=None,
                        confirmation_text=None,
                    )
                    self._write_application_record(job_id, record)
                    meta = ApplyMeta(status="dry_run", timestamp=timestamp)
                    self._write_apply_meta(job_id, meta)
                    return meta

                # Step 4: Submit and verify
                logger.info("%s Submitting application for %s/%s", LogTag.FAST, self.source_name, job_id)
                submit_result = await crawler.arun(
                    url=application_url,
                    config=CrawlerRunConfig(
                        js_only=True,
                        c4a_script=self.get_submit_script(),
                        wait_for=f"css:{selectors.success_indicator}",
                        screenshot=True,
                        session_id=session_id,
                    ),
                )
                if submit_result.screenshot:
                    self._save_screenshot(submit_result.screenshot, job_id, "screenshot_submitted.png")

                confirmation_text = None
                if submit_result.markdown:
                    raw = (
                        getattr(submit_result.markdown, "raw_markdown", None)
                        or str(submit_result.markdown)
                    )
                    confirmation_text = raw[:500]

                self._validate_success_text(submit_result)

                submitted_at = datetime.now(timezone.utc).isoformat()
                record = self._build_application_record(
                    ingest_data=ingest_data,
                    job_id=job_id,
                    application_url=application_url,
                    cv_path=cv_path,
                    letter_path=letter_path,
                    profile=profile,
                    dry_run=False,
                    submitted_at=submitted_at,
                    confirmation_text=confirmation_text,
                )
                self._write_application_record(job_id, record)
                meta = ApplyMeta(status="submitted", timestamp=submitted_at)
                self._write_apply_meta(job_id, meta)
                logger.info("%s Application submitted for %s/%s", LogTag.OK, self.source_name, job_id)
                return meta

        except Exception as exc:
            error_status = (
                "portal_changed" if isinstance(exc, PortalStructureChangedError) else "failed"
            )
            # Best-effort error screenshot — never let this shadow the original exception
            try:
                async with AsyncWebCrawler(config=self._browser_config()) as crawler:
                    err_result = await crawler.arun(
                        url="about:blank",
                        config=CrawlerRunConfig(
                            js_only=True,
                            screenshot=True,
                            session_id=session_id,
                        ),
                    )
                    if err_result.screenshot:
                        self._save_screenshot(err_result.screenshot, job_id, "error_state.png")
            except Exception:
                pass
            meta = ApplyMeta(status=error_status, timestamp=timestamp, error=str(exc))
            self._write_apply_meta(job_id, meta)
            raise

    def _build_application_record(
        self,
        *,
        ingest_data: dict,
        job_id: str,
        application_url: str,
        cv_path: Path,
        letter_path: Path | None,
        profile: dict,
        dry_run: bool,
        submitted_at: str | None,
        confirmation_text: str | None,
    ) -> ApplicationRecord:
        return ApplicationRecord(
            source=self.source_name,
            job_id=job_id,
            job_title=ingest_data.get("job_title", ""),
            company_name=ingest_data.get("company_name", ""),
            application_url=application_url,
            cv_path=str(cv_path),
            letter_path=str(letter_path) if letter_path else None,
            fields_filled=list(profile.keys()),
            dry_run=dry_run,
            submitted_at=submitted_at,
            confirmation_text=confirmation_text,
        )
```

- [ ] **Step 4: Run tests**

```bash
python -m pytest tests/test_apply_base_adapter.py -v
```

Expected: All tests PASS. (Tests only call pure methods — no crawl4ai browser needed.)

- [ ] **Step 5: Commit**

```bash
git add src/apply/smart_adapter.py tests/test_apply_base_adapter.py
git commit -m "feat(apply): add ApplyAdapter ABC and shared run logic"
```
