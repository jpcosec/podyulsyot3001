# Unmask Pipeline Errors + Move Translator to CLI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Unmask swallowed errors across the pipeline and move translation out of the LangGraph server into the CLI pre-processing step, eliminating the recursion-depth failure that blocks all German-language jobs.

**Architecture:** Translation moves from a LangGraph node (runs inside the server, deep stack) to a CLI-side pre-processing step (shallow stack, clean context). The `translate` graph node becomes a verification-only step that fails loudly if the artifact is missing. Every other broad `except` that hides real failures is either re-raised, promoted to ERROR, or given a clear failure signal.

**Tech Stack:** Python 3.13, LangGraph 1.1.3, `deep-translator`, Textual TUI, pytest

---

## Files Changed

| File | Change |
|------|--------|
| `future_docs/issues/load_profile_patches_silent_failure.md` | Create — deferred issue doc |
| `src/core/tools/translator/main.py` | Extract `translate_single_job()` function |
| `src/graph/nodes/translate.py` | Replace translation logic with verify-artifact-only |
| `src/graph/__init__.py` | Fix `extract_bridge` crash + warn on missing content.md |
| `src/cli/main.py` | Add translate pre-step to `_run_batch` and `_run_pipeline` |
| `src/core/ai/match_skill/storage.py` | Promote `propagate_profile_patches` exception to ERROR |
| `src/review_ui/screens/review_screen.py` | Add error state after failed `_submit_review` |
| `src/cli/main.py` | Log actual exception in `_run_api` health check |
| `tests/test_pipeline_graph.py` | Add translate-node and extract-bridge failure tests |

---

## Task 1: Document load_profile patches issue in future_docs

**Files:**
- Create: `future_docs/issues/load_profile_patches_silent_failure.md`
- Modify: `src/graph/nodes/load_profile.py:89-96` (add inline TODO)

- [ ] **Step 1: Create the future_docs entry**

Write `future_docs/issues/load_profile_patches_silent_failure.md`:

```markdown
# load_profile: Swallowed Patch Merge Failure

**Why deferred:** Patch files are absent in most environments. The failure path is uncommon and the fix requires deciding whether a bad patches file should abort the whole pipeline run.
**Last reviewed:** 2026-03-30

## Problem / Motivation

`_load_profile_sync` in `src/graph/nodes/load_profile.py` catches any exception from
loading or merging `profile_patches.json` with a warning log and silently continues
with an un-patched evidence set.

```python
try:
    global_patches = data_manager.read_json_path(patches_path)
    evidence = _merge_patches(evidence, global_patches)
except Exception as e:
    logger.warning(f"{LogTag.WARN} Failed to load profile patches: {e}")
```

This means:
- A corrupt or schema-mismatched `profile_patches.json` goes unnoticed.
- The match runs with fewer evidence items than the operator intended.
- The operator has no signal that their patch file was ignored.

## Proposed Direction

Replace the broad `except` with a tight `except (json.JSONDecodeError, OSError)` for
read failures (legitimate — file may be malformed) and let `_merge_patches` type errors
propagate as `ValueError` to the outer node handler, which will surface them as
`status=failed` with an `error_state` block. Add a log at ERROR level even for the
handled read failures.

```python
try:
    global_patches = data_manager.read_json_path(patches_path)
    evidence = _merge_patches(evidence, global_patches)
except (json.JSONDecodeError, OSError) as e:
    logger.error(f"{LogTag.FAIL} Failed to read profile patches — running without them: {e}")
```

## Linked TODOs

- `src/graph/nodes/load_profile.py:95` — `# TODO(future): tighten patches exception — see future_docs/issues/load_profile_patches_silent_failure.md`
```

- [ ] **Step 2: Add inline TODO in load_profile.py**

In `src/graph/nodes/load_profile.py`, replace line 96:
```python
            logger.warning(f"{LogTag.WARN} Failed to load profile patches: {e}")
```
with:
```python
            logger.warning(f"{LogTag.WARN} Failed to load profile patches: {e}")
            # TODO(future): tighten patches exception — see future_docs/issues/load_profile_patches_silent_failure.md
