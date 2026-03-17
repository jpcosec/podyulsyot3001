# UI Workbench Phase 0 Bootstrap

## Start Neo4j

```bash
docker compose -f docker-compose.neo4j.yml up -d
```

## Start everything (API + UI)

```bash
./scripts/dev.sh
```

Opens UI at `http://127.0.0.1:4173` and API at `http://127.0.0.1:8010`. Ctrl+C stops both.

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
