# Match Skill

This module provides a LangGraph + LangChain-native version of the `dev` branch match-review loop without markdown review files.

## Design

- `graph.py` builds a reusable `match_skill` subgraph.
- `prompt.py` uses `ChatPromptTemplate` for the LLM boundary.
- `contracts.py` defines the structured model and review payload schemas.
- `storage.py` persists immutable round artifacts as JSON for Studio or a custom UI.

## Human Review Flow

1. Run the graph with a checkpointer and `interrupt_before=["human_review_node"]`.
2. Read the paused thread state plus `review/current.json`.
3. Submit a typed `ReviewPayload` with `graph.update_state(..., as_node="human_review_node")`.
4. Resume the graph on the same `thread_id`.

## Artifacts

By default artifacts are written under `output/match_skill/<source>/<job_id>/nodes/match_skill/`.

## CLI

Run a new thread:

```bash
python -m src.cli.run_match_skill \
  --source demo \
  --job-id 123 \
  --requirements requirements.json \
  --profile-evidence profile.json
```

Resume a paused thread with a structured review payload:

```bash
python -m src.cli.run_match_skill \
  --source demo \
  --job-id 123 \
  --resume \
  --review-payload review_payload.json
```

- `approved/state.json`
- `review/current.json`
- `review/decision.json`
- `review/rounds/round_<NNN>/proposal.json`
- `review/rounds/round_<NNN>/decision.json`
- `review/rounds/round_<NNN>/feedback.json`

The review surface is JSON-first so it can feed LangGraph Studio, a CLI TUI, or a small React/Streamlit review app.

## LangGraph Studio

This repo now exposes the graph through `langgraph.json` as:

- `match_skill`: `src.match_skill.graph:create_studio_graph`

Notes:

- Studio should be able to render the graph topology immediately.
- To run the real model node in Studio, set `GOOGLE_API_KEY` or `GEMINI_API_KEY`.
- Without those credentials, Studio falls back to a deterministic demo chain so you can still test graph behavior end-to-end.

## Sample Payloads

Example files for Studio or CLI replay live under `test_assets/match_assets/`:

- `test_assets/match_assets/sample_requirements.json`
- `test_assets/match_assets/sample_profile_evidence.json`
- `test_assets/match_assets/sample_review_payload_approve.json`
- `test_assets/match_assets/sample_review_payload_regenerate.json`