```

- [ ] **Step 3: Commit**

```bash
git add future_docs/issues/load_profile_patches_silent_failure.md src/graph/nodes/load_profile.py
git commit -m "docs: add future_docs entry for load_profile patches silent failure"
```

---

## Task 2: Fix extract_bridge — abort cleanly when translate artifact is missing

The node currently crashes with an unhandled `FileNotFoundError` when `translate/proposed/state.json`
doesn't exist (because the translate node failed). It must return `status=failed` with an `error_state`
so the graph terminates cleanly.

**Files:**
- Modify: `src/graph/__init__.py:24-88`
- Test: `tests/test_pipeline_graph.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_pipeline_graph.py`:

```python
def test_extract_bridge_returns_failed_when_translate_missing(tmp_path):
    """extract_bridge must return status=failed, not raise, when translate artifact is absent."""
    from unittest.mock import MagicMock
    from src.graph import make_extract_bridge_node
    from src.core.data_manager import DataManager

    dm = MagicMock(spec=DataManager)
    dm.read_json_artifact.side_effect = FileNotFoundError("translate/proposed/state.json not found")

    node = make_extract_bridge_node(dm)
    state = {
        "source": "test",
        "job_id": "999",
        "status": "failed",
        "artifact_refs": {},
        "error_state": {"node": "translate", "message": "Translation failed", "details": None},
    }
    result = node(state)

    assert result["status"] == "failed"
    assert result["current_node"] == "extract_bridge"
    assert "translate" in result["error_state"]["message"].lower()
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd /home/jp/postulator/podyulsyot3001 && python -m pytest tests/test_pipeline_graph.py::test_extract_bridge_returns_failed_when_translate_missing -v
```

Expected: FAIL — node raises `FileNotFoundError` instead of returning error state.

- [ ] **Step 3: Fix `_extract_bridge_node` in `src/graph/__init__.py`**

Replace the entire `_extract_bridge_node` function (lines 24–80):

```python
def _extract_bridge_node(state: GraphState, data_manager: DataManager) -> dict:
    source = state["source"]
    job_id = state["job_id"]

    if state.get("status") == "failed":
        prior = state.get("error_state") or {}
        return {
            "current_node": "extract_bridge",
            "status": "failed",
            "error_state": {
                "node": "extract_bridge",
                "message": f"Skipped: upstream node '{prior.get('node', 'unknown')}' failed — {prior.get('message', '')}",
                "details": None,
            },
        }

    try:
        translated_state = data_manager.read_json_artifact(
            source=source,
            job_id=job_id,
            node_name="translate",
            stage="proposed",
            filename="state.json",
        )
    except FileNotFoundError:
        return {
            "current_node": "extract_bridge",
            "status": "failed",
            "error_state": {
                "node": "extract_bridge",
                "message": "translate/proposed/state.json not found — translation must complete before extract_bridge",
                "details": None,
            },
        }

    requirements = extract_requirements_from_job_posting(translated_state)
    requirements_dicts = [item.model_dump() for item in requirements]
    state_payload = {
        "source": source,
        "job_id": job_id,
        "requirements": requirements_dicts,
        "job_posting": translated_state,
    }
    refs = dict(state.get("artifact_refs", {}))
    bridge_state = data_manager.write_json_artifact(
        source=source,
        job_id=job_id,
        node_name="extract_bridge",
        stage="proposed",
        filename="state.json",
        data=state_payload,
    )
    refs["bridge_state"] = str(bridge_state)
    try:
        content = data_manager.read_text_artifact(
            source=source,
            job_id=job_id,
            node_name="translate",
            stage="proposed",
            filename="content.md",
        )
        content_ref = data_manager.write_text_artifact(
            source=source,
            job_id=job_id,
            node_name="extract_bridge",
            stage="proposed",
            filename="content.md",
            content=content,
        )
        refs["bridge_content"] = str(content_ref)
    except FileNotFoundError:
        logger.warning(
            "%s translate/content.md absent for %s/%s — continuing without it",
            LogTag.WARN, source, job_id,
        )

    return {
        "artifact_refs": refs,
        "requirements": requirements_dicts,
        "current_node": "extract_bridge",
        "status": "running",
    }
```

Also add the missing imports at the top of `src/graph/__init__.py`:

```python
import logging
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)
```

And remove the now-unused nested `_build_bridge` wrapper in `make_extract_bridge_node`:

```python
def make_extract_bridge_node(data_manager: DataManager):
    """Create the extract-bridge node adapter for schema-v0."""

    def extract_bridge_node(state: GraphState) -> dict:
        return _extract_bridge_node(state, data_manager)

    return extract_bridge_node
```

- [ ] **Step 4: Run test to verify it passes**

```bash
python -m pytest tests/test_pipeline_graph.py::test_extract_bridge_returns_failed_when_translate_missing -v
```

Expected: PASS

- [ ] **Step 5: Run full test suite to check for regressions**

```bash
python -m pytest tests/test_pipeline_graph.py tests/test_extract_bridge.py -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add src/graph/__init__.py tests/test_pipeline_graph.py
git commit -m "fix: extract_bridge returns status=failed cleanly when translate artifact is missing"
```

---

## Task 3: Fix storage.py — propagate_profile_patches promotes to ERROR

The current `except Exception: warning` hides a real failure. User feedback is silently
lost when the write fails. Promote to ERROR level so it appears in logs and monitoring.

**Files:**
- Modify: `src/core/ai/match_skill/storage.py:188-195`

- [ ] **Step 1: Replace the exception handler in `propagate_profile_patches`**

In `src/core/ai/match_skill/storage.py`, find the `except` block around line 188:

```python
        except Exception as e:
            # We don't want to crash the whole pipeline if global sync fails
            # but we should log it
            import logging

            logging.getLogger(__name__).warning(
                f"Failed to propagate profile patches: {e}"
            )
```

Replace with:

```python
        except Exception as e:
            logger.error(
                "%s Failed to propagate profile patches to %s — feedback from this review will not be persisted globally: %s",
                LogTag.FAIL,
                global_path,
                e,
            )
