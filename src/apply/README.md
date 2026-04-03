# src/apply — Auto-Application Module

Standalone CLI module for automated job application using Crawl4AI and BrowserOS-backed flows.

Reads from existing ingested job artifacts and runs portal-specific application flows through a shared apply CLI.

---

## Usage

### First-time session setup (run once per portal/backend)

```bash
python -m src.apply.main --source xing --setup-session
python -m src.apply.main --source stepstone --setup-session
python -m src.apply.main --backend browseros --source linkedin --setup-session
```

For Crawl4AI portals, this opens a visible browser at the portal URL. Log in manually, then press Enter. Session cookies are saved to `data/profiles/<portal>_profile/` and reused headlessly on all subsequent runs.

For BrowserOS, the session setup opens the portal in BrowserOS and waits for manual login confirmation.

### Apply to a job

```bash
# Dry-run (fills form, takes screenshot, does NOT submit)
python -m src.apply.main \
  --source xing \
  --job-id 12345 \
  --cv path/to/cv.pdf \
  --dry-run

# BrowserOS dry-run for LinkedIn
python -m src.apply.main \
  --backend browseros \
  --source linkedin \
  --job-id 12345 \
  --cv path/to/cv.pdf \
  --profile-json path/to/profile.json \
  --dry-run

# Auto mode (submits the application)
python -m src.apply.main \
  --source xing \
  --job-id 12345 \
  --cv path/to/cv.pdf \
  --letter path/to/letter.pdf
```

The `--job-id` must match an already-ingested job under the job runtime folder. The module reads the ingest-stage `state.json` artifact to get `application_url`, `job_title`, and `company_name`.

Backend selection lives in `build_parser()` in `src/apply/main.py`.

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

If a portal updates its DOM or BrowserOS snapshots stop matching the expected path, the run writes `apply_meta.json` with `status=portal_changed`.

Fix process:
1. Capture fresh portal evidence or BrowserOS snapshots
2. Compare against the current adapter selectors or Ariadne-style path
3. Update the relevant adapter or playbook in `src/apply/`
4. Re-run the matching apply tests under `tests/test_apply_*`

---

## Adding a new portal

1. Decide whether the new source is implemented through Crawl4AI, BrowserOS, or both.
2. For Crawl4AI, add a provider under `src/apply/providers/<name>/` and extend `ApplyAdapter`.
3. For BrowserOS, add or package a normalized playbook under `src/apply/playbooks/` and wire it in `src/apply/browseros_backend.py`.
4. Add tests under `tests/test_apply_*`.
5. Register the source/backend in `src/apply/main.py`.
