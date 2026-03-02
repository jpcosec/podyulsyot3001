# Step 07 — CLI `apply-to` Command

## Goal
Wire the `apply-to <url1> <url2> ...` command into `src/cli/pipeline.py`. This is the user-facing entry point that invokes the `ApplicationAgent` with human-in-the-loop review at key checkpoints. The command should feel like a guided workflow: scrape → review plans → approve → execute → review outputs.

## Depends on
- **06-agent-orchestrator** — `ApplicationAgent` with `plan()` and `execute_plan()`

## Files to Read First
- `src/agent/orchestrator.py` — `ApplicationAgent` (from step 06)
- `src/cli/pipeline.py` — `build_parser()`, `main()` (understand how CLI commands are registered)
- `src/cli/pipeline.py` — `run_app_run()` (understand the existing staged flow for reference)

## Files to Modify

### `src/cli/pipeline.py`

Add a new subcommand `apply-to` in `build_parser()` and a handler function.

#### Parser Addition
```python
# In build_parser(), add alongside other subparsers:
apply_parser = subparsers.add_parser(
    "apply-to",
    help="Scrape job URLs, analyze fit, and generate application documents",
)
apply_parser.add_argument(
    "urls",
    nargs="+",
    help="One or more job posting URLs to process",
)
apply_parser.add_argument(
    "--source",
    default="tu_berlin",
    help="Source namespace (default: tu_berlin)",
)
apply_parser.add_argument(
    "--auto",
    action="store_true",
    help="Skip human review checkpoints (not recommended)",
)
apply_parser.add_argument(
    "--via",
    default="docx",
    choices=["docx", "latex"],
    help="CV rendering engine (default: docx)",
)
apply_parser.add_argument(
    "--docx-template",
    default="modern",
    choices=["classic", "modern", "harvard", "executive"],
    help="DOCX template style (default: modern)",
)
```

#### Handler Function
```python
def run_apply_to(args):
    """Guided application workflow: scrape → plan → review → execute."""
    from src.agent.orchestrator import ApplicationAgent

    agent = ApplicationAgent()
    urls = args.urls

    # ── Phase 1: Scrape and Plan ─────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  PHASE 1: Scraping {len(urls)} job(s) and analyzing fit")
    print(f"{'='*60}\n")

    batch = agent.plan(urls)

    print(f"\nFound {len(batch.plans)} viable job(s), skipped {len(batch.skipped)}.")
    print(f"Batch report: {agent.config.pipeline_root / 'batch_report.md'}")

    if not batch.plans:
        print("No jobs to apply to. Exiting.")
        return

    # Print summary
    for plan in batch.plans:
        marker = ">>>" if plan.fit.recommendation == "strong_apply" else "  >"
        print(f"  {marker} [{plan.priority}] {plan.job.title} — score {plan.fit.overall_score}/100 ({plan.fit.recommendation})")

    if batch.skipped:
        print(f"\n  Skipped:")
        for s in batch.skipped:
            print(f"      {s.get('job', {}).get('title', '?')} — score {s.get('score', '?')}")

    # ── Human Checkpoint 1 ───────────────────────────────────────
    if not args.auto:
        print(f"\nReview the batch report, then press Enter to continue (or Ctrl+C to abort)...")
        input()

    # ── Phase 2: Execute Each Plan ───────────────────────────────
    for plan in batch.plans:
        job_id = plan.job.reference_number or "manual"
        print(f"\n{'='*60}")
        print(f"  PHASE 2: Processing {plan.job.title} ({job_id})")
        print(f"{'='*60}\n")

        try:
            results = agent.execute_plan(
                plan,
                source=args.source,
                via=args.via,
                docx_template=args.docx_template,
            )

            print(f"\n  Results for {job_id}:")
            print(f"    CV:          {results.get('cv_pdf', 'N/A')}")
            print(f"    Letter:      {results.get('letter_pdf', 'N/A')}")
            print(f"    ATS Score:   {results.get('ats_score', 'N/A')}")
            print(f"    Tailoring:   {results.get('tailoring', 'N/A')}")

        except Exception as e:
            print(f"\n  ERROR processing {job_id}: {e}")
            print(f"  Continuing with next job...\n")
            continue

        # ── Human Checkpoint 2 (per job) ─────────────────────────
        if not args.auto and plan != batch.plans[-1]:
            print(f"\nReview outputs for {job_id}, then press Enter for next job (or Ctrl+C to stop)...")
            input()

    # ── Summary ──────────────────────────────────────────────────
    print(f"\n{'='*60}")
    print(f"  DONE — Processed {len(batch.plans)} application(s)")
    print(f"{'='*60}")
    print(f"\nNext steps:")
    print(f"  1. Review generated documents in data/pipelined_data/{args.source}/<job_id>/")
    print(f"  2. Run 'pipeline.py cv-validate-ats <job_id>' for detailed ATS reports")
    print(f"  3. Merge final PDFs with 'python src/utils/pdf_merger.py'")
```