```

Check that `logger` and `LogTag` are already imported at the top of `storage.py`. If not, add:

```python
import logging
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)
```

- [ ] **Step 2: Run match skill tests to confirm no regressions**

```bash
python -m pytest tests/test_match_skill.py -v
```

Expected: all PASS

- [ ] **Step 3: Commit**

```bash
git add src/core/ai/match_skill/storage.py
git commit -m "fix: promote propagate_profile_patches failure to ERROR level — feedback loss is now visible"
```

---

## Task 4: Fix review_screen — _submit_review shows error state after failure

When `resume_with_review` raises, the TUI currently logs red text but the screen
continues as if the review was submitted. The submit button should be re-enabled
and a persistent error banner should appear so the operator knows they must retry.

**Files:**
- Modify: `src/review_ui/screens/review_screen.py:160-180`

- [ ] **Step 1: Replace the `_submit_review` worker body**

Find the `_submit_review` worker method (around line 160). Replace its body:

```python
    @work(thread=True, exit_on_error=False)
    def _submit_review(self, payload: ReviewPayload) -> None:
        """Submit the review payload to LangGraph in a background thread."""
        self.app.call_from_thread(
            self.query_one("#status-log", RichLog).write,
            "[yellow]Submitting review to LangGraph…[/]",
        )
        try:
            result = self._bus.resume_with_review(payload)
            status = (
                result.get("status", "unknown") if isinstance(result, dict) else "done"
            )
            self.app.call_from_thread(
                self.query_one("#status-log", RichLog).write,
                f"[green]Graph resumed — final status: [bold]{status}[/bold][/]",
            )
        except Exception as exc:  # noqa: BLE001
            self.app.call_from_thread(self._on_submit_error, exc)

    def _on_submit_error(self, exc: Exception) -> None:
        """Re-enable submission UI and display the error after a failed resume."""
        log = self.query_one("#status-log", RichLog)
        log.write(f"[red bold]Submit failed — review was NOT sent to LangGraph.[/]")
        log.write(f"[red]{type(exc).__name__}: {exc}[/]")
        log.write("[yellow]Fix the error above and try submitting again.[/]")
        try:
            self.query_one("#submit-btn").disabled = False
        except Exception:  # noqa: BLE001
            pass  # submit button may not exist in all screen configurations
```

- [ ] **Step 2: Run TUI-related tests if any exist**

```bash
python -m pytest tests/ -k "review" -v
```

Expected: any existing tests PASS (there may be none for this screen).

- [ ] **Step 3: Commit**

```bash
git add src/review_ui/screens/review_screen.py
git commit -m "fix: review_screen re-enables submit and shows persistent error when resume_with_review fails"
```

---

## Task 5: Fix cli/main.py — log actual exception in _run_api health check

**Files:**
- Modify: `src/cli/main.py:234-240`

- [ ] **Step 1: Replace the silent except in `_run_api`**

Find the `_run_api` function (around line 228). Replace:

```python
    try:
        client = LangGraphAPIClient()
        if client.is_healthy():
            print(client.url)
            return 0
    except Exception:
        pass
```

With:

```python
    try:
        client = LangGraphAPIClient()
        if client.is_healthy():
            print(client.url)
            return 0
    except Exception as exc:
        logger.debug("LangGraph API health check raised: %s", exc)
```

- [ ] **Step 2: Run CLI tests**

```bash
python -m pytest tests/test_cli.py -v
```

Expected: all PASS

- [ ] **Step 3: Commit**

```bash
git add src/cli/main.py
git commit -m "fix: log actual exception in _run_api health check instead of silently swallowing"
```

---

## Task 6: Extract translate_single_job from translator/main.py

Pull the per-job translation logic into a reusable function so the CLI can call it
directly without going through the full directory-scan main().

**Files:**
- Modify: `src/core/tools/translator/main.py`
- Test: `tests/test_pipeline_graph.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_pipeline_graph.py`:

```python
def test_translate_single_job_skips_when_already_translated(tmp_path):
    """translate_single_job must skip and return True when output files already exist."""
    from unittest.mock import MagicMock, patch
    from src.core.tools.translator.main import translate_single_job
    from src.core.data_manager import DataManager

    dm = MagicMock(spec=DataManager)
    dm.artifact_path.return_value = tmp_path / "state.json"
    (tmp_path / "state.json").write_text('{"job_title": "Test"}')

    # Simulate already-translated output existing
    out_json = tmp_path / "out.json"
    out_md = tmp_path / "out.md"
    out_json.write_text("{}")
    out_md.write_text("")

    def _artifact_path(source, job_id, node_name, stage, filename):
        if node_name == "ingest":
            return tmp_path / "state.json" if filename == "state.json" else tmp_path / "content.md"
        return out_json if filename == "state.json" else out_md

    dm.artifact_path.side_effect = _artifact_path

    adapter = MagicMock()
    result = translate_single_job(dm, adapter, "test", "job1", target_lang="en", force=False)
    assert result is True
    adapter.translate_fields.assert_not_called()


