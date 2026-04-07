# Ariadne Session Orchestrator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extract the orchestration loop from both motor providers into a single `AriadneSession` orchestrator and connect motors to Ariadne through a `MotorProvider`/`MotorSession` protocol.

**Architecture:** `AriadneSession` in `ariadne/session.py` owns map loading, storage, navigation, and the step-dispatch loop. Motors expose `MotorProvider.open_session()` returning a `MotorSession` with two operations: `observe(selectors)` and `execute_step(step, ...)`. The CLI instantiates the right motor and hands it to `AriadneSession.run()`. The `AutomationRegistry` is deleted; that selection logic moves inline into `main.py`.

**Tech Stack:** Python 3.11, Pydantic v2, Crawl4AI, `asynccontextmanager`, `typing.Protocol`, pytest + pytest-asyncio, `ast` stdlib (guardrail test).

---

## File Map

| Status | File | Role |
|--------|------|------|
| **Create** | `src/automation/ariadne/motor_protocol.py` | `MotorSession` + `MotorProvider` protocols |
| **Create** | `src/automation/ariadne/session.py` | `AriadneSession` orchestrator |
| **Create** | `tests/unit/automation/ariadne/test_session.py` | Unit tests for AriadneSession |
| **Rewrite** | `src/automation/motors/crawl4ai/apply_engine.py` | `C4AIMotorProvider` + `C4AIMotorSession` only |
| **Modify** | `src/automation/motors/crawl4ai/replayer.py` | No change needed (API already correct) |
| **Rewrite** | `src/automation/motors/browseros/cli/backend.py` | `BrowserOSMotorProvider` + `BrowserOSMotorSession` only |
| **Modify** | `src/automation/motors/browseros/cli/replayer.py` | Add `execute_single_step()` for per-step dispatch |
| **Rewrite** | `src/automation/main.py` | Inline motor selection; delete registry import |
| **Delete** | `src/automation/registry.py` | Logic absorbed into `main.py` |
| **Move** | `tests/unit/automation/motors/crawl4ai/portals/*/test_apply.py` → `tests/unit/automation/portals/*/test_apply_map.py` | Rewrite to not import motor class |
| **Create** | `tests/unit/automation/test_boundary_guardrails.py` | AST-based import scanner |
| **Modify** | legacy debt tracker under `plan_docs/issues/` | Fix three stale open checkboxes |
| **Modify** | `src/automation/motors/crawl4ai/apply_engine.py` | Fix bare `except Exception: pass` (part of Task 3 rewrite) |

---

## Task 1: Define Motor Protocols

**Files:**
- Create: `src/automation/ariadne/motor_protocol.py`
- Create: `tests/unit/automation/ariadne/test_motor_protocol.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/automation/ariadne/test_motor_protocol.py
"""Verify that MotorSession and MotorProvider are structural (Protocol) types."""
from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

import pytest

from src.automation.ariadne.motor_protocol import MotorProvider, MotorSession


class _FakeSession:
    async def observe(self, selectors: set[str]) -> dict[str, bool]:
        return {s: False for s in selectors}

    async def execute_step(self, step, context, cv_path, letter_path, is_first, url):
        pass


class _FakeProvider:
    @asynccontextmanager
    async def open_session(self, session_id: str) -> AsyncIterator[_FakeSession]:
        yield _FakeSession()


def test_fake_session_satisfies_protocol():
    s: MotorSession = _FakeSession()  # type: ignore[assignment]
    assert callable(s.observe)
    assert callable(s.execute_step)


def test_fake_provider_satisfies_protocol():
    p: MotorProvider = _FakeProvider()  # type: ignore[assignment]
    assert callable(p.open_session)


@pytest.mark.asyncio
async def test_provider_yields_session():
    provider = _FakeProvider()
    async with provider.open_session("test-id") as session:
        result = await session.observe({"div.foo"})
        assert result == {"div.foo": False}
```

