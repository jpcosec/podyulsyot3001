# src/apply — Auto-Application Module

Standalone CLI module for automated job application via XING Easy Apply and StepStone Easy Apply.

Reads from an existing ingested job artifact, fills and submits the application form using a persistent browser session.

**Spec:** `docs/superpowers/specs/2026-03-30-apply-module-design.md`

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
