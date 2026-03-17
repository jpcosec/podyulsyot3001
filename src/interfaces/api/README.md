# Review API Module

Current-state documentation for the UI review API.

## Purpose

Expose review workbench read surfaces for portfolio, per-job timeline, and view payloads.

## Entrypoints

- App factory: `src/interfaces/api/app.py`
- CLI runner: `src/cli/run_review_api.py`
- Settings: `src/interfaces/api/config.py`

## Routers

- `routers/health.py`
  - `GET /health`
- `routers/portfolio.py`
  - `GET /api/v1/portfolio/summary`
- `routers/jobs.py`
  - `GET /api/v1/jobs/{source}/{job_id}/timeline`
  - `GET /api/v1/jobs/{source}/{job_id}/review/match`
  - `GET /api/v1/jobs/{source}/{job_id}/view1`
  - `GET /api/v1/jobs/{source}/{job_id}/view2`
  - `GET /api/v1/jobs/{source}/{job_id}/view3`
- `routers/neo4j.py`
  - `GET /api/v1/neo4j/health`
  - `POST /api/v1/neo4j/bootstrap-schema`

## Data Source

Current implementation is filesystem-backed via `read_models.py`.

- Reads job artifacts from `PHD2_DATA_ROOT` (default `data/jobs`)
- Builds UI payloads from approved/proposed node artifacts

Neo4j integration currently covers health and schema bootstrap only.

## Verification

- Tests: `python -m pytest tests/interfaces/api -q`
- Local run: `python -m src.cli.run_review_api`

## Known Gaps

1. No write endpoints yet (read-only API).
2. No API-driven review decision submission flow.
3. No Neo4j-backed read models for View 1/2/3 yet.
