# UI Workbench Phase 0 Bootstrap

## Start everything (Neo4j + API + UI)

```bash
./scripts/dev-all.sh
```

Opens (or the next free ports if these are busy):

- UI: `http://127.0.0.1:4173`
- API: `http://127.0.0.1:8010`
- Neo4j Browser: `http://127.0.0.1:7474`

Ctrl+C stops UI/API. Set `STOP_NEO4J_ON_EXIT=1` if you also want Docker to stop when exiting.

## Start only API + UI (keep Neo4j manual)

```bash
./scripts/dev.sh
```

Opens UI at `http://127.0.0.1:4173` and API at `http://127.0.0.1:8010`.

### Or start separately

```bash
# API only
python -m src.cli.run_review_api

# UI only
npm --prefix apps/review-workbench install
npm --prefix apps/review-workbench run dev
```

## Quick checks

```bash
curl http://127.0.0.1:8010/health
curl http://127.0.0.1:8010/api/v1/portfolio/summary
curl http://127.0.0.1:8010/api/v1/neo4j/health
```
