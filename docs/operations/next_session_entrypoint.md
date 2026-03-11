# Next Session Entrypoint

## Status snapshot (where we stopped)

Current implemented flow in code:

1. `scrape`
2. `translate_if_needed`
3. `extract_understand`
4. `match`
5. `review_match`

Implemented components:

- Graph helpers: `src/graph.py` (`build_prep_match_node_registry`, `create_prep_match_app`, `run_prep_match`)
- LLM plumbing: `src/ai/prompt_manager.py`, `src/ai/llm_runtime.py`
- Node packages:
  - `src/nodes/scrape/`
  - `src/nodes/translate_if_needed/`
  - `src/nodes/extract_understand/`
  - `src/nodes/match/`
  - `src/nodes/review_match/`

Batch artifacts already generated:

- `data/jobs/tu_berlin/_batch_extract_report.json`

Profile source copied into this repo:

- `data/reference_data/profile/base_profile/profile_base_data.json`

Note: `src/cli/run_prep_match.py` now accepts either:

- a JSON list of `my_profile_evidence`, or
- the copied `profile_base_data.json` shape (it auto-transforms to evidence rows).

Profile modeling decision:

- `cv_generation_context` in `profile_base_data.json` is preserved for narrative generation,
- summary/tagline seeds are not injected as matching evidence (`P_SUM` removed),
- matching evidence is built only from auditable records (education/experience/projects/publications/skills/languages).

## Entrypoint command (tomorrow)

Run full prep->match pipeline until `review_match` artifacts are ready:

```bash
python -m src.cli.run_prep_match \
  --source tu_berlin \
  --job-id 201588 \
  --run-id run-next-session \
  --source-url https://www.jobs.tu-berlin.de/en/job-postings/201588 \
  --profile-evidence data/reference_data/profile/base_profile/profile_base_data.json
```

Review file to edit:

- `data/jobs/tu_berlin/201588/nodes/match/review/decision.md`

Resume after editing decision file:

```bash
python -m src.cli.run_prep_match --source tu_berlin --job-id 201588 --resume
```

## Quick verify before running

```bash
python -m pytest -q
```
