# LangGraph Run + HITL + Testing Guide

This guide explains:

1. how graph-based runtime execution works,
2. how human-in-the-loop (HITL) review works,
3. how to test the flow reliably.

Primary implementation references:

- `src/cli/pipeline.py`
- `src/graph/pipeline.py`
- `src/steps/matching.py`

## 1) How graph execution works

`pipeline job <id> run` executes a LangGraph `StateGraph` coordinator.

Node order:

```text
ingest -> match -> review_gate(interrupt) -> motivate -> tailor_cv -> email -> render -> package
```

State persistence:

- checkpoint DB path: `data/pipelined_data/<source>/<job_id>/.graph/checkpoints.db`
- thread id: `<source>/<job_id>`
- checkpoint files are runtime-only and gitignored (`**/.graph/`)

Important runtime behavior:

- `run` starts a fresh execution thread for the job.
- `run --resume` continues from an interrupted checkpoint.
- `graph-status` inspects current checkpoint state and next node(s).

## 2) Human-in-the-loop interaction

HITL is implemented at `review_gate`.

### 2.1 First pass

1. Start run:

   ```bash
   python src/cli/pipeline.py job <job_id> run
   ```

2. Pipeline pauses when review lock is missing (`planning/reviewed_mapping.json`).
3. You review and edit:

   - `planning/match_proposal.md`
   - each requirement decision: `approve`, `edit`, or `reject`
   - optional reviewer text in `Edited Claim:` and `Notes:`

4. Resume:

   ```bash
   python src/cli/pipeline.py job <job_id> run --resume
   ```

On resume, the system parses the reviewed proposal and writes `planning/reviewed_mapping.json`, then continues through downstream nodes.

### 2.2 Additional review rounds

If matching must be regenerated:

```bash
python src/cli/pipeline.py job <job_id> match --force
python src/cli/pipeline.py job <job_id> run --resume
```

Regeneration safeguards:

- previous proposal archived as `planning/match_proposal.roundN.md`
- stale `planning/reviewed_mapping.json` removed automatically
- claim priority: edited claim > LLM claim > deterministic fallback

## 3) Operator commands

### 3.1 Core run commands

```bash
python src/cli/pipeline.py job <job_id> run
python src/cli/pipeline.py job <job_id> run --resume
python src/cli/pipeline.py job <job_id> graph-status
```

### 3.2 Manual step commands (still available)

```bash
python src/cli/pipeline.py job <job_id> ingest
python src/cli/pipeline.py job <job_id> match
python src/cli/pipeline.py job <job_id> match-approve
python src/cli/pipeline.py job <job_id> motivate
python src/cli/pipeline.py job <job_id> tailor-cv
python src/cli/pipeline.py job <job_id> draft-email
python src/cli/pipeline.py job <job_id> render --via docx --docx-template modern
python src/cli/pipeline.py job <job_id> package
```

Use manual verbs for targeted recovery/debug; use `run`/`run --resume` for normal orchestration.

## 4) Testing the flow

### 4.1 Fast automated regression (recommended)

Run focused tests that cover CLI parsing and step integrations:

```bash
pytest tests/cli/test_pipeline.py tests/steps/test_matching.py tests/steps/test_cv_tailoring.py tests/steps/test_motivation.py -q
```

Run full suite:

```bash
pytest tests/ -x
```

### 4.2 Manual smoke test (single job)

1. Choose job id with existing ingestion artifacts.
2. Start run:

   ```bash
   python src/cli/pipeline.py job <job_id> run
   ```

3. Confirm interruption message and verify proposal exists:

   - `planning/match_proposal.md`

4. Edit proposal decisions.
5. Resume:

   ```bash
   python src/cli/pipeline.py job <job_id> run --resume
   ```

6. Verify downstream artifacts:

   - `planning/reviewed_mapping.json`
   - `planning/motivation_letter.md`
   - `planning/cv_tailoring.md`
   - `planning/application_email.md`
   - `output/cv.pdf`
   - `output/Final_Application.pdf`

7. Inspect graph checkpoint state:

   ```bash
   python src/cli/pipeline.py job <job_id> graph-status
   ```

### 4.3 Resume/recovery checks

Test checkpoint continuity:

1. `run` until interrupt
2. stop terminal/session
3. start new terminal
4. execute `run --resume`

Expected: execution resumes from checkpointed review state, not from start.

## 5) Common failure modes

- `run --resume` before any interrupt/checkpoint -> resume error; run fresh first.
- edited proposal missing decisions -> review parse can fail; complete decision checkboxes.
- missing runtime deps (`langgraph`, `langgraph-checkpoint-sqlite`) -> install env dependencies.