def test_translate_single_job_translates_non_english(tmp_path):
    """translate_single_job must call adapter.translate_fields for non-English jobs."""
    import json
    from unittest.mock import MagicMock
    from src.core.tools.translator.main import translate_single_job
    from src.core.data_manager import DataManager

    ingest_json = tmp_path / "ingest_state.json"
    ingest_json.write_text(json.dumps({"job_title": "Ingenieur", "original_language": "de"}))
    ingest_md = tmp_path / "content.md"
    ingest_md.write_text("Beschreibung")
    out_json = tmp_path / "translate_state.json"
    out_md = tmp_path / "translate_content.md"

    dm = MagicMock(spec=DataManager)

    def _artifact_path(source, job_id, node_name, stage, filename):
        if node_name == "ingest":
            return ingest_json if filename == "state.json" else ingest_md
        return out_json if filename == "state.json" else out_md

    dm.artifact_path.side_effect = _artifact_path
    dm.read_json_path.return_value = {"job_title": "Ingenieur", "original_language": "de"}
    dm.read_text_path.return_value = "Beschreibung"

    adapter = MagicMock()
    adapter.translate_fields.return_value = {"job_title": "Engineer", "original_language": "en"}
    adapter.translate_text.return_value = "Description"

    result = translate_single_job(dm, adapter, "test", "job1", target_lang="en", force=False)
    assert result is True
    adapter.translate_fields.assert_called_once()
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_pipeline_graph.py::test_translate_single_job_skips_when_already_translated tests/test_pipeline_graph.py::test_translate_single_job_translates_non_english -v
```

Expected: FAIL — `translate_single_job` doesn't exist yet.

- [ ] **Step 3: Add `translate_single_job` to `src/core/tools/translator/main.py`**

Add this function before `main()`:

```python
def translate_single_job(
    data_manager: DataManager,
    adapter: "GoogleTranslatorAdapter",
    source: str,
    job_id: str,
    *,
    target_lang: str = "en",
    force: bool = False,
) -> bool:
    """Translate a single ingested job. Returns True on success or skip, raises on failure.

    Writes translated artifacts to ``nodes/translate/proposed/``.
    Skips silently if already translated and ``force`` is False.
    """
    ingest_json = data_manager.artifact_path(
        source=source, job_id=job_id, node_name="ingest", stage="proposed", filename="state.json"
    )
    ingest_md = data_manager.artifact_path(
        source=source, job_id=job_id, node_name="ingest", stage="proposed", filename="content.md"
    )
    out_json = data_manager.artifact_path(
        source=source, job_id=job_id, node_name="translate", stage="proposed", filename="state.json"
    )
    out_md = data_manager.artifact_path(
        source=source, job_id=job_id, node_name="translate", stage="proposed", filename="content.md"
    )

    if not ingest_json.exists():
        raise FileNotFoundError(f"Ingest artifact missing for {source}/{job_id}: {ingest_json}")

    if not force and out_json.exists() and out_md.exists():
        logger.info("[⏭️] %s/%s already translated — skipping", source, job_id)
        return True

    data = data_manager.read_json_path(ingest_json)
    orig_lang = data.get("original_language", "auto")

    if orig_lang == target_lang:
        logger.info("[⏭️] %s/%s already in target language '%s'", source, job_id, target_lang)
        translated_data = data
        translated_md = data_manager.read_text_path(ingest_md) if ingest_md.exists() else ""
    else:
        logger.info("[🔄] Translating %s/%s from '%s' to '%s'", source, job_id, orig_lang, target_lang)
        translated_data = adapter.translate_fields(
            data, fields=P_FIELDS_TO_TRANSLATE, target_lang=target_lang, source_lang=orig_lang
        )
        translated_data["original_language"] = target_lang
        md_content = data_manager.read_text_path(ingest_md) if ingest_md.exists() else ""
        translated_md = (
            adapter.translate_text(md_content, target_lang=target_lang, source_lang=orig_lang)
            if md_content
            else ""
        )

    data_manager.write_json_artifact(
        source=source, job_id=job_id, node_name="translate", stage="proposed",
        filename="state.json", data=translated_data,
    )
    data_manager.write_text_artifact(
        source=source, job_id=job_id, node_name="translate", stage="proposed",
        filename="content.md", content=translated_md,
    )
    logger.info("[✅] %s/%s translated successfully", source, job_id)
    return True
