# Apply Module — Models and CLI

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Create the foundational scaffolding for `src/apply/` — Pydantic models, the CLI entry point, and the `__init__.py` exports.

**Architecture:** Mirror the `src/scraper/` pattern exactly — a `build_providers()` function, argparse, `asyncio.run(main())`. Models follow the design described in `src/apply/README.md` and `plan_docs/applying/applying_feature_design.md`.

**Tech Stack:** Python stdlib only for this task (Pydantic, argparse, asyncio). No crawl4ai dependency yet.

---

## Design Rules

1. **Mirror `src/scraper/main.py` structure.** Same `build_providers()`, same argparse shape, same logging setup with file + stream handlers. Read `src/scraper/main.py` before writing — don't invent a different pattern.
2. **DataManager** is at `src/core/data_manager.py`. Use `write_json_artifact(source, job_id, node_name, stage, filename, data)` and `read_json_artifact(...)` — same kwargs every time.
3. **LogTag** is at `src/shared/log_tags.py`. Import and use it — never write emoji strings by hand.
4. **`data/` is already in `.gitignore`**, so `data/profiles/` is automatically excluded from git. No change needed.
5. **`--setup-session` and `--job-id` are mutually exclusive.** Validate in `main()` with `sys.exit(1)` if both present.
6. Models are Pydantic v2 `BaseModel` — use `model_dump()` for serialization.

---

## File Structure

- Create: `src/apply/__init__.py`
- Create: `src/apply/models.py`
- Create: `src/apply/main.py`
- Create: `src/apply/providers/__init__.py`
- Test: `tests/test_apply_models.py`

---

### Task 1: Models

**Files:**
- Create: `src/apply/models.py`
- Test: `tests/test_apply_models.py`

- [ ] **Step 1: Write the failing test**

```python
# tests/test_apply_models.py
"""Tests for apply module models (spec Section 3)."""
from src.apply.models import ApplicationRecord, ApplyMeta, FormSelectors


def test_form_selectors_mandatory_fields_required():
    """FormSelectors requires all four mandatory selectors."""
    import pytest
    with pytest.raises(Exception):
        FormSelectors()  # missing mandatory fields

    sel = FormSelectors(
        apply_button="button[data-testid='apply']",
        cv_upload="input[type='file']",
        submit_button="button[type='submit']",
        success_indicator=".application-success",
    )
    assert sel.first_name is None
    assert sel.cv_select_existing is None


def test_form_selectors_optional_fields():
    """Optional selectors default to None."""
    sel = FormSelectors(
        apply_button="button",
        cv_upload="input",
        submit_button="button",
        success_indicator=".success",
        first_name="input[name='firstName']",
        cv_select_existing="button.select-cv",
    )
    assert sel.first_name == "input[name='firstName']"
    assert sel.last_name is None


def test_apply_meta_status_values():
    """ApplyMeta accepts only the four defined status values."""
    import pytest
    for status in ("submitted", "dry_run", "failed", "portal_changed"):
        m = ApplyMeta(status=status, timestamp="2026-03-30T00:00:00Z")
        assert m.status == status
    with pytest.raises(Exception):
        ApplyMeta(status="unknown", timestamp="2026-03-30T00:00:00Z")


def test_apply_meta_serialization():
    """ApplyMeta.model_dump() produces a plain dict."""
    m = ApplyMeta(status="submitted", timestamp="2026-03-30T00:00:00Z")
    d = m.model_dump()
    assert d["status"] == "submitted"
    assert d["error"] is None


def test_application_record_round_trip():
    """ApplicationRecord serializes and deserializes cleanly."""
    rec = ApplicationRecord(
        source="xing",
        job_id="12345",
        job_title="Data Engineer",
        company_name="Acme GmbH",
        application_url="https://xing.com/jobs/data-engineer-12345",
        cv_path="/path/to/cv.pdf",
        letter_path=None,
        fields_filled=["first_name", "last_name", "email"],
        dry_run=False,
        submitted_at="2026-03-30T00:00:00Z",
        confirmation_text="Your application was received.",
    )
    d = rec.model_dump()
    assert d["source"] == "xing"
    assert d["letter_path"] is None
    assert d["dry_run"] is False
```

- [ ] **Step 2: Run test to verify it fails**

```bash
python -m pytest tests/test_apply_models.py -v
```

Expected: `ModuleNotFoundError: No module named 'src.apply'`

- [ ] **Step 3: Create `src/apply/models.py`**

```python
"""Pydantic models for the apply module.

Design reference: `src/apply/README.md` and `plan_docs/applying/applying_feature_design.md`
"""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class FormSelectors(BaseModel):
    """CSS selectors the adapter validates against the live DOM before interaction.

    Mandatory selectors (apply_button, cv_upload, submit_button, success_indicator):
    absence raises PortalStructureChangedError.

    Optional selectors: absence is logged as a warning and the interaction is skipped.
    """

    # Mandatory
    apply_button: str
    cv_upload: str
    submit_button: str
    success_indicator: str

    # Optional
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    letter_upload: str | None = None
    error_indicator: str | None = None
    cv_select_existing: str | None = None  # portals that prefer selecting a saved CV


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

- [ ] **Step 4: Create `src/apply/__init__.py`**

```python
"""Auto-application module.

Entry point: python -m src.apply.main
"""
```

- [ ] **Step 5: Create `src/apply/providers/__init__.py`**

```python
```

(empty file)

- [ ] **Step 6: Run tests to verify they pass**

```bash
python -m pytest tests/test_apply_models.py -v
```

Expected: All 5 tests PASS.

- [ ] **Step 7: Commit**

```bash
git add src/apply/__init__.py src/apply/models.py src/apply/providers/__init__.py tests/test_apply_models.py
git commit -m "feat(apply): add Pydantic models (FormSelectors, ApplyMeta, ApplicationRecord)"
```

---

### Task 2: CLI Entry Point

**Files:**
- Create: `src/apply/main.py`

> **Note:** The CLI imports `XingApplyAdapter` and `StepStoneApplyAdapter`, which don't exist yet. Use `TYPE_CHECKING` or a lazy import inside `build_providers()` so the module is importable before the adapters are written.

- [ ] **Step 1: Write the failing test**

```python
# Add to tests/test_apply_models.py (append at end of file)

