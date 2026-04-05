# Browser Automation Worktree

This worktree is intentionally narrowed to one issue: the browser automation pipeline. It keeps only the code and docs needed to iterate on scraping, portal-specific application flows, and BrowserOS-backed automation.

---

## Scope

This worktree currently contains:

- `src/scraper/` - job discovery and portal ingestion helpers
- `src/apply/` - automated application flows, provider adapters, BrowserOS integration, and playbooks
- `plan_docs/automation/` - focused planning docs for the browser automation refactor
- `docs/standards/` - cross-cutting documentation standards that still apply to this scoped worktree

Missing modules from the fuller repository are intentionally out of scope here unless the browser automation issue directly needs them.

---

## Configuration

The worktree still uses a root `.env` file for runtime secrets and environment setup.

### Common Environment Variables
```env
PLAYWRIGHT_BROWSERS_PATH="0"
GOOGLE_API_KEY="your_gemini_key"
GEMINI_API_KEY="your_gemini_key"
```

---

## CLI / Usage

This worktree exposes module-local CLIs rather than the old unified control plane.

Primary entry points:

- `python -m src.scraper.main --source stepstone --limit 5` - ingest jobs from a source
- `python -m src.apply.main --source xing --job-id 12345 --cv path/to/cv.pdf --dry-run` - exercise an application flow without submitting
- `python -m src.apply.main --backend browseros --source linkedin --setup-session` - prepare a BrowserOS-backed session

---

## Data Contract

The active contracts in this worktree are centered on scraping and applying:

- `src/scraper/models.py` - validated job posting and ingestion-facing models
- `src/apply/models.py` - apply-time contracts and status records
- runtime artifacts under `data/jobs/<source>/<job_id>/...` for job-specific automation state

---

## How to Add / Extend

1. Add new portal scraping logic under `src/scraper/providers/`.
2. Add new application behavior under `src/apply/providers/` or `src/apply/playbooks/`.
3. Keep BrowserOS-specific integration inside `src/apply/` unless a broader automation abstraction is actually implemented.
4. Update `plan_docs/automation/` when the browser automation design changes materially.
5. Record major scoped changes in `changelog.md`.

---

## How to Use

```bash
# Scrape a few jobs
python -m src.scraper.main --source stepstone --limit 3

# Prepare a session for a portal
python -m src.apply.main --source xing --setup-session

# Run a dry application flow
python -m src.apply.main --source xing --job-id 12345 --cv path/to/cv.pdf --dry-run
```

Module-specific documentation:

- `src/scraper/README.md`
- `src/apply/README.md`
- `plan_docs/automation/README.md`

---

## Troubleshooting

- `src.apply.main` fails before portal actions begin -> run the relevant `--setup-session` flow first.
- Browser automation behaves differently across portals -> inspect the provider adapter or playbook under `src/apply/providers/` or `src/apply/playbooks/`.
- Scrape output is missing application fields -> check the source adapter under `src/scraper/providers/` and keep fixes scoped to automation inputs.
