# CLI Module

Current role: operator entrypoints for running and resuming workflow components.

## Main commands in this workspace

- `python -m src.cli.run_prep_match ...`
- `python -m src.cli.run_prep_match --resume ...`
- `python -m src.cli.run_review_api`
- `python -m src.cli.bootstrap_neo4j_schema`
- `python -m src.cli.check_repo_protocol`
- `python -m src.cli.propagate_protocol_pack`
- `./scripts/dev.sh` — starts both UI + API in one terminal (Ctrl+C stops both)
- `./scripts/dev-all.sh` — starts Neo4j + API + UI and bootstraps Neo4j schema

## Current status

- CLI surface is mixed between legacy and new ADR-001 scaffold commands.
- Resume behavior relies on deterministic review artifacts and checkpoint state.