def test_build_parser_requires_source():
    """build_parser() creates a parser that requires --source."""
    import pytest
    from src.apply.main import build_parser
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args([])


def test_build_parser_apply_mode():
    """build_parser() parses apply mode args."""
    from src.apply.main import build_parser
    parser = build_parser()
    args = parser.parse_args([
        "--source", "xing",
        "--job-id", "12345",
        "--cv", "/path/cv.pdf",
        "--dry-run",
    ])
    assert args.source == "xing"
    assert args.job_id == "12345"
    assert args.cv_path == "/path/cv.pdf"
    assert args.dry_run is True
    assert args.setup_session is False


def test_build_parser_setup_session_mode():
    """build_parser() parses setup-session mode."""
    from src.apply.main import build_parser
    parser = build_parser()
    args = parser.parse_args(["--source", "xing", "--setup-session"])
    assert args.setup_session is True
    assert args.job_id is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_apply_models.py::test_build_parser_requires_source -v
```

Expected: `ImportError: cannot import name 'build_parser' from 'src.apply.main'`

- [ ] **Step 3: Create `src/apply/main.py`**

```python
"""CLI entry point and provider registry for job auto-application.

Usage:
    # Apply to a job
    python -m src.apply.main --source xing --job-id 12345 --cv cv.pdf [--letter letter.pdf] [--dry-run]

    # First-time session setup (mutually exclusive with apply mode)
    python -m src.apply.main --source xing --setup-session

Design reference: `src/apply/README.md` and `plan_docs/applying/applying_feature_design.md`
"""
from __future__ import annotations

import argparse
import asyncio
import datetime
import logging
import os
import sys
from pathlib import Path

from src.core.data_manager import DataManager
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def build_providers(data_manager: DataManager | None = None) -> dict[str, object]:
    """Lazy import adapters to avoid import-time crawl4ai initialization."""
    from src.apply.providers.stepstone.adapter import StepStoneApplyAdapter
    from src.apply.providers.xing.adapter import XingApplyAdapter

    manager = data_manager or DataManager()
    return {
        "xing": XingApplyAdapter(manager),
        "stepstone": StepStoneApplyAdapter(manager),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Job auto-application CLI")
    parser.add_argument(
        "--source",
        required=True,
        choices=["xing", "stepstone"],
        help="Job portal to apply on.",
    )
    # Apply mode
    parser.add_argument("--job-id", dest="job_id", help="Job ID to apply to.")
    parser.add_argument("--cv", dest="cv_path", help="Path to CV PDF.")
    parser.add_argument("--letter", dest="letter_path", help="Path to cover letter PDF (optional).")
    parser.add_argument(
        "--dry-run",
        dest="dry_run",
        action="store_true",
        default=False,
        help="Fill form but do not submit (marcha blanca mode).",
    )
    # Session setup mode — mutually exclusive with apply mode
    parser.add_argument(
        "--setup-session",
        dest="setup_session",
        action="store_true",
        default=False,
        help="Open visible browser to log in manually. Mutually exclusive with --job-id.",
    )
    return parser


async def main(argv: list[str] | None = None) -> None:
    args = build_parser().parse_args(argv or sys.argv[1:])

    os.makedirs("logs", exist_ok=True)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/apply_{args.source}_{timestamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.FileHandler(log_filename, encoding="utf-8"),
            logging.StreamHandler(),
        ],
        force=True,
    )

    if args.setup_session and args.job_id:
        logger.error(
            "%s --setup-session and --job-id are mutually exclusive.", LogTag.FAIL
        )
        sys.exit(1)

    providers = build_providers()
    adapter = providers[args.source]

    if args.setup_session:
        await adapter.setup_session()
        return

    if not args.job_id or not args.cv_path:
        logger.error(
            "%s --job-id and --cv are required in apply mode.", LogTag.FAIL
        )
        sys.exit(1)

    meta = await adapter.run(
        job_id=args.job_id,
        cv_path=Path(args.cv_path),
        letter_path=Path(args.letter_path) if args.letter_path else None,
        dry_run=args.dry_run,
    )
    logger.info("%s Apply completed: status=%s", LogTag.OK, meta.status)


if __name__ == "__main__":
    asyncio.run(main())
```

- [ ] **Step 4: Run all apply model tests**

```bash
python -m pytest tests/test_apply_models.py -v
```

Expected: All 8 tests PASS.

- [ ] **Step 5: Commit**

```bash
git add src/apply/main.py tests/test_apply_models.py
git commit -m "feat(apply): add CLI entry point with argparse and provider registry"
```
