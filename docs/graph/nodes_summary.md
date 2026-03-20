# Graph Flow and Node Summary (Current State)

## Purpose

Describe only the runnable graph behavior in the current codebase.

Forward-looking topology is tracked under `plan/spec/` and other planning docs.

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
7. `render`
8. `package`

Review routing in `review_match`:

- `approve` -> `generate_documents` -> `render` -> `package`
- `request_regeneration` -> `match`
- `reject` -> stop

`package` is now a real terminal delivery step for the current prep flow: it validates `render` output refs and writes final markdown deliverables plus `final/manifest.json`.

## Checkpoint/resume behavior

- `thread_id` is `f"{source}_{job_id}"`.
- Checkpoint path: `data/jobs/<source>/<job_id>/graph/checkpoint.sqlite`.
- Resume with `--resume` restores checkpointed review context.

## Node roles

- `scrape` (`NLLM-ND`): fetches URL and produces canonical scrape artifacts plus compatible ingested payload in state.
- `translate_if_needed` (`NLLM-ND`): conditionally normalizes language.
- `extract_understand` (`LLM`): produces structured extraction output.
- `match` (`LLM`): writes match proposal + review artifacts.
- `review_match` (`NLLM-D`): deterministic decision parser and route switch.
- `generate_documents` (`LLM` + deterministic rendering): writes CV/letter/email proposals and assist artifacts.
- `render` (`NLLM-D`): copies generated markdown into `nodes/render/proposed/` and records approved render refs with hashes.
- `package` (`NLLM-D`): validates rendered content hashes, writes `final/*.md` plus `final/manifest.json`, and marks run completed.

## Planning pointer

Target full-graph topology and staged rollout are maintained in planning docs under `plan/`.
