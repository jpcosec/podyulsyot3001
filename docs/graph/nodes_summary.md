# Graph Flow and Node Summary (Current State)

## Purpose

Describe only the runnable graph behavior in the current codebase.

Forward-looking topology is tracked under `plan/spec/`.

## Executable entrypoints

- Runtime path: `create_prep_match_app()` in `src/graph.py`
- Operator entrypoint: `python -m src.cli.run_prep_match`

## Current flow and routing

Linear path:

1. `scrape`
2. `translate_if_needed`
3. `extract_understand`
4. `match`
5. `review_match`
6. `generate_documents`
7. `package`

Review routing in `review_match`:

- `approve` -> `generate_documents` -> `package`
- `request_regeneration` -> `match`
- `reject` -> stop

`package` in this prep graph is a terminal status node, not the full delivery packager.

## Checkpoint/resume behavior

- `thread_id` is `f"{source}_{job_id}"`.
- Checkpoint path: `data/jobs/<source>/<job_id>/graph/checkpoint.sqlite`.
- Resume with `--resume` restores checkpointed review context.

## Node roles

- `scrape` (`NLLM-ND`): fetches URL and builds ingested payload in state.
- `translate_if_needed` (`NLLM-ND`): conditionally normalizes language.
- `extract_understand` (`LLM`): produces structured extraction output.
- `match` (`LLM`): writes match proposal + review artifacts.
- `review_match` (`NLLM-D`): deterministic decision parser and route switch.
- `generate_documents` (`LLM` + deterministic rendering): writes CV/letter/email proposals and assist artifacts.
- `package` (`NLLM-D`): marks prep run completed.

## Planning pointer

Target full-graph topology and staged rollout are maintained in:

- `plan/spec/node_io_target_matrix.md`
- `plan/adr/adr_001_ui_first_knowledge_graph_langchain.md`
