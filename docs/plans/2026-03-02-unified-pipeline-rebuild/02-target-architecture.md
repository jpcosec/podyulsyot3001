# Target Architecture (Unified LangGraph Pipeline)

Date: 2026-03-02
Decision: hard-break rebuild with one orchestrator

## 1) Design Goals

1. One orchestration path for proposal + CV + letter + email.
2. One LLM call template for every generative step.
3. One state model persisted after each node.
4. Deterministic rendering and extraction remain untouched at engine level.
5. Resume/retry without rerunning completed nodes.

## 2) Package Layout

Planned package:

`src/unified_pipeline/`

- `state.py`
  - `ApplicationState`
  - node status map
  - artifacts registry
  - run metadata (budget, retries, prompt fingerprints)
- `contracts.py`
  - node I/O contracts built from `src/models/*.py`
- `llm/template.py`
  - single LLM executor
- `llm/errors.py`
  - normalized errors (`LLMRateLimitError`, `LLMParseError`, etc.)
- `nodes/`
  - `ingest.py`
  - `context.py`
  - `match.py`
  - `gap.py`
  - `proposal.py`
  - `review_gate.py`
  - `render_cv.py`
  - `motivation.py`
  - `email.py`
  - `report.py`
- `checkpoints.py`
  - load/save state snapshots
- `graph.py`
  - LangGraph assembly and transition policy
- `runner.py`
  - programmatic entrypoint

## 3) LLM Template Contract

`template.py` should expose one function:

```python
def call_llm(
    *,
    prompt_name: str,
    context: dict,
    output_model: type[BaseModel],
    run_state: ApplicationState,
    temperature: float | None = None,
    max_retries: int = 2,
) -> BaseModel:
    ...
```

Responsibilities:

- load prompt via `load_prompt_with_context` or `load_prompt`
- serialize context deterministically
- call `GeminiClient.generate`
- extract JSON object safely
- validate with `output_model.model_validate(...)`
- retry on parse/transient failures
- account call budget and call count
- write telemetry event to run log

Hard rule:

- No module outside `llm/template.py` may parse raw model text.

## 4) State and Checkpoint Model

`ApplicationState` minimum fields:

- `run_id`
- `job_id`
- `source`
- `phase`
- `job_posting` (`JobPosting | None`)
- `evidence_items`
- `requirement_mapping`
- `proposed_claims`
- `approved_claims`
- `cv_artifacts`
- `motivation_artifacts`
- `email_artifacts`
- `reports`
- `node_status` (`pending|running|completed|failed|blocked`)
- `call_budget` / `calls_used`
- `errors`

Checkpoint persistence:

- Save JSON snapshot after every node:
  - `data/pipelined_data/<source>/<job_id>/output/unified/checkpoints/<step>.json`
- Save one rolling latest pointer:
  - `.../output/unified/checkpoints/latest.json`

## 5) Node Contracts

### Deterministic nodes

- `ingest`: scrape/normalize and load job tracker data
- `context`: build candidate+job context from deterministic sources
- `render_cv`: compile approved claims with deterministic renderer
- `report`: ATS extraction and run report packaging

### LLM nodes

- `match`: requirement-to-evidence mapping
- `gap`: missing evidence and risk proposals
- `proposal`: final approved proposal draft set
- `motivation`: final letter
- `email`: application email

### Human gate node

- `review_gate`: blocks downstream generation unless explicit approval exists

## 6) LangGraph Wiring

Expected graph characteristics:

- Directed acyclic path for deterministic order.
- Conditional edge at review gate.
- Resume starts from latest non-completed node.
- Rate-limit errors route to retry with capped attempts.

## 7) CLI Surface (Unified)

New commands:

- `python src/cli/pipeline.py unified-run <job_id> --source <source>`
- `python src/cli/pipeline.py unified-phase <job_id> --from match --to proposal`
- `python src/cli/pipeline.py unified-review <job_id> --approve`
- `python src/cli/pipeline.py unified-resume <job_id>`

Compatibility policy:

- Legacy commands are removed or turned into thin aliases to unified commands.

## 8) Migration Notes

Artifact root:

- New: `output/unified/` as canonical run root.
- Legacy outputs may remain for historical inspection but are no longer produced.

Documentation alignment:

- Update `README.md` and pipeline deep-dive after implementation.
