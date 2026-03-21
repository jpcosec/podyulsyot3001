# PhD 2.0 (Rebuild Workspace)

This repository is the active rebuild track for the PhD application pipeline.

## What the project is

PhD 2.0 is a graph-driven pipeline that turns a job posting plus candidate profile evidence into application artifacts with explicit human review at semantic gates.

Today, the repo contains both:

- current runnable pipeline code, and
- target-state / planning documentation for a larger architecture still in progress.

Use the docs marked as current runtime truth when you need to know what actually runs.

## Current runnable flow

The operator-facing runnable graph today is the prep-match flow in `src/graph.py`:

`scrape -> translate_if_needed -> extract_understand -> match -> review_match -> generate_documents -> render -> package`

Current review routing:

- `approve` -> `generate_documents`
- `request_regeneration` -> `match`
- `reject` -> end

The main CLI entrypoint is:

```bash
python -m src.cli.run_prep_match \
  --source <source> \
  --job-id <job_id> \
  --source-url <url> \
  --profile-evidence <path>
```

Resume form:

```bash
python -m src.cli.run_prep_match --source <source> --job-id <job_id> --resume
```

Helpful support CLIs:

- `python -m src.cli.run_scrape_probe ...`
- `python -m src.cli.run_stepstone_autoapply ...`

## Repository structure

- `src/core/` - deterministic services, contracts, review parsing, workspace I/O, provenance, scraping facade, render/package helpers
- `src/ai/` - LLM runtime and prompt manager
- `src/nodes/` - graph node packages
- `src/cli/` - operator CLI entrypoints
- `src/interfaces/api/` - API/server-side interface work
- `src/graph.py` - LangGraph assembly and prep-match app wiring

## What is current vs planned

- Current runtime truth lives primarily in:
  - `docs/runtime/graph_flow.md`
  - `docs/runtime/node_io_matrix.md`
  - `docs/runtime/data_management.md`
  - `docs/operations/tool_interaction_and_known_issues.md`
  - `docs/index/canonical_map.md`
- Planning, migration, ADR, and target-state design docs live under `plan/`
- Heavy subsystem implementation docs live close to code under `src/**/README.md` and `apps/**/README.md`

Do not assume every architecture or plan doc describes current runtime behavior.

## Documentation index

Start here:

- `docs/index/README.md`
- `docs/index/canonical_map.md`

## Common commands

Install Python runtime dependencies:

```bash
python -m pip install -r requirements.txt
```

Run all tests:

```bash
python -m pytest tests/ -q
```

Run a focused slice:

```bash
python -m pytest tests/core/scraping -q
python -m pytest tests/nodes/review_match -q
python -m pytest tests/nodes/render tests/nodes/package -q
```

Start local dev stack:

```bash
./scripts/dev-all.sh
```

This starts the minimal local JSON mode by default (UI + API, no Neo4j).

If you explicitly need the legacy Neo4j sidecar:

```bash
START_NEO4J=1 ./scripts/dev-all.sh
```

## Core principles

1. Deterministic correctness before semantic trust.
2. No silent fallback-to-success paths.
3. Human review is required for semantic acceptance.
4. Current runtime and target-state plans must be documented separately.
5. Major documentation changes belong in `changelog.md`.

## Documentation hygiene

- Keep cross-cutting docs under `docs/`
- Keep planning and migration material under `plan/`
- Mark target-state and historical docs clearly when they are not current runtime truth