```

Add the `DataManager` import at the top if not already present:
```python
from src.core.data_manager import DataManager
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_pipeline_graph.py::test_translate_single_job_skips_when_already_translated tests/test_pipeline_graph.py::test_translate_single_job_translates_non_english -v
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/core/tools/translator/main.py tests/test_pipeline_graph.py
git commit -m "feat: extract translate_single_job() from translator main for CLI pre-processing use"
```

---

## Task 7: Replace translate node with verify-artifact-only logic

The graph node must no longer perform translation. It verifies the artifact exists and
sets the refs. If missing, it fails loudly with a clear actionable message.

**Files:**
- Modify: `src/graph/nodes/translate.py`
- Test: `tests/test_pipeline_graph.py`

- [ ] **Step 1: Write the failing test**

Add to `tests/test_pipeline_graph.py`:

```python
def test_translate_node_fails_when_artifact_missing(tmp_path):
    """translate node must return status=failed when translate/state.json is absent."""
    from unittest.mock import MagicMock
    from src.graph.nodes.translate import make_translate_node
    from src.core.data_manager import DataManager

    dm = MagicMock(spec=DataManager)
    dm.artifact_exists.return_value = False
    dm.artifact_path.return_value = tmp_path / "state.json"  # doesn't exist

    node = make_translate_node(dm)
    result = node({"source": "test", "job_id": "999", "artifact_refs": {}})

    assert result["status"] == "failed"
    assert result["current_node"] == "translate"
    assert "translate" in result["error_state"]["message"].lower()


def test_translate_node_succeeds_when_artifact_present(tmp_path):
    """translate node must return status=running and populate refs when artifact exists."""
    import json
    from unittest.mock import MagicMock
    from src.graph.nodes.translate import make_translate_node
    from src.core.data_manager import DataManager

    state_file = tmp_path / "state.json"
    state_file.write_text(json.dumps({"job_title": "Engineer"}))

    dm = MagicMock(spec=DataManager)
    dm.artifact_path.return_value = state_file
    dm.artifact_exists.side_effect = lambda **kw: kw.get("filename") == "state.json"

    node = make_translate_node(dm)
    result = node({"source": "test", "job_id": "999", "artifact_refs": {}})

    assert result["status"] == "running"
    assert result["current_node"] == "translate"
    assert "translated_state" in result["artifact_refs"]
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
python -m pytest tests/test_pipeline_graph.py::test_translate_node_fails_when_artifact_missing tests/test_pipeline_graph.py::test_translate_node_succeeds_when_artifact_present -v
```

Expected: FAIL — node still tries to translate instead of just verifying.

- [ ] **Step 3: Replace `src/graph/nodes/translate.py`**

```python
"""Pipeline translate node — verify-only adapter for schema-v0.

Translation is performed as a CLI pre-processing step (src.core.tools.translator.main).
This node verifies the translated artifact is present and populates artifact_refs.
"""

from __future__ import annotations

import logging

from src.core.data_manager import DataManager
from src.core.state import GraphState
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


def make_translate_node(data_manager: DataManager):
    """Create the translate verify node."""

    def translate_node(state: GraphState) -> dict:
        source = state["source"]
        job_id = state["job_id"]
        refs = dict(state.get("artifact_refs", {}))

        state_path = data_manager.artifact_path(
            source=source,
            job_id=job_id,
            node_name="translate",
            stage="proposed",
            filename="state.json",
        )

        if not state_path.exists():
            logger.error(
                "%s translate/proposed/state.json missing for %s/%s — run 'translate' step before pipeline",
                LogTag.FAIL, source, job_id,
            )
            return {
                "current_node": "translate",
                "status": "failed",
                "error_state": {
                    "node": "translate",
                    "message": (
                        f"translate/proposed/state.json not found for {source}/{job_id}. "
                        "Translation must be run before launching the pipeline."
                    ),
                    "details": None,
                },
            }

        refs["translated_state"] = str(state_path)

        content_path = data_manager.artifact_path(
            source=source,
            job_id=job_id,
            node_name="translate",
            stage="proposed",
            filename="content.md",
        )
        if content_path.exists():
            refs["translated_content"] = str(content_path)

        logger.info("%s Translate artifact verified for %s/%s", LogTag.OK, source, job_id)
        return {
            "artifact_refs": refs,
            "current_node": "translate",
            "status": "running",
        }

    return translate_node
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
python -m pytest tests/test_pipeline_graph.py::test_translate_node_fails_when_artifact_missing tests/test_pipeline_graph.py::test_translate_node_succeeds_when_artifact_present -v
```

Expected: PASS

- [ ] **Step 5: Run full pipeline graph tests**

```bash
python -m pytest tests/test_pipeline_graph.py -v
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add src/graph/nodes/translate.py tests/test_pipeline_graph.py
git commit -m "feat: translate node becomes verify-only — translation is now a CLI pre-processing step"
```

---

## Task 8: Add translate pre-step to CLI run-batch and pipeline commands

`_run_batch` and `_run_pipeline` must translate each job before invoking the API.
If translation fails for a job, that job is skipped with an error log — others continue.

**Files:**
- Modify: `src/cli/main.py`

- [ ] **Step 1: Add `_translate_jobs` helper to `src/cli/main.py`**

Add after the `_build_pipeline_input` function (around line 163):

```python
def _translate_jobs(jobs: list[tuple[str, str]], *, force: bool = False) -> list[tuple[str, str]]:
    """Translate all jobs in-place before pipeline invocation. Returns successfully translated jobs."""
    from src.core.tools.translator.main import translate_single_job, PROVIDERS
    from src.core import DataManager

    data_manager = DataManager()
    adapter = PROVIDERS["google"]
    ready: list[tuple[str, str]] = []

    for source, job_id in jobs:
        try:
            translate_single_job(data_manager, adapter, source, job_id, force=force)
            ready.append((source, job_id))
        except Exception as exc:
            logger.error(
                "%s Translation failed for %s/%s — skipping: %s",
                LogTag.FAIL, source, job_id, exc,
            )

    return ready
