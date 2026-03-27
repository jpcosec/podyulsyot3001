# LangSmith Verification (Current Runtime)

## Purpose

Describe how to run the prep-match pipeline in LangSmith-verifiable mode.

## What is instrumented

- Graph-level run span: `graph.run_pipeline`
- Every graph node span: `node.<node_name>` (applies to all nodes registered in `create_app`)
- Deterministic quality evaluation span: `quality_eval.prep_match`

## Required environment variables

- `LANGSMITH_API_KEY` (required in verifiable mode)
- `LANGSMITH_PROJECT` (optional, default: `phd-20`)
- `LANGSMITH_ENDPOINT` (optional; only needed for custom LangSmith endpoints)

You can also enforce verification globally by setting:

- `PHD2_LANGSMITH_REQUIRE_VERIFICATION=1`

## CLI usage

Run prep-match with explicit verification:

```bash
python -m src.cli.run_pipeline \
  --source <source> \
  --job-id <job_id> \
  --source-url <url> \
  --profile-evidence <path> \
  --langsmith-verifiable
```

In this mode:

- missing `LANGSMITH_API_KEY` fails closed
- a deterministic verification report is written to `data/jobs/<source>/<job_id>/graph/langsmith_verification.json`
- failed quality checks raise an error