- [ ] **Step 2: Run the test — expect ImportError (module doesn't exist yet)**

```bash
python -m pytest tests/unit/automation/ariadne/test_motor_protocol.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.automation.ariadne.motor_protocol'`

- [ ] **Step 3: Create `src/automation/ariadne/motor_protocol.py`**

```python
"""Motor Protocol — Contracts between Ariadne and execution motors."""
from __future__ import annotations

from pathlib import Path
from typing import Any, AsyncContextManager, Protocol, runtime_checkable

from src.automation.ariadne.models import AriadneStep


@runtime_checkable
class MotorSession(Protocol):
    """Single-session interface: observe DOM state and execute one step."""

    async def observe(self, selectors: set[str]) -> dict[str, bool]:
        """Check which CSS selectors are present in the live page.

        Args:
            selectors: CSS selectors to probe.

        Returns:
            Mapping of selector → presence boolean.
        """
        ...

    async def execute_step(
        self,
        step: AriadneStep,
        context: dict[str, Any],
        cv_path: Path,
        letter_path: Path | None,
        is_first: bool,
        url: str | None,
    ) -> None:
        """Execute a single AriadneStep on the live page."""
        ...


@runtime_checkable
class MotorProvider(Protocol):
    """Factory for opening motor sessions."""

    def open_session(self, session_id: str) -> AsyncContextManager[MotorSession]:
        """Open a browser session scoped to one apply run.

        Args:
            session_id: Unique identifier for this session (used for browser tab/session reuse).

        Returns:
            Async context manager yielding a MotorSession.
        """
        ...
```

- [ ] **Step 4: Run the test — expect PASS**

```bash
python -m pytest tests/unit/automation/ariadne/test_motor_protocol.py -v
```

Expected: 3 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/automation/ariadne/motor_protocol.py tests/unit/automation/ariadne/test_motor_protocol.py
git commit -m "feat(ariadne): add MotorSession and MotorProvider protocols"
```

---

## Task 2: Implement AriadneSession

**Files:**
- Create: `src/automation/ariadne/session.py`
- Create: `tests/unit/automation/ariadne/test_session.py`

- [ ] **Step 1: Write the failing tests**

```python
# tests/unit/automation/ariadne/test_session.py
"""Unit tests for AriadneSession orchestrator."""
from __future__ import annotations

import json
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.automation.ariadne.models import (
    AriadneObserve,
    AriadnePath,
    AriadnePortalMap,
    AriadneStep,
    AriadneTask,
    AriadneState,
    ApplyMeta,
)
from src.automation.ariadne.session import AriadneSession


def _minimal_map() -> AriadnePortalMap:
    """Minimal valid portal map for testing (1 state, 1 task, 1 path with 1 step)."""
    step = AriadneStep(
        step_index=1,
        name="fill_form",
        description="Fill the form",
        observe=AriadneObserve(required_elements=[]),
        actions=[],
        dry_run_stop=False,
    )
    return AriadnePortalMap(
        portal_name="test_portal",
        base_url="https://example.com",
        states={
            "success": AriadneState(
                id="success",
                description="Application sent",
                presence_predicate=AriadneObserve(required_elements=[]),
            )
        },
        tasks={
            "submit_easy_apply": AriadneTask(
                id="submit_easy_apply",
                goal="Submit",
                entry_state="job_details",
                success_states=["success"],
                failure_states=[],
            )
        },
        paths={
            "standard_easy_apply": AriadnePath(
                id="standard_easy_apply",
                task_id="submit_easy_apply",
                steps=[step],
            )
        },
    )


class _FakeSession:
    def __init__(self):
        self.observe = AsyncMock(return_value={})
        self.execute_step = AsyncMock()


class _FakeProvider:
    def __init__(self, session: _FakeSession):
        self._session = session

    @asynccontextmanager
    async def open_session(self, session_id: str) -> AsyncIterator[_FakeSession]:
        yield self._session


def _make_session(map_: AriadnePortalMap) -> tuple[AriadneSession, MagicMock]:
    storage = MagicMock()
    storage.check_already_submitted.return_value = False
    storage.get_job_state.return_value = {
        "job_title": "Dev",
        "company_name": "Acme",
        "application_url": "https://example.com/apply",
    }
    storage.write_apply_meta = MagicMock()

    sess = AriadneSession.__new__(AriadneSession)
    sess.portal_name = "test_portal"
    sess.storage = storage
    sess._map = map_
    return sess, storage


@pytest.mark.asyncio
async def test_already_submitted_raises():
    sess, storage = _make_session(_minimal_map())
    storage.check_already_submitted.return_value = True
    motor = _FakeProvider(_FakeSession())

    with pytest.raises(RuntimeError, match="already submitted"):
        await sess.run(motor, job_id="job1", cv_path=Path("cv.pdf"))


@pytest.mark.asyncio
async def test_invalid_path_id_raises():
    sess, _ = _make_session(_minimal_map())
    motor = _FakeProvider(_FakeSession())

    with pytest.raises(ValueError, match="Path 'missing' not found"):
        await sess.run(motor, job_id="job1", cv_path=Path("cv.pdf"), path_id="missing")


@pytest.mark.asyncio
async def test_run_calls_execute_step_once():
    sess, storage = _make_session(_minimal_map())
    fake_session = _FakeSession()
    motor = _FakeProvider(fake_session)

    meta = await sess.run(motor, job_id="job1", cv_path=Path("cv.pdf"))

    assert meta.status == "submitted"
    fake_session.execute_step.assert_called_once()
    storage.write_apply_meta.assert_called_once()


@pytest.mark.asyncio
async def test_dry_run_stops_before_dry_run_stop_step():
    map_ = _minimal_map()
    map_.paths["standard_easy_apply"].steps[0].dry_run_stop = True
    sess, _ = _make_session(map_)
    fake_session = _FakeSession()
    motor = _FakeProvider(fake_session)

    meta = await sess.run(motor, job_id="job1", cv_path=Path("cv.pdf"), dry_run=True)

    assert meta.status == "dry_run"
    fake_session.execute_step.assert_not_called()


@pytest.mark.asyncio
async def test_meta_written_on_failure():
    sess, storage = _make_session(_minimal_map())
    fake_session = _FakeSession()
    fake_session.execute_step.side_effect = RuntimeError("boom")
    motor = _FakeProvider(fake_session)

    with pytest.raises(RuntimeError, match="boom"):
        await sess.run(motor, job_id="job1", cv_path=Path("cv.pdf"))

    written = storage.write_apply_meta.call_args[0]
    assert written[2]["status"] == "failed"
    assert "boom" in written[2]["error"]
```

- [ ] **Step 2: Run the tests — expect ImportError**

```bash
python -m pytest tests/unit/automation/ariadne/test_session.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.automation.ariadne.session'`

- [ ] **Step 3: Create `src/automation/ariadne/session.py`**

```python
"""Ariadne Session — Orchestrator for portal apply flows."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.automation.ariadne.exceptions import TerminalStateReached
from src.automation.ariadne.models import ApplyMeta, AriadnePortalMap
from src.automation.ariadne.motor_protocol import MotorProvider
from src.automation.ariadne.navigator import AriadneNavigator
from src.automation.storage import AutomationStorage
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class AriadneSession:
    """Owns the apply orchestration loop: map loading, navigation, step dispatch.

    The motor is injected at run-time so the same session can be driven by any
    motor (Crawl4AI, BrowserOS, future Vision motor) without changes here.
    """

    def __init__(
        self,
        portal_name: str,
        storage: AutomationStorage | None = None,
    ) -> None:
        self.portal_name = portal_name
        self.storage = storage or AutomationStorage()
        self._map: AriadnePortalMap | None = None

    @property
    def portal_map(self) -> AriadnePortalMap:
        """Load the portal map lazily from `src/automation/portals/<name>/maps/easy_apply.json`."""
        if not self._map:
            map_path = (
                Path(__file__).parent.parent
                / "portals" / self.portal_name / "maps" / "easy_apply.json"
            )
            if not map_path.exists():
                raise FileNotFoundError(
                    f"Ariadne Map not found for '{self.portal_name}' at {map_path}"
                )
            with open(map_path) as f:
                self._map = AriadnePortalMap.model_validate(json.load(f))
        return self._map

    async def run(
        self,
        motor: MotorProvider,
        *,
        job_id: str,
        cv_path: Path,
        letter_path: Path | None = None,
        dry_run: bool = False,
        path_id: str = "standard_easy_apply",
    ) -> ApplyMeta:
        """Run an apply flow using the supplied motor.

        Args:
            motor: A MotorProvider that opens browser sessions.
            job_id: The job to apply to.
            cv_path: Local path to the CV file.
            letter_path: Optional cover letter.
            dry_run: If True, stop at the first step marked dry_run_stop.
            path_id: Which path in the portal map to follow.

        Returns:
            ApplyMeta with final status.

        Raises:
            RuntimeError: If the job was already submitted.
            ValueError: If the path_id does not exist in the map.
            TerminalStateReached: If the navigator detects a failure state.
        """
        if self.storage.check_already_submitted(self.portal_name, job_id):
            raise RuntimeError(
                f"Job {job_id} ({self.portal_name}) was already submitted."
            )

        portal_map = self.portal_map
        path = portal_map.paths.get(path_id)
        if not path:
            raise ValueError(
                f"Path '{path_id}' not found in map for {self.portal_name}"
            )

        ingest_data = self.storage.get_job_state(self.portal_name, job_id)
        application_url = ingest_data.get("application_url") or ingest_data.get("url")
        context = self._build_context(ingest_data, cv_path, letter_path, application_url)
        all_selectors = self._collect_selectors(portal_map)
        navigator = AriadneNavigator(portal_map)
        session_id = f"apply_{self.portal_name}_{job_id}"
        timestamp = datetime.now(timezone.utc).isoformat()

        try:
            async with motor.open_session(session_id) as ms:
                step_index = 1
                while step_index <= len(path.steps):
                    step = path.steps[step_index - 1]

                    if dry_run and step.dry_run_stop:
                        logger.info("%s Dry-run stop at step '%s'", LogTag.OK, step.name)
                        break

                    obs = await ms.observe(all_selectors)
                    current_state = navigator.find_current_state(obs)

                    finished, mission_status = navigator.check_mission_status(
                        path.task_id, current_state or ""
                    )
                    if finished:
                        if mission_status == "terminal_failure":
                            raise TerminalStateReached(
                                f"Reached failure state: {current_state}"
                            )
                        break

                    logger.info(
                        "%s Step %s/%s: %s",
                        LogTag.FAST,
                        step_index,
                        len(path.steps),
                        step.name,
                    )
                    await ms.execute_step(
                        step=step,
                        context=context,
                        cv_path=cv_path,
                        letter_path=letter_path,
                        is_first=(step_index == 1),
                        url=application_url,
                    )

                    obs_after = await ms.observe(all_selectors)
                    next_state = navigator.find_current_state(obs_after)
                    step_index = navigator.get_next_step_index(path, step_index, next_state)

            final_status = "dry_run" if dry_run else "submitted"
            meta = ApplyMeta(status=final_status, timestamp=timestamp)
            self.storage.write_apply_meta(self.portal_name, job_id, meta.model_dump())
            logger.info("%s Apply finished: %s", LogTag.OK, final_status)
            return meta

        except Exception as exc:
            logger.error("%s Apply failed: %s", LogTag.FAIL, exc)
            error_meta = ApplyMeta(status="failed", timestamp=timestamp, error=str(exc))
            self.storage.write_apply_meta(self.portal_name, job_id, error_meta.model_dump())
            raise

    def _collect_selectors(self, portal_map: AriadnePortalMap) -> set[str]:
        """Collect all CSS selectors from state presence predicates."""
        selectors: set[str] = set()
        for state in portal_map.states.values():
            for target in state.presence_predicate.required_elements:
                if target.css:
                    selectors.add(target.css)
        return selectors

    def _build_context(
        self,
        ingest_data: dict[str, Any],
        cv_path: Path,
        letter_path: Path | None,
        application_url: str | None,
    ) -> dict[str, Any]:
        return {
            "profile": {
                "first_name": "Juan Pablo",
                "last_name": "Ruiz",
                "email": "jp@example.com",
                "phone": "+49123456789",
            },
            "job": {
                "job_title": ingest_data.get("job_title", ""),
                "company_name": ingest_data.get("company_name", ""),
                "application_url": application_url or "",
            },
            "cv_path": str(cv_path),
            "letter_path": str(letter_path) if letter_path else None,
        }
```

- [ ] **Step 4: Run the tests — expect PASS**

```bash
python -m pytest tests/unit/automation/ariadne/test_session.py -v
```

Expected: 5 PASSED

- [ ] **Step 5: Commit**

```bash
git add src/automation/ariadne/session.py tests/unit/automation/ariadne/test_session.py
git commit -m "feat(ariadne): add AriadneSession orchestrator"
```

---

## Task 3: Refactor Crawl4AI into C4AIMotorProvider + C4AIMotorSession

**Files:**
- Rewrite: `src/automation/motors/crawl4ai/apply_engine.py`
- Create: `tests/unit/automation/motors/crawl4ai/test_motor_provider.py`

The current `Crawl4AIApplyProvider` owns orchestration (map loading, `run()` loop, navigator). All of that moves to `AriadneSession`. What stays is browser management and step execution.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/automation/motors/crawl4ai/test_motor_provider.py
"""Unit tests for C4AIMotorProvider / C4AIMotorSession."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.automation.motors.crawl4ai.apply_engine import C4AIMotorProvider


def test_provider_is_instantiable():
    provider = C4AIMotorProvider()
    assert hasattr(provider, "open_session")


def test_provider_has_no_portal_map():
    provider = C4AIMotorProvider()
    assert not hasattr(provider, "portal_map")
    assert not hasattr(provider, "source_name")


@pytest.mark.asyncio
async def test_open_session_yields_session_with_correct_interface():
    provider = C4AIMotorProvider()
    fake_crawler_ctx = MagicMock()
    fake_crawler_ctx.__aenter__ = AsyncMock(return_value=MagicMock())
    fake_crawler_ctx.__aexit__ = AsyncMock(return_value=False)

    with patch("src.automation.motors.crawl4ai.apply_engine.AsyncWebCrawler", return_value=fake_crawler_ctx):
        async with provider.open_session("test-session") as session:
            assert hasattr(session, "observe")
            assert hasattr(session, "execute_step")
```

- [ ] **Step 2: Run to see failure**

```bash
python -m pytest tests/unit/automation/motors/crawl4ai/test_motor_provider.py -v
```

Expected: `ImportError` (class doesn't exist yet)

- [ ] **Step 3: Rewrite `src/automation/motors/crawl4ai/apply_engine.py`**

```python
"""Crawl4AI Motor Provider — Browser adapter for Ariadne.

Implements MotorProvider / MotorSession for the Crawl4AI backend.
Orchestration (map loading, navigation, run loop) is owned by AriadneSession.
"""
from __future__ import annotations

import json
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig

from src.automation.ariadne.models import AriadneStep
from src.automation.motors.crawl4ai.replayer import C4AIReplayer
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class C4AIMotorSession:
    """Single-session adapter: observe DOM and execute steps via Crawl4AI."""

    def __init__(
        self,
        crawler: AsyncWebCrawler,
        session_id: str,
        replayer: C4AIReplayer,
    ) -> None:
        self._crawler = crawler
        self._session_id = session_id
        self._replayer = replayer

    async def observe(self, selectors: set[str]) -> dict[str, bool]:
        """Check which CSS selectors are present in the live page."""
        if not selectors:
            return {}

        js_checks = ", ".join(
            f'"{sel}": !!document.querySelector({json.dumps(sel)})'
            for sel in selectors
        )
        js_code = f"return {{{js_checks}}};"
        results: dict[str, bool] = {}

        async def _check_hook(page: Any, **kwargs: Any) -> Any:
            nonlocal results
            results = await page.evaluate(js_code)
            return page

        await self._crawler.arun(
            url="about:blank",
            config=CrawlerRunConfig(
                js_only=True,
                session_id=self._session_id,
                hooks={"before_retrieve_html": _check_hook},
            ),
        )
        return results

    async def execute_step(
        self,
        step: AriadneStep,
        context: dict[str, Any],
        cv_path: Path,
        letter_path: Path | None,
        is_first: bool,
        url: str | None,
    ) -> None:
        """Execute a single AriadneStep via C4AIReplayer."""
        await self._replayer.execute_step(
            step=step,
            crawler=self._crawler,
            session_id=self._session_id,
            context=context,
            cv_path=cv_path,
            letter_path=letter_path,
            is_first_step=is_first,
            application_url=url,
        )


class C4AIMotorProvider:
    """Opens Crawl4AI browser sessions for AriadneSession.

    Usage::

        motor = C4AIMotorProvider()
        session = AriadneSession("linkedin")
        meta = await session.run(motor, job_id="123", cv_path=Path("cv.pdf"))
    """

    @asynccontextmanager
    async def open_session(self, session_id: str) -> AsyncIterator[C4AIMotorSession]:
        """Open a Crawl4AI browser session.

        Args:
            session_id: Unique session name (used for tab/CDP reuse).

        Yields:
            C4AIMotorSession ready to observe and execute steps.
        """
        async with AsyncWebCrawler(config=self._browser_config()) as crawler:
            yield C4AIMotorSession(crawler, session_id, C4AIReplayer())

    def _browser_config(self, headless: bool = True) -> BrowserConfig:
        from src.automation.motors.browseros.injection import get_browseros_injected_config
        return get_browseros_injected_config(headless=headless)
```

- [ ] **Step 4: Run the tests — expect PASS**

```bash
python -m pytest tests/unit/automation/motors/crawl4ai/test_motor_provider.py -v
```

Expected: 3 PASSED

- [ ] **Step 5: Run all automation tests to check for regressions**

```bash
python -m pytest tests/unit/automation/ -q --ignore=tests/unit/automation/motors/crawl4ai/portals
```

Expected: all pass (the portal sub-tests are ignored here; they'll be moved in Task 6)

- [ ] **Step 6: Commit**

```bash
git add src/automation/motors/crawl4ai/apply_engine.py tests/unit/automation/motors/crawl4ai/test_motor_provider.py
git commit -m "refactor(crawl4ai): strip orchestration; expose C4AIMotorProvider + C4AIMotorSession"
```

---

## Task 4: Refactor BrowserOS into BrowserOSMotorProvider + BrowserOSMotorSession

**Files:**
- Modify: `src/automation/motors/browseros/cli/replayer.py` (add `execute_single_step`)
- Rewrite: `src/automation/motors/browseros/cli/backend.py`
- Create: `tests/unit/automation/motors/browseros/cli/test_motor_provider.py`

The `BrowserOSReplayer.run()` currently iterates all steps. We need a single-step method so `BrowserOSMotorSession.execute_step` can call it one step at a time.

- [ ] **Step 1: Write the failing test**

```python
# tests/unit/automation/motors/browseros/cli/test_motor_provider.py
"""Unit tests for BrowserOSMotorProvider / BrowserOSMotorSession."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.automation.motors.browseros.cli.backend import BrowserOSMotorProvider
from src.automation.motors.browseros.cli.replayer import BrowserOSReplayer


def _fake_client():
    client = MagicMock()
    client.new_hidden_page.return_value = 42
    client.take_snapshot.return_value = []
    client.search_dom.return_value = []
    return client


def test_provider_is_instantiable():
    client = _fake_client()
    provider = BrowserOSMotorProvider(client=client)
    assert hasattr(provider, "open_session")


def test_provider_has_no_portal_map():
    client = _fake_client()
    provider = BrowserOSMotorProvider(client=client)
    assert not hasattr(provider, "portal_map")
    assert not hasattr(provider, "source_name")


@pytest.mark.asyncio
async def test_open_session_opens_and_closes_page():
    client = _fake_client()
    provider = BrowserOSMotorProvider(client=client)

    async with provider.open_session("test-session") as session:
        assert hasattr(session, "observe")
        assert hasattr(session, "execute_step")

    client.new_hidden_page.assert_called_once()
    client.close_page.assert_called_once_with(42)


@pytest.mark.asyncio
async def test_observe_checks_selectors_via_search_dom():
    client = _fake_client()
    client.search_dom.return_value = [1]  # found
    provider = BrowserOSMotorProvider(client=client)

    async with provider.open_session("sess") as session:
        result = await session.observe({"div.apply-btn"})

    assert result == {"div.apply-btn": True}


def test_replayer_has_execute_single_step():
    assert hasattr(BrowserOSReplayer, "execute_single_step")
```

- [ ] **Step 2: Run to see failure**

```bash
python -m pytest tests/unit/automation/motors/browseros/cli/test_motor_provider.py -v
```

Expected: `ImportError` (BrowserOSMotorProvider doesn't exist) or `AttributeError` (execute_single_step missing)

- [ ] **Step 3: Add `execute_single_step` to `BrowserOSReplayer`**

Add this method to `BrowserOSReplayer` in `src/automation/motors/browseros/cli/replayer.py` after the existing `run()` method:

```python
    def execute_single_step(
        self,
        *,
        page_id: int,
        step: "AriadneStep",
        context: dict[str, Any],
        cv_path: Path,
        fields_filled: list[str] | None = None,
    ) -> None:
        """Execute a single AriadneStep on the given page.

        Args:
            page_id: BrowserOS page to operate on.
            step: The step to execute.
            context: Template context for interpolation.
            cv_path: Local CV path for upload actions.
            fields_filled: Optional accumulator list for tracking touched fields.
        """
        if fields_filled is None:
            fields_filled = []
        logger.info("%s Executing Step %s: %s", LogTag.OK, step.step_index, step.name)
        snapshot = self.client.take_snapshot(page_id)
        self._assert_observation(snapshot, step.observe, step.name, page_id)
        if step.human_required:
            self._request_human_confirmation(step.description)
        for action in step.actions:
            self._execute_action(
                page_id=page_id,
                action=action,
                context=context,
                cv_path=cv_path,
                fields_filled=fields_filled,
            )
```

- [ ] **Step 4: Rewrite `src/automation/motors/browseros/cli/backend.py`**

```python
"""BrowserOS Motor Provider — Browser adapter for Ariadne.

Implements MotorProvider / MotorSession for the BrowserOS backend.
Orchestration (map loading, navigation, run loop) is owned by AriadneSession.
"""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from src.automation.ariadne.models import AriadneStep
from src.automation.motors.browseros.cli.client import BrowserOSClient
from src.automation.motors.browseros.cli.replayer import BrowserOSReplayer
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class BrowserOSMotorSession:
    """Single-session adapter: observe DOM and execute steps via BrowserOS."""

    def __init__(
        self,
        client: BrowserOSClient,
        page_id: int,
        replayer: BrowserOSReplayer,
    ) -> None:
        self._client = client
        self._page_id = page_id
        self._replayer = replayer

    async def observe(self, selectors: set[str]) -> dict[str, bool]:
        """Check which CSS selectors are present via BrowserOS DOM search."""
        results: dict[str, bool] = {}
        for sel in selectors:
            matches = self._client.search_dom(self._page_id, sel)
            results[sel] = bool(matches)
        return results

    async def execute_step(
        self,
        step: AriadneStep,
        context: dict[str, Any],
        cv_path: Path,
        letter_path: Path | None,
        is_first: bool,
        url: str | None,
    ) -> None:
        """Navigate on first step, then execute the AriadneStep."""
        if is_first and url:
            self._client.navigate(url, self._page_id)
        self._replayer.execute_single_step(
            page_id=self._page_id,
            step=step,
            context=context,
            cv_path=cv_path,
        )


class BrowserOSMotorProvider:
    """Opens BrowserOS browser sessions for AriadneSession.

    Usage::

        motor = BrowserOSMotorProvider()
        session = AriadneSession("linkedin")
        meta = await session.run(motor, job_id="123", cv_path=Path("cv.pdf"))
    """

    def __init__(self, client: BrowserOSClient | None = None) -> None:
        self._client = client or BrowserOSClient()

    @asynccontextmanager
    async def open_session(self, session_id: str) -> AsyncIterator[BrowserOSMotorSession]:
        """Open a hidden BrowserOS page for the duration of one apply run.

        Args:
            session_id: Unused by BrowserOS (page_id is used instead), kept for protocol compat.

        Yields:
            BrowserOSMotorSession ready to observe and execute steps.
        """
        page_id = self._client.new_hidden_page()
        try:
            yield BrowserOSMotorSession(
                self._client, page_id, BrowserOSReplayer(self._client)
            )
        finally:
            try:
                self._client.close_page(page_id)
            except Exception:
                logger.warning(
                    "%s Failed to close BrowserOS page %s", LogTag.WARN, page_id
                )


def build_browseros_providers(
    portals: list[str] | None = None,
) -> dict[str, "BrowserOSMotorProvider"]:
    """Build BrowserOS motor providers for a list of portals.

    Each portal gets its own provider instance (separate browser context).
    """
    portals = portals or ["linkedin", "xing", "stepstone"]
    return {portal: BrowserOSMotorProvider() for portal in portals}
```

- [ ] **Step 5: Run the tests — expect PASS**

```bash
python -m pytest tests/unit/automation/motors/browseros/cli/test_motor_provider.py -v
```

Expected: 5 PASSED

- [ ] **Step 6: Commit**

```bash
git add src/automation/motors/browseros/cli/replayer.py \
        src/automation/motors/browseros/cli/backend.py \
        tests/unit/automation/motors/browseros/cli/test_motor_provider.py
git commit -m "refactor(browseros): strip orchestration; expose BrowserOSMotorProvider + BrowserOSMotorSession"
```

---

## Task 5: Collapse `registry.py` into `main.py` and Delete the File

**Files:**
- Rewrite: `src/automation/main.py` (inline motor selection)
- Delete: `src/automation/registry.py`
- Modify: `tests/unit/automation/test_main.py` (if exists; verify import)

- [ ] **Step 1: Verify no test directly imports `AutomationRegistry`**

```bash
grep -r "AutomationRegistry\|from src.automation.registry" tests/ --include="*.py" -l
```

Expected: no files (or only `test_registry.py` which can be deleted if it exists)

If `tests/unit/automation/test_registry.py` exists, delete it — that test file is testing the wrong abstraction.

- [ ] **Step 2: Rewrite `src/automation/main.py`**

Replace the `_run_apply` function (lines ~93-130) with the version below. The `_run_scrape` function's `AutomationRegistry.get_scrape_provider` call becomes an inline import chain. Keep all argument parsing unchanged.

Replace:
```python
async def _run_apply(args) -> None:
    """Run an apply cycle using the AutomationRegistry."""
    from src.shared.log_tags import LogTag
    from src.automation.registry import AutomationRegistry
    ...
    adapter = AutomationRegistry.get_apply_provider(...)
    ...
    meta = await adapter.run(...)
```

With:
```python
async def _run_apply(args) -> None:
    """Run an apply cycle using AriadneSession + the selected motor."""
    from src.shared.log_tags import LogTag
    from src.automation.ariadne.session import AriadneSession

    _setup_logging(f"apply_{args.source}")
    logger = logging.getLogger(__name__)

    if args.profile_json:
        profile_data = json.loads(Path(args.profile_json).read_text(encoding="utf-8"))
    else:
        profile_data = None

    storage = AutomationStorage()
    session = AriadneSession(portal_name=args.source, storage=storage)

    if args.backend == "browseros":
        from src.automation.motors.browseros.cli.backend import BrowserOSMotorProvider
        motor = BrowserOSMotorProvider()
    elif args.backend == "crawl4ai":
        from src.automation.motors.crawl4ai.apply_engine import C4AIMotorProvider
        motor = C4AIMotorProvider()
    else:
        logger.error("%s Unsupported backend: %s", LogTag.FAIL, args.backend)
        sys.exit(1)

    if args.setup_session and args.job_id:
        logger.error("%s --setup-session and --job-id are mutually exclusive.", LogTag.FAIL)
        sys.exit(1)

    if args.setup_session:
        # BrowserOS only: open visible page for manual login
        from src.automation.motors.browseros.cli.client import BrowserOSClient
        client = BrowserOSClient()
        base_url = session.portal_map.base_url
        page_id = client.new_page()
        client.navigate(base_url, page_id)
        client.show_page(page_id)
        input(f"\n[{args.source}] Log in in BrowserOS, then press Enter.\n")
        logger.info("%s BrowserOS session ready for %s", LogTag.OK, args.source)
        return

    if not args.job_id or not args.cv_path:
        logger.error("%s --job-id and --cv are required in apply mode.", LogTag.FAIL)
        sys.exit(1)

    meta = await session.run(
        motor,
        job_id=args.job_id,
        cv_path=Path(args.cv_path),
        letter_path=Path(args.letter_path) if args.letter_path else None,
        dry_run=args.dry_run,
    )
    logger.info("%s Apply completed: status=%s", LogTag.OK, meta.status)
```

Replace the `_run_scrape` function's registry call:
```python
async def _run_scrape(args) -> None:
    """Run a full scrape cycle."""
    from src.shared.log_tags import LogTag

    _setup_logging(f"scrape_{args.source}")
    logger = logging.getLogger(__name__)
    storage = AutomationStorage()

    if args.source == "stepstone":
        from src.automation.motors.crawl4ai.portals.stepstone.scrape import StepStoneAdapter
        adapter = StepStoneAdapter(storage.data_manager)
    elif args.source == "xing":
        from src.automation.motors.crawl4ai.portals.xing.scrape import XingAdapter
        adapter = XingAdapter(storage.data_manager)
    elif args.source == "tuberlin":
        from src.automation.motors.crawl4ai.portals.tuberlin.scrape import TUBerlinAdapter
        adapter = TUBerlinAdapter(storage.data_manager)
    else:
        logger.error("%s Unsupported scrape source: %s", LogTag.FAIL, args.source)
        sys.exit(1)

    for param, value in {
        "categories": args.categories,
        "city": args.city,
        "job_query": args.job_query,
        "max_days": args.max_days,
    }.items():
        if value is not None and param not in adapter.supported_params:
            logger.warning(
                "%s Provider '%s' does not support '%s'; ignoring.",
                LogTag.WARN, args.source, param,
            )

    already_scraped: list[str] = []
    if not args.overwrite:
        source_root = storage.data_manager.source_root(args.source)
        if source_root.exists():
            already_scraped = sorted(
                p.name for p in source_root.iterdir()
                if p.is_dir() and storage.data_manager.has_ingested_job(args.source, p.name)
            )

    ingested = await adapter.run(already_scraped=already_scraped, **vars(args))
    logger.info("%s Ingested %s jobs for source '%s'", LogTag.OK, len(ingested), args.source)
```

- [ ] **Step 3: Delete `src/automation/registry.py`**

```bash
git rm src/automation/registry.py
```

- [ ] **Step 4: Run the full test suite to verify no breakage**

```bash
python -m pytest tests/unit/automation/ -q --ignore=tests/unit/automation/motors/crawl4ai/portals
```

Expected: all pass

- [ ] **Step 5: Commit**

```bash
git add src/automation/main.py
git commit -m "refactor(cli): inline motor selection into main.py; delete registry.py"
```

---

## Task 6: Move Portal Map Tests Out of `motors/`

**Files:**
- Delete: `tests/unit/automation/motors/crawl4ai/portals/linkedin/test_apply.py`
- Delete: `tests/unit/automation/motors/crawl4ai/portals/xing/test_apply.py`
- Delete: `tests/unit/automation/motors/crawl4ai/portals/stepstone/test_apply.py`
- Create: `tests/unit/automation/portals/linkedin/test_apply_map.py`
- Create: `tests/unit/automation/portals/xing/test_apply_map.py`
- Create: `tests/unit/automation/portals/stepstone/test_apply_map.py`

These tests verify the JSON portal map content. They must import from `ariadne.models`, not from any motor class.

- [ ] **Step 1: Create `tests/unit/automation/portals/__init__.py` and subdirs**

```bash
mkdir -p tests/unit/automation/portals/linkedin
mkdir -p tests/unit/automation/portals/xing
mkdir -p tests/unit/automation/portals/stepstone
touch tests/unit/automation/portals/__init__.py
touch tests/unit/automation/portals/linkedin/__init__.py
touch tests/unit/automation/portals/xing/__init__.py
touch tests/unit/automation/portals/stepstone/__init__.py
```

- [ ] **Step 2: Create `tests/unit/automation/portals/linkedin/test_apply_map.py`**

```python
"""Validate the LinkedIn easy_apply Ariadne map."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.automation.ariadne.models import AriadnePortalMap

_MAP_PATH = Path("src/automation/portals/linkedin/maps/easy_apply.json")


@pytest.fixture(scope="module")
def portal_map() -> AriadnePortalMap:
    return AriadnePortalMap.model_validate(json.loads(_MAP_PATH.read_text()))


def test_portal_name(portal_map):
    assert portal_map.portal_name == "linkedin"


def test_required_states_present(portal_map):
    assert "job_details" in portal_map.states


def test_standard_path_present(portal_map):
    assert "standard_easy_apply" in portal_map.paths


def test_success_criteria(portal_map):
    task = portal_map.tasks["submit_easy_apply"]
    assert task.success_criteria.get("text_match") == "application"
```

- [ ] **Step 3: Create `tests/unit/automation/portals/xing/test_apply_map.py`**

```python
"""Validate the XING easy_apply Ariadne map."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.automation.ariadne.models import AriadnePortalMap

_MAP_PATH = Path("src/automation/portals/xing/maps/easy_apply.json")


@pytest.fixture(scope="module")
def portal_map() -> AriadnePortalMap:
    return AriadnePortalMap.model_validate(json.loads(_MAP_PATH.read_text()))


def test_portal_name(portal_map):
    assert portal_map.portal_name == "xing"


def test_required_states_present(portal_map):
    assert "job_details" in portal_map.states


def test_standard_path_present(portal_map):
    assert "standard_easy_apply" in portal_map.paths


def test_success_criteria(portal_map):
    task = portal_map.tasks["submit_easy_apply"]
    assert task.success_criteria.get("text_match") == "Bewerbung"
```

- [ ] **Step 4: Create `tests/unit/automation/portals/stepstone/test_apply_map.py`**

```python
"""Validate the StepStone easy_apply Ariadne map."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.automation.ariadne.models import AriadnePortalMap

_MAP_PATH = Path("src/automation/portals/stepstone/maps/easy_apply.json")


@pytest.fixture(scope="module")
def portal_map() -> AriadnePortalMap:
    return AriadnePortalMap.model_validate(json.loads(_MAP_PATH.read_text()))


def test_portal_name(portal_map):
    assert portal_map.portal_name == "stepstone"


def test_required_states_present(portal_map):
    assert "job_details" in portal_map.states


def test_standard_path_present(portal_map):
    assert "standard_easy_apply" in portal_map.paths


def test_success_criteria(portal_map):
    task = portal_map.tasks["submit_easy_apply"]
    assert task.success_criteria.get("text_match") == "Bewerbung"
```

- [ ] **Step 5: Run new tests**

```bash
python -m pytest tests/unit/automation/portals/ -v
```

Expected: 12 PASSED (4 per portal)

- [ ] **Step 6: Delete old motor-coupled tests**

```bash
git rm tests/unit/automation/motors/crawl4ai/portals/linkedin/test_apply.py
git rm tests/unit/automation/motors/crawl4ai/portals/xing/test_apply.py
git rm tests/unit/automation/motors/crawl4ai/portals/stepstone/test_apply.py
```

- [ ] **Step 7: Run full test suite**

```bash
python -m pytest tests/unit/automation/ -q
```

Expected: all pass, no references to `Crawl4AIApplyProvider` in portal tests

- [ ] **Step 8: Commit**

```bash
git add tests/unit/automation/portals/
git commit -m "refactor(tests): move portal map tests out of motors/; test maps directly via ariadne.models"
```

---

## Task 7: Add AST-Based Layer Boundary Guardrail Test

**Files:**
- Create: `tests/unit/automation/test_boundary_guardrails.py`

This test statically scans import statements and fails if any layer imports from a layer it is not allowed to depend on.

**Dependency rules:**
- `ariadne/` → may NOT import from `motors/` or `portals/`
- `portals/` → may NOT import from `motors/`
- `motors/crawl4ai/` → may NOT import from `portals/`
- `motors/browseros/` → may NOT import from `portals/`

- [ ] **Step 1: Write the test**

```python
# tests/unit/automation/test_boundary_guardrails.py
"""AST-based import boundary guardrail.

Enforces the Ariadne dependency rule:
  ariadne/ (domain) → portals/ + motors/ (adapters) → execution libs

No layer may import from a layer above it in the hierarchy.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

SRC = Path("src/automation")

# Each entry: layer_path → list of forbidden import prefixes
RULES: dict[str, list[str]] = {
    "ariadne": [
        "src.automation.motors",
        "src.automation.portals",
    ],
    "portals": [
        "src.automation.motors",
    ],
    "motors/crawl4ai": [
        "src.automation.portals",
    ],
    "motors/browseros": [
        "src.automation.portals",
    ],
}


def _collect_imports(path: Path) -> list[str]:
    """Return all import module strings found in a Python file."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def _find_violations(layer: str, forbidden: list[str]) -> list[str]:
    layer_path = SRC / layer
    if not layer_path.exists():
        return []
    violations: list[str] = []
    for py_file in sorted(layer_path.rglob("*.py")):
        for imp in _collect_imports(py_file):
            for prefix in forbidden:
                if imp == prefix or imp.startswith(prefix + "."):
                    rel = py_file.relative_to(SRC)
                    violations.append(f"  {rel}: imports '{imp}' (forbidden: '{prefix}')")
    return violations


@pytest.mark.parametrize("layer,forbidden", RULES.items())
def test_layer_does_not_import_forbidden(layer: str, forbidden: list[str]) -> None:
    violations = _find_violations(layer, forbidden)
    assert not violations, (
        f"Layer boundary violations in 'src/automation/{layer}':\n"
        + "\n".join(violations)
    )
```

- [ ] **Step 2: Run the test**

```bash
python -m pytest tests/unit/automation/test_boundary_guardrails.py -v
```

Expected: 4 PASSED (all layers clean after previous tasks)

If any violations are reported, fix the offending import before proceeding.

- [ ] **Step 3: Commit**

```bash
git add tests/unit/automation/test_boundary_guardrails.py
git commit -m "test(guardrails): add AST-based layer boundary import scanner"
```

---

## Task 8: Fix Stale Debt Items

**Files:**
- Modify: legacy debt tracker under `plan_docs/issues/`

Three items were fixed in previous commits but remain marked as open checkboxes in the debt tracker.

- [ ] **Step 1: Open the legacy debt tracker in `plan_docs/issues/` and find the three stale items**

The three items to mark as done (change `- [ ]` to `- [x]`):

1. `_get_live_state` opens new crawler inside an existing crawler context
2. `status` variable shadowing in the C4AI `run()` loop
3. BrowserOS CSS Support checkbox (was listed as unchecked but the fix already landed)

- [ ] **Step 2: Mark them as resolved in the debt doc**

For each stale item, change:
```markdown
- [ ] <description>
```
to:
```markdown
- [x] <description> _(fixed in <commit-sha>)_
```

Use `git log --oneline` to find the relevant commit SHA to reference.

- [ ] **Step 3: Run full test suite one final time**

```bash
python -m pytest tests/unit/automation/ -q
```

Expected: all pass

- [ ] **Step 4: Commit**

```bash
git add plan_docs/issues/
git commit -m "docs(debt): mark three stale items as resolved"
```

---

## Self-Review

### Spec coverage

| Requirement | Task |
|---|---|
| `MotorSession` / `MotorProvider` protocols | Task 1 |
| `AriadneSession` orchestrator (map loading, nav loop, idempotency, meta write) | Task 2 |
| C4AI motor provider (observe via JS hook, execute_step via C4AIReplayer) | Task 3 |
| BrowserOS motor provider (observe via search_dom, execute_step via execute_single_step) | Task 4 |
| `registry.py` collapsed | Task 5 |
| Portal tests decoupled from motor class | Task 6 |
| Boundary guardrail test | Task 7 |
| Debt doc accuracy | Task 8 |

### Placeholder scan

No TBD/TODO/placeholder items. All code blocks are complete.

### Type consistency

- `MotorSession.observe` → `dict[str, bool]`: used consistently in `AriadneSession._collect_selectors`, `C4AIMotorSession.observe`, `BrowserOSMotorSession.observe`, and `AriadneNavigator.find_current_state`.
- `MotorSession.execute_step` signature: `(step, context, cv_path, letter_path, is_first, url)` — matches all three callers (AriadneSession, C4AIMotorSession delegating to C4AIReplayer, BrowserOSMotorSession delegating to execute_single_step).
- `BrowserOSReplayer.execute_single_step` uses same internal `_execute_action` / `_assert_observation` methods as the existing `run()`.
- `AriadneSession._build_context` returns same shape as what `C4AIReplayer.execute_step` and `BrowserOSReplayer` already consume (profile, job, cv_path, letter_path).