```

- [ ] **Step 2: Wire `_translate_jobs` into `_run_batch`**

In `_run_batch`, after the `if not jobs:` guard (around line 329) and before the `initial_input` block, add:

```python
    jobs = _translate_jobs(jobs)
    if not jobs:
        logger.error("%s All jobs failed translation — nothing to run", LogTag.FAIL)
        return 1
```

The full `_run_batch` body becomes:

```python
async def _run_batch(args: argparse.Namespace) -> int:
    url = LangGraphAPIClient.ensure_server()
    client = LangGraphAPIClient(url)
    data_manager = DataManager()

    jobs: list[tuple[str, str]] = []
    if args.jobs:
        jobs.extend(
            _parse_job_selector(selector, args.sources) for selector in args.jobs
        )
    if args.stdin:
        jobs.extend(_read_jobs_from_stdin(args.sources))
    if not jobs:
        jobs = _newest_jobs_for_sources(data_manager, args.sources, args.limit)

    if not jobs:
        logger.warning("%s No jobs selected for batch run", LogTag.WARN)
        return 1

    jobs = _translate_jobs(jobs)
    if not jobs:
        logger.error("%s All jobs failed translation — nothing to run", LogTag.FAIL)
        return 1

    initial_input = _build_pipeline_input(
        profile_evidence_path=args.profile_evidence,
        requirements_path=args.requirements,
    )
    if args.auto_approve_review:
        initial_input["auto_approve_review"] = True
    for source, job_id in jobs:
        result = await _invoke_remote_pipeline(
            client,
            source=source,
            job_id=job_id,
            initial_input=initial_input,
        )
        logger.info(
            "%s Batch run %s/%s finished with status %s",
            LogTag.OK,
            source,
            job_id,
            result.get("status"),
        )
        print(f"{source}\t{job_id}\t{result.get('status', 'unknown')}")
    return 0
```

- [ ] **Step 3: Wire `_translate_jobs` into `_run_pipeline`**

In `_run_pipeline`, before `initial_input = _build_pipeline_input(...)`, add:

```python
    ready = _translate_jobs([(args.source, args.job_id)])
    if not ready:
        logger.error("%s Translation failed for %s/%s — aborting", LogTag.FAIL, args.source, args.job_id)
        return 1
```

The full `_run_pipeline` body becomes:

```python
async def _run_pipeline(args: argparse.Namespace) -> int:
    url = LangGraphAPIClient.ensure_server()
    client = LangGraphAPIClient(url)

    ready = _translate_jobs([(args.source, args.job_id)])
    if not ready:
        logger.error("%s Translation failed for %s/%s — aborting", LogTag.FAIL, args.source, args.job_id)
        return 1

    initial_input = _build_pipeline_input(
        profile_evidence_path=args.profile_evidence,
        requirements_path=args.requirements,
    )
    if args.auto_approve_review:
        initial_input["auto_approve_review"] = True
    result = await _invoke_remote_pipeline(
        client,
        source=args.source,
        job_id=args.job_id,
        source_url=args.source_url,
        initial_input=initial_input,
    )
    logger.info("%s Pipeline finished with status: %s", LogTag.OK, result.get("status"))
    return 0
```

- [ ] **Step 4: Run CLI tests**

```bash
python -m pytest tests/test_cli.py -v
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add src/cli/main.py
git commit -m "feat: run-batch and pipeline commands translate jobs in CLI before invoking LangGraph server"
```

---

## Task 9: End-to-end smoke test — HITL pause only

Verify the happy path up to the HITL pause using a fresh job each run.

**Files:** none (manual verification)

- [ ] **Step 1: Delete previously ingested data to start clean**

```bash
rm -rf /home/jp/postulator/podyulsyot3001/data/jobs
```

- [ ] **Step 2: Scrape 1 job from tuberlin**

```bash
cd /home/jp/postulator/podyulsyot3001 && python3 -m src.scraper.main --source tuberlin --limit 1 2>&1 | tail -5
```

Expected: `[✅] Ingested 1 jobs for source 'tuberlin'`

- [ ] **Step 3: Verify LangGraph server is running from correct directory**

```bash
curl -s http://localhost:8124/ok
```

Expected: `{"ok":true}`. If not running, start with:
```bash
nohup langgraph dev --config langgraph.json --no-browser --port 8124 > /tmp/langgraph_postulator.log 2>&1 &
sleep 12 && curl -s http://localhost:8124/ok
```

- [ ] **Step 4: Run pipeline for tuberlin (will translate then invoke)**

```bash
python3 -m src.cli.main run-batch --sources tuberlin --limit 1 2>&1
```

Expected output includes:
- `[🔄] Translating tuberlin/... from 'de' to 'en'` (or `[⏭️]` if already en)
- `[✅] ... translated successfully`
- Run status: `running` (paused at HITL)

- [ ] **Step 5: Confirm thread is paused at match_skill (not crashed)**

```bash
python3 -c "
import httpx, json
from src.core.api_client import LangGraphAPIClient
import os; job_id = os.listdir('data/jobs/tuberlin')[0]
tid = LangGraphAPIClient.thread_id_for('tuberlin', job_id)
r = httpx.get(f'http://localhost:8124/threads/{tid}/state')
v = r.json().get('values', {})
print(f'status={v.get(\"status\")} next={r.json().get(\"next\")} node={v.get(\"current_node\")}')
" 2>&1 | grep -v "urllib3\|RequestsDependency\|warnings.warn"
```

Expected: `status=running next=['match_skill'] node=load_profile` (HITL interrupt — correct)

- [ ] **Step 6: Run unit + integration test suite**

```bash
python -m pytest tests/ -q --ignore=tests/e2e
```

Expected: all PASS (or pre-existing failures only — no new regressions)

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "chore: verify up-to-HITL flow after translator move and error unmasking"
```

