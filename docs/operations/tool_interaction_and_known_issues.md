# Tool Interaction and Known Issues

## Purpose

This guide describes how to operate the PhD 2.0 toolchain in a human-in-the-loop (HITL) workflow, and how to handle common failure modes.

Use this as the practical operator playbook.

## Interaction model

The operator controls progression. The tool does not auto-approve review gates.

Standard loop:

1. Run graph or node command for one job.
2. Inspect proposed artifacts.
3. Edit review decisions where needed.
4. Validate review decisions.
5. Resume execution or stop.

## Expected command surface

Command names below define the expected operator surface:

- `phd2 scrape-url ...` - scrape and store raw artifacts for one job.
- `phd2 scrape-listing ...` - crawl listing and scrape new jobs.
- `phd2 run --source <source> --job-id <id> --until-node <node>` - run graph until a node.
- `phd2 run --source <source> --job-id <id> --resume` - resume from review interrupt.
- `phd2 node-run --source <source> --job-id <id> --node <node>` - run one node directly.
- `phd2 review-validate --source <source> --job-id <id> --node <node>` - parse and validate review markdown.
- `phd2 graph-status --source <source> --job-id <id>` - show pending gate and progress.

If a command is unavailable in your current branch, use the documented equivalent and record the deviation in incident notes.

## Control Plane resume contract (LangGraph)

This section specifies how CLI commands interact with review interrupts.

Execution identity rule:

- LangGraph `thread_id` is always `f"{source}_{job_id}"`.

### A) `phd2 review-validate` (Data Plane only)

`review-validate` does not mutate LangGraph state.

Flow:

1. resolve `proposed/state.json` and `review/decision.md` through `WorkspaceManager`,
2. call `sync_json_md.md_to_json(...)`,
3. fail with actionable parse/hash error if invalid,
4. write `review/decision.json` if valid.

Example failure style:

- `Line 14: multiple decision checkboxes marked`.

### B) `phd2 run --resume` (Control Plane)

`run --resume` wakes the graph from checkpoint state.

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

When resumed, LangGraph executes the next pending review node (for example `review_match`).
That review node reads `review/decision.json` from disk via `ArtifactReader` and emits routing (for example `{"review_decision": "approve"}`).

Non-negotiable rule:

- CLI never injects decision JSON directly into LangGraph state.
- CLI only validates disk artifacts (`review-validate`) and wakes graph execution (`run --resume`).

## Typical operator session

Example flow for a single job:

1. Prepare source artifacts:
   - `phd2 scrape-url --source <source> --job-url <url>`
2. Run until first review gate:
   - `phd2 run --source <source> --job-id <id>`
3. Inspect and edit review markdown:
   - `nodes/<node>/review/decision.md`
4. Validate review file:
   - `phd2 review-validate --source <source> --job-id <id> --node <node>`
5. Resume:
   - `phd2 run --source <source> --job-id <id> --resume`
6. Repeat until `package` completes.

## Minimum artifact checks per run

At each pause or completion, verify:

1. `proposed/state.json` exists for the node just executed.
2. reviewable nodes also include `proposed/view.md` and `review/decision.md`.
3. approved outputs include `approved/state.json`.
4. critical nodes include `meta/provenance.json`.
5. final stage includes `final/` deliverables and `manifest.json`.

## HITL review workflow

For reviewable nodes, expected artifacts:

- `nodes/<node>/proposed/state.json`
- `nodes/<node>/proposed/view.md`
- `nodes/<node>/review/decision.md`

Operator actions:

1. Open `decision.md`.
2. Mark exactly one decision per requirement block.
3. Add `Notes` only where needed.
4. Run `review-validate`.
5. Resume graph.

Valid decisions are exactly:

- `approve`
- `request_regeneration`
- `reject`

Never edit `source_state_hash` manually. If hash mismatch occurs, regenerate the review file from current proposed state.

## Acceptance policy by node type

Deterministic nodes:

- automated tests required,
- HITL artifact inspection required.

LLM nodes:

- semantic fixtures are not acceptance criteria,
- only HITL review on real jobs can mark semantic readiness.

## Output inspection checklist

Use this checklist on every run:

1. Required files exist in expected directories.
2. JSON artifacts match contract shape.
3. Review markdown is parseable and unambiguous.
4. Provenance exists for approved outputs.
5. Content is job-specific (not generic placeholders).

## Known issues and troubleshooting

## 1) Stale review hash mismatch

Symptoms:

- `review-validate` fails with source hash mismatch.

