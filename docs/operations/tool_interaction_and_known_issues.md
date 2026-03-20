# Tool Interaction and Known Issues

## Purpose

This guide describes how to operate the current PhD 2.0 toolchain in a human-in-the-loop workflow and how to handle common failure modes.

Use this as the practical operator playbook for what is actually runnable in this repo.

## Interaction model

The operator controls progression. The tool does not auto-approve review gates.

Standard loop:

1. Run the prep-match flow for one job.
2. Inspect generated artifacts.
3. Edit review decisions where needed.
4. Resume execution.
5. Inspect final packaged outputs.

## Current command surface

The runnable operator commands in this workspace are Python module entrypoints, not `phd2 ...` aliases.

Primary flow:

- `python -m src.cli.run_prep_match --source <source> --job-id <id> --source-url <url> --profile-evidence <json-path>`
- `python -m src.cli.run_prep_match --source <source> --job-id <id> --resume`

Supporting tools:

- `python -m src.cli.run_scrape_probe --source <source> --url <url> --mode detail`
- `python -m src.cli.run_scrape_probe --source <source> --url <listing_url> --mode listing --max-pages <n>`
- `python -m src.cli.run_stepstone_autoapply --job-url <url> [--apply]`

Do not assume `phd2 run`, `phd2 review-validate`, `phd2 graph-status`, or other alias commands exist in this repo unless they are added explicitly.

## Control-plane resume contract (LangGraph)

Execution identity rule:

- LangGraph `thread_id` is always `f"{source}_{job_id}"`.

### Resume (`run_prep_match --resume`)

`run_prep_match --resume` wakes the graph from checkpoint state.

Flow:

1. compile graph with persistent checkpointer,
2. set runtime config:

```python
config = {"configurable": {"thread_id": f"{source}_{job_id}"}}
```

3. resume from interrupt with empty invocation:

```python
graph.invoke(None, config)
```

When resumed, LangGraph executes the next pending review node (`review_match` in the current prep flow).
That review node reads and parses `nodes/match/review/decision.md`, writes `decision.json` as a runtime artifact, and emits routing such as `{"review_decision": "approve"}`.

Non-negotiable rule:

- CLI never injects human decisions directly into LangGraph state.
- Resume wakes graph execution; `review_match` remains the deterministic parser/validator.

## Current review gate reality

The current runnable prep flow has one active semantic review gate:

- `review_match`

The broader multi-stage review architecture in planning docs is not yet the operator-facing flow in `run_prep_match`.

## Typical operator session

Initial run:

```bash
python -m src.cli.run_prep_match \
  --source <source> \
  --job-id <job_id> \
  --source-url <url> \
  --profile-evidence <path_to_json>
```

Edit review markdown:

- `data/jobs/<source>/<job_id>/nodes/match/review/decision.md`

Resume:

```bash
python -m src.cli.run_prep_match --source <source> --job-id <job_id> --resume
```

Repeat until route is `approve` or `reject` and the flow reaches `package`.

## Minimum artifact checks per run

At each pause or completion, verify:

1. the node just executed wrote its expected state/artifact files,
2. `match` review flow includes `nodes/match/review/decision.md`,
3. `render` wrote `nodes/render/approved/state.json`,
4. `package` wrote `final/*.md` and `final/manifest.json`,
5. `graph/run_summary.json` reflects the latest run status.

## Output inspection checklist

Use this checklist on every run:

1. Required files exist in expected directories.
2. Review markdown is parseable and unambiguous.
3. Final markdown outputs are job-specific and not generic placeholders.
4. `final/manifest.json` hashes match the delivered files.
5. `graph/run_summary.json` status matches the observed end state.

## Known issues and troubleshooting

## 1) Stale review hash mismatch

Symptoms:

- resume fails with a source hash mismatch error.

Cause:

- `decision.md` was generated from an older `nodes/match/approved/state.json`.

Fix:

1. regenerate or let `review_match` regenerate the current review markdown,
2. re-apply review decisions,
3. resume again.

## 2) Ambiguous or invalid decision markup

Symptoms:

- parser error about multiple or missing marked decisions.

Cause:

- more than one option marked, or no option marked in a requirement row/block.

Fix:

1. mark exactly one decision per actionable row/block,
2. avoid changing the checkbox token labels,
3. resume again.

## 3) Hidden fallback behavior or low-quality generation

Symptoms:

- outputs are repetitive, generic, or still contain placeholders.

Cause:

- prompt/runtime quality issues or insufficient grounding, even when the graph run itself succeeds.

Fix:

1. inspect `nodes/generate_documents/approved/state.json` and generated markdown,
2. verify the approved matches are sensible,
3. tighten prompt or deterministic post-check logic rather than masking the issue.

## 4) Translation dependency or provider issues

Symptoms:

- translation node fails or long input translation breaks.

Cause:

- missing dependency, provider failure, or long input edge cases.

Fix:

1. verify environment dependencies,
2. rerun the deterministic translation tests,
3. inspect `raw/language_check.json` and `nodes/translate_if_needed/approved/state.json` when present.

## 5) Missing Gemini credentials

Symptoms:

- LLM nodes fail before or during `extract_understand`, `match`, or `generate_documents`.

Cause:

- missing or invalid `GOOGLE_API_KEY` / Gemini credentials.

Fix:

1. configure the API key in local environment or `.env`,
2. rerun the job,
3. confirm the run advances beyond the previous failure node.
