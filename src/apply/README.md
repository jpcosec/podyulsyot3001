# src/apply — Auto-Application Module

This document provides a guide for developing and extending the `apply` module. It covers the architectural principles and the practical usage of the module.

---

## 1. Architectural Principles

This module is built on LangGraph and follows a set of principles to ensure that it is maintainable, testable, and robust.

### 1.1. Implementation Sequence

When adding new features or extending existing ones, follow this sequence. Each step should produce something verifiable before the next begins.

1.  **Define Contracts:** Start by defining the data contracts (e.g., Pydantic models) for your inputs, outputs, and any intermediate data structures. This ensures that all parts of your feature communicate correctly.
2.  **Build Persistence:** Define how your feature will read and write artifacts. The module uses a centralized persistence layer that writes to `data/jobs/<source>/<job_id>/...`.
3.  **Construct Logics:** Implement the core logic of your feature. This could be in the form of prompts for an LLM, or business logic in Python.
4.  **Build the Graph:** Once the individual components are ready, wire them together in a LangGraph graph.
5.  **Add a CLI entrypoint:** Expose your feature through the module's CLI in `main.py`.

### 1.2. Node Taxonomy

Every node in the LangGraph graph should have a clear responsibility. Name your nodes according to their function:

| Type | Responsibility | Rules |
|---|---|---|
| **Input validation** (`load_*`) | Validate and normalize state inputs, merge prior artifacts | Fail fast — raise if required inputs are missing |
| **LLM boundary** (`run_*_llm`) | Build prompt variables, invoke chain, validate output | Only place that calls the model. No disk I/O. |
| **Persistence** (`persist_*`) | Write artifacts, compute hashes, return refs into state | No business logic. Use the central data manager. |
| **Breakpoint anchor** (`*_review_node`) | Pause the graph for human input | Intentionally thin — exists only as an interrupt target |
| **Review/routing** (`apply_*`) | Validate review payload, hash-check, route based on decision | Hash validation is mandatory. |
| **Context prep** (`prepare_*`) | Prepare the data for the next step in the graph. | Must confirm routing condition before executing. |

### 1.3. Graph State

The `GraphState` (a TypedDict) should only carry routing signals and references to artifacts, not the full payloads. Heavy payloads should be written to disk by a persistence node and reloaded by the nodes that need them. The state is the routing bus, not the data bus.

### 1.4. Test Coverage

All new features must be accompanied by tests. The minimum test coverage for any graph-based feature is:

-   **Approve flow**: The graph runs, pauses for review (if applicable), resumes with approval, and completes successfully.
-   **Regeneration flow**: A review requests regeneration, and the graph correctly prepares the context and runs the relevant part of the graph again.
-   **Rejection flow**: A review rejects the output, and the graph ends cleanly.

---

## 2. Usage

### 2.1. First-time session setup (run once per portal/backend)

```bash
python -m src.apply.main --source xing --setup-session
python -m src.apply.main --source stepstone --setup-session
python -m src.apply.main --backend browseros --source linkedin --setup-session
```

For Crawl4AI portals, this opens a visible browser at the portal URL. Log in manually, then press Enter. Session cookies are saved to `data/profiles/<portal>_profile/` and reused headlessly on all subsequent runs.

For BrowserOS, the session setup opens the portal in BrowserOS and waits for manual login confirmation.

### 2.2. Apply to a job

```bash
# Dry-run (fills form, takes screenshot, does NOT submit)
python -m src.apply.main 
  --source xing 
  --job-id 12345 
  --cv path/to/cv.pdf 
  --dry-run

# BrowserOS dry-run for LinkedIn
python -m src.apply.main 
  --backend browseros 
  --source linkedin 
  --job-id 12345 
  --cv path/to/cv.pdf 
  --profile-json path/to/profile.json 
  --dry-run

# Auto mode (submits the application)
python -m src.apply.main 
  --source xing 
  --job-id 12345 
  --cv path/to/cv.pdf 
  --letter path/to/letter.pdf
```

The `--job-id` must match an already-ingested job under the job runtime folder. The module reads the ingest-stage `state.json` artifact to get `application_url`, `job_title`, and `company_name`.

Backend selection lives in `build_parser()` in `src/apply/main.py`.

### 2.3. Check apply status

```bash
cat data/jobs/xing/12345/nodes/apply/meta/apply_meta.json
```

---

## 3. Idempotency

| Prior status | Behaviour |
|---|---|
| `submitted` | Blocked — application already sent |
| `dry_run` | Allowed — dry-run artifacts overwritten |
| `failed` | Allowed — retry |
| `portal_changed` | Allowed — retry after fixing selectors |
| missing | Allowed — first run |

---

## 4. Artifacts

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

## 5. When the portal changes

If a portal updates its DOM or BrowserOS snapshots stop matching the expected path, the run writes `apply_meta.json` with `status=portal_changed`.

Fix process:
1. Capture fresh portal evidence or BrowserOS snapshots
2. Compare against the current adapter selectors or Ariadne-style path
3. Update the relevant adapter or playbook in `src/apply/`
4. Re-run the matching apply tests under `tests/test_apply_*`

---

## 6. Adding a new portal

1. Decide whether the new source is implemented through Crawl4AI, BrowserOS, or both.
2. For Crawl4AI, add a provider under `src/apply/providers/<name>/` and extend `ApplyAdapter`.
3. For BrowserOS, add or package a normalized playbook under `src/apply/playbooks/` and wire it in `src/apply/browseros_backend.py`.
4. Add tests under `tests/test_apply_*`.
5. Register the source/backend in `src/apply/main.py`.