Cause:

- `decision.md` was generated from an older `proposed/state.json`.

Fix:

1. Regenerate review markdown from current proposed JSON.
2. Re-apply review decisions.
3. Re-run `review-validate`.

## 2) Ambiguous or invalid decision markup

Symptoms:

- parser error about multiple/no marked decisions.

Cause:

- more than one option marked, or no option marked in a requirement block.

Fix:

1. Mark exactly one decision per block.
2. Avoid changing decision token labels.
3. Validate again.

## 3) Hidden fallback behavior (wax regression)

Symptoms:

- generation appears successful despite model/parsing failures,
- outputs are repetitive and generic.

Cause:

- broad exception handling or fallback-to-template path returning success.

Fix:

1. Remove silent fallback-to-success logic.
2. Fail node execution loudly with actionable error.
3. Keep fallback paths explicit and marked as non-success.

## 4) Prompt locality violation

Symptoms:

- prompt files loaded from global prompt module,
- node prompt assets missing.

Cause:

- node uses shared global prompt import instead of local prompt assets.

Fix:

1. Keep prompt assets under each AI node package.
2. Run prompt locality checks.

## 5) Import boundary violations (`core` importing `ai`)

Symptoms:

- architecture lint/check scripts fail.

Cause:

- deterministic layer gained dependency on AI layer.

Fix:

1. Move shared logic to neutral core utilities when deterministic.
2. Keep model-specific code in `src/ai`.

## 6) Translation dependency missing

Symptoms:

- runtime error for translator package import.

Cause:

- optional translation package not installed in environment.

Fix:

1. Install required translation dependency.
2. Re-run deterministic translation checks.

## 7) LLM output parse/schema failure

Symptoms:

- model output cannot be parsed to expected schema.

Cause:

- model returned malformed JSON or wrong fields.

Fix:

1. Ensure strict schema-guided prompting.
2. Add bounded retry policy.
3. If still invalid, fail node and inspect raw model output.

## 8) Resume/checkpoint mismatch

Symptoms:

- resume fails or resumes wrong gate.

Cause:

- stale checkpoint, wrong run id, or manually edited runtime metadata.

Fix:

1. Inspect `runtime/checkpoints/` and graph status.
2. Resume using matching source/job/run context.
3. If inconsistent, restart run for the current step only.

## 9) Rendering toolchain failures

Symptoms:

- render node fails to produce DOCX/PDF.

Cause:

- missing external rendering tools or template/config mismatch.

Fix:

1. Verify renderer dependencies in environment.
2. Validate template paths and input markdown structure.
3. Re-run render on a single job and inspect logs.

## 10) Packaging dependency failures

Symptoms:

- package node fails on merge/compression/hashing.

Cause:

- missing PDF merge/compression dependency or invalid upstream files.

Fix:

1. Verify package dependencies are installed.
2. Confirm render outputs exist and are valid PDFs.
3. Re-run package node with same approved inputs.

## 11) Style drift across node implementations

Symptoms:

- mixed patterns (logic writes files, reader mutates state, inconsistent contracts).

Cause:

- skipping node template discipline.

Fix:

1. Refactor node back to `reader/logic/writer/node` responsibilities.
2. Keep function sizes small and explicit.
3. Add/update architecture checks for drift indicators.

## Incident logging recommendation

For every failure that blocks a step, record:

- step id,
- job id/source,
- failing node,
- command used,
- observed symptom,
- root cause,
- fix applied,
- verification result.

This keeps the rebuild auditable and prevents repeated mistakes.

## Obsidian integration

Review decision files (`review/decision.md`) are designed for editing in Obsidian.

### Why Obsidian

- Raw JSON is not practical for direct human review.
- Markdown decision files provide a natural editing surface with checkboxes, notes, and structured blocks.
- Obsidian's live preview mode works well with YAML front matter and checkbox syntax.

### Workflow

1. `sync_json_md` generates `review/decision.md` from `proposed/state.json`.
2. Operator opens `decision.md` in Obsidian.
3. Operator marks decisions, edits claims, adds notes.
4. Operator runs `phd2 review-validate` to parse the edited file.
5. Graph resumes if validation passes.

### Optional HTML view enhancement

For richer read-only inspection, nodes may optionally generate `proposed/view.html` from canonical JSON. This is a convenience feature, not part of the review protocol. The review truth always remains in validated artifacts (`review/decision.json` and `approved/state.json`).

See `docs/business_rules/sync_json_md.md` for the full sync service specification.