#### Main Dispatch
```python
# In main(), add to the command dispatch:
elif args.command == "apply-to":
    run_apply_to(args)
```

## Specification

### User Experience Flow
```
$ python src/cli/pipeline.py apply-to https://tu.berlin/job1 https://tu.berlin/job2

============================================================
  PHASE 1: Scraping 2 job(s) and analyzing fit
============================================================

Found 2 viable job(s), skipped 0.
Batch report: data/pipelined_data/batch_report.md

  >>> [1] Research Assistant III-51/26 — score 78/100 (strong_apply)
    > [2] Research Assistant IV-12/26 — score 52/100 (apply)

Review the batch report, then press Enter to continue (or Ctrl+C to abort)...

============================================================
  PHASE 2: Processing Research Assistant III-51/26 (III-51/26)
============================================================

  Results for III-51/26:
    CV:          data/.../cv/rendered/docx/cv.pdf
    Letter:      data/.../planning/motivation_letter.pdf
    ATS Score:   72
    Tailoring:   8 claims approved

Review outputs for III-51/26, then press Enter for next job...

============================================================
  DONE — Processed 2 application(s)
============================================================
```

### `--auto` Flag
Skips all `input()` checkpoints. Useful for batch processing when the user trusts the agent. Not recommended for first runs.

### Error Handling
- If scraping fails for one URL, log the error and continue with the rest.
- If execution fails for one job, log the error and continue with the next.
- Never crash the entire batch for a single job's failure.

### Integration with Existing Commands
The `apply-to` command does NOT replace existing commands. Users can still:
- `cv-build 201084 english --via docx` — manual CV rendering
- `motivation-build 201084` — manual motivation letter
- `cv-validate-ats 201084` — manual ATS validation

The `apply-to` command is an orchestration layer on top of the same tools.

## Verification
```bash
cd /home/jp/phd

# 1. Parser recognizes the command
python -c "
from src.cli.pipeline import build_parser
parser = build_parser()
args = parser.parse_args(['apply-to', 'https://example.com/job1', 'https://example.com/job2'])
assert args.command == 'apply-to'
assert len(args.urls) == 2
assert args.source == 'tu_berlin'
assert args.auto == False
print('apply-to parser works.')
"

# 2. Parser with flags
python -c "
from src.cli.pipeline import build_parser
parser = build_parser()
args = parser.parse_args(['apply-to', 'https://example.com/job1', '--auto', '--via', 'latex', '--docx-template', 'harvard'])
assert args.auto == True
assert args.via == 'latex'
assert args.docx_template == 'harvard'
print('apply-to flags work.')
"

# 3. Help text includes apply-to
python -c "
import subprocess
result = subprocess.run(['python', 'src/cli/pipeline.py', '--help'], capture_output=True, text=True)
assert 'apply-to' in result.stdout
print('apply-to appears in help text.')
"
```

## Done Criteria
- [ ] `apply-to` subcommand registered in `build_parser()`
- [ ] `run_apply_to()` function handles the full flow
- [ ] Human checkpoints with `input()` (skippable with `--auto`)
- [ ] Per-job error handling (one failure doesn't crash the batch)
- [ ] Summary output at the end with artifact paths
- [ ] `--source`, `--auto`, `--via`, `--docx-template` flags work
- [ ] Help text includes `apply-to`
- [ ] Verification script exits 0