---

## Task 10: E2E test — full pipeline from scrape to package

Add a pytest-based e2e test that runs the complete pipeline (scrape → translate →
match with auto-approve → generate_documents → render → package) against the live
LangGraph server. Each test invocation scrapes a fresh job so stale artifacts never
mask regressions.

**Files:**
- Create: `tests/e2e/fixtures/stub_profile.json`
- Modify: `tests/e2e/test_pipeline.py`

- [ ] **Step 1: Create the stub profile fixture**

Write `tests/e2e/fixtures/stub_profile.json`:

```json
{
  "owner": {
    "full_name": "Test Candidate",
    "email": "test@example.com",
    "professional_summary": "Experienced data scientist with Python and ML background.",
    "tagline": "Data Scientist"
  },
  "education": [
    {
      "degree": "M.Sc. Computer Science",
      "institution": "Test University",
      "specialization": "Machine Learning"
    }
  ],
  "experience": [
    {
      "role": "Data Scientist",
      "organization": "TestCorp GmbH",
      "start_date": "2020-01",
      "end_date": null,
      "achievements": [
        "Built and deployed ML pipelines using Python and scikit-learn.",
        "Developed SQL-based reporting dashboards in Power BI.",
        "Implemented data quality checks and ELT processes."
      ]
    }
  ],
  "projects": [
    {
      "name": "ML Pipeline Automation",
      "role": "Lead Engineer",
      "stack": ["Python", "scikit-learn", "SQL", "Azure"]
    }
  ],
  "skills": {
    "programming": ["Python", "SQL"],
    "ml": ["scikit-learn", "Machine Learning", "Data Science"],
    "tools": ["Power BI", "Azure", "Git"]
  },
  "languages": [
    {"name": "English", "level": "C2"},
    {"name": "German", "level": "B2"}
  ]
}
```

- [ ] **Step 2: Write the failing e2e test class**

Add to `tests/e2e/test_pipeline.py`:

```python
import asyncio
import json
import os
import shutil
from pathlib import Path

import httpx
import pytest

FIXTURES = Path(__file__).parent / "fixtures"
SERVER_URL = "http://localhost:8124"
PROFILE_PATH = "data/reference_data/profile/base_profile/profile_base_data.json"


def _server_available() -> bool:
    try:
        return httpx.get(f"{SERVER_URL}/ok", timeout=2).status_code == 200
    except Exception:
        return False


@pytest.fixture()
def stub_profile(tmp_path):
    """Install stub profile_base_data.json at the expected default path and clean up after."""
    dest = Path(PROFILE_PATH)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(FIXTURES / "stub_profile.json", dest)
    yield dest
    dest.unlink(missing_ok=True)


@pytest.fixture()
def fresh_job(stub_profile):
    """Scrape a fresh tuberlin job, yield (source, job_id), delete data/jobs after test."""
    import asyncio
    from src.scraper.main import build_providers
    from src.core.data_manager import DataManager

    dm = DataManager()
    adapter = build_providers(dm)["tuberlin"]
    job_ids = asyncio.run(
        adapter.run(already_scraped=[], source="tuberlin", limit=1, drop_repeated=False, overwrite=True)
    )
    assert job_ids, "Scraper returned no jobs — check network or tuberlin availability"
    yield "tuberlin", job_ids[0]

    shutil.rmtree("data/jobs/tuberlin", ignore_errors=True)


@pytest.mark.e2e
@pytest.mark.skipif(not _server_available(), reason="LangGraph server not running on port 8124")
class TestFullPipelineE2E:
    """Full pipeline e2e: scrape → translate → match (auto-approve) → generate → render → package."""

    def test_scrape_produces_ingest_artifact(self, fresh_job):
        source, job_id = fresh_job
        state_file = Path(f"data/jobs/{source}/{job_id}/nodes/ingest/proposed/state.json")
        assert state_file.exists(), f"Ingest artifact missing: {state_file}"
        data = json.loads(state_file.read_text())
        assert data.get("job_title"), "Ingest state has no job_title"
        assert data.get("original_language"), "Ingest state has no original_language"

    def test_translate_produces_artifact(self, fresh_job):
        from src.core.tools.translator.main import translate_single_job, PROVIDERS
        from src.core.data_manager import DataManager

        source, job_id = fresh_job
        dm = DataManager()
        translate_single_job(dm, PROVIDERS["google"], source, job_id)

        out = Path(f"data/jobs/{source}/{job_id}/nodes/translate/proposed/state.json")
        assert out.exists(), f"Translate artifact missing: {out}"
        data = json.loads(out.read_text())
        assert data.get("original_language") == "en", "Translated state language not set to 'en'"

    def test_full_pipeline_reaches_completed(self, fresh_job):
        """Full pipeline with auto-approve must reach status=completed and produce a manifest."""
        from src.core.tools.translator.main import translate_single_job, PROVIDERS
        from src.core.data_manager import DataManager
        from src.core.api_client import LangGraphAPIClient

        source, job_id = fresh_job

        # Pre-translate
        dm = DataManager()
        translate_single_job(dm, PROVIDERS["google"], source, job_id)

        # Run pipeline with auto-approve
        async def _run():
            client = LangGraphAPIClient(SERVER_URL)
            return await client.invoke_pipeline(
                source=source,
                job_id=job_id,
                initial_input={"auto_approve_review": True},
            )

        result = asyncio.run(_run())

        # Check final pipeline status
        thread_id = LangGraphAPIClient.thread_id_for(source, job_id)
        r = httpx.get(f"{SERVER_URL}/threads/{thread_id}/state")
        state_values = r.json().get("values", {})
        final_status = state_values.get("status")

        assert final_status == "completed", (
            f"Pipeline did not complete. status={final_status!r}, "
            f"error_state={state_values.get('error_state')}"
        )

    def test_all_stage_artifacts_present(self, fresh_job):
        """After a completed pipeline run, every stage must have written its expected artifact."""
        from src.core.tools.translator.main import translate_single_job, PROVIDERS
        from src.core.data_manager import DataManager
        from src.core.api_client import LangGraphAPIClient

        source, job_id = fresh_job
        dm = DataManager()
        translate_single_job(dm, PROVIDERS["google"], source, job_id)

        async def _run():
            client = LangGraphAPIClient(SERVER_URL)
            return await client.invoke_pipeline(
                source=source,
                job_id=job_id,
                initial_input={"auto_approve_review": True},
            )

        asyncio.run(_run())

        base = Path(f"data/jobs/{source}/{job_id}/nodes")
        expected = {
            "ingest":            base / "ingest/proposed/state.json",
            "translate":         base / "translate/proposed/state.json",
            "extract_bridge":    base / "extract_bridge/proposed/state.json",
            "load_profile":      base / "pipeline_inputs/proposed/profile_evidence.json",
            "match_skill":       base / "match_skill/approved/state.json",
            "generate_documents_cv":     base / "generate_documents/proposed/cv.md",
            "generate_documents_letter": base / "generate_documents/proposed/cover_letter.md",
            "render_cv":         base / "render/proposed",
            "package_manifest":  base / "package/final/manifest.json",
        }

        missing = [name for name, path in expected.items() if not path.exists()]
        assert not missing, f"Missing artifacts after completed run: {missing}"

    def test_package_manifest_references_valid_files(self, fresh_job):
        """The final manifest must list files that actually exist on disk."""
        from src.core.tools.translator.main import translate_single_job, PROVIDERS
        from src.core.data_manager import DataManager
        from src.core.api_client import LangGraphAPIClient

        source, job_id = fresh_job
        dm = DataManager()
        translate_single_job(dm, PROVIDERS["google"], source, job_id)

        async def _run():
            client = LangGraphAPIClient(SERVER_URL)
            return await client.invoke_pipeline(
                source=source,
                job_id=job_id,
                initial_input={"auto_approve_review": True},
            )

        asyncio.run(_run())

        manifest_path = Path(f"data/jobs/{source}/{job_id}/nodes/package/final/manifest.json")
        assert manifest_path.exists(), "manifest.json not written"

        manifest = json.loads(manifest_path.read_text())
        artifacts = manifest.get("artifacts", {})
        assert artifacts, "Manifest has no artifacts"

        missing_files = [
            ref for ref in artifacts.values()
            if not Path(ref).exists()
        ]
        assert not missing_files, f"Manifest references files that do not exist: {missing_files}"
```

- [ ] **Step 3: Run e2e tests (expect failures if server not running)**

```bash
python -m pytest tests/e2e/test_pipeline.py -v -m e2e 2>&1 | tail -30
```

If server is running: all 5 tests should PASS for a full-pipeline run.
If server is not running: all `TestFullPipelineE2E` tests are skipped — expected.

- [ ] **Step 4: Verify no other tests broken**

```bash
python -m pytest tests/ -q --ignore=tests/e2e
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add tests/e2e/test_pipeline.py tests/e2e/fixtures/stub_profile.json
git commit -m "test: add full e2e test covering scrape→translate→match→generate→render→package"
```
