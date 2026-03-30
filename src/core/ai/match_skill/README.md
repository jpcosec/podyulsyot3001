# ⚖️ Match Skill

This module provides a LangGraph + LangChain-native matching loop with a deterministic human-in-the-loop review workflow. It replaces manual markdown review files with structured JSON artifacts and a Textual TUI.

---

## 🏗️ Architecture & Features

The match skill is a reusable LangGraph subgraph with a single human review breakpoint.

- Graph definition and node wiring: `src/core/ai/match_skill/graph.py`
- State schema (`MatchSkillState`): `src/core/ai/match_skill/graph.py`
- LLM prompt construction: `src/core/ai/match_skill/prompt.py`
- Artifact persistence (immutable rounds, review surface): `src/core/ai/match_skill/storage.py`
- Input/output contracts: `src/core/ai/match_skill/contracts.py`

Full graph flow:

```
__start__
  → load_match_inputs
  → run_match_llm
  → persist_match_round
  → human_review_node          ← graph pauses here
  → apply_review_decision
       → generate_documents → __end__          (approve)
       → prepare_regeneration_context          (request_regeneration)
             → run_match_llm  (loop)
       → __end__                               (reject)
```

Routes via LangGraph `Command` after the review decision.

---

## ⚙️ Configuration

```env
GOOGLE_API_KEY="your_gemini_api_key_here"
```

---

## 🚀 CLI / Usage

CLI arguments are defined in `src/core/ai/match_skill/main.py`. Run `python -m src.core.ai.match_skill.main --help` for the full reference.

The TUI review interface is in `src/review_ui/`.

---

## 📝 Data Contract

Input and output schemas are defined in `src/core/ai/match_skill/contracts.py`:
- `RequirementInput` — one requirement from the job posting
- `ProfileEvidence` — one evidence item from the candidate profile
- `RequirementMatch` — LLM output for one matched requirement
- `MatchEnvelope` — full structured LLM output
- `ReviewPayload` — what the TUI sends back into the graph to resume
- `ReviewSurface` / `ReviewSurfaceItem` — the JSON artifact displayed in the TUI

---

## 📂 Artifacts & Storage

All rounds are versioned under `data/jobs/<source>/<job_id>/nodes/match_skill/`:
- `approved/state.json` — final approved state
- `review/current.json` — latest pending proposal
- `review/rounds/round_<NNN>/` — immutable per-round snapshots

---

## 👤 HITL Operator Contract

Review is payload-driven, not acknowledgement-driven. Pressing Continue alone does nothing — the graph requires an explicit `ReviewPayload`.

**As a reviewer, you are responsible for:**
- Inspecting `review/current.json` — the structured review surface for the current round
- Making an explicit decision per requirement row: `approve`, `request_regeneration`, or `reject`
- Providing patch evidence when requesting regeneration
- Submitting via the TUI (`src/review_ui/`) or by passing `--review-payload` to the CLI

**The system guarantees:**
- The graph will not proceed without a valid, hash-checked payload
- A bare Continue (no payload) returns safely to `pending_review` — no crash
- Every round is persisted immutably under `review/rounds/round_NNN/` before the graph pauses
- A stale payload (hash mismatch — the proposal changed since you loaded the surface) is rejected

---

## 🛠️ How to Add / Extend

1. **Modify matching logic**: update nodes in `src/core/ai/match_skill/graph.py`.
2. **Refine prompts**: update `src/core/ai/match_skill/prompt.py`.
3. **Add contract fields**: extend models in `src/core/ai/match_skill/contracts.py` — update `Field(description=...)` for any LLM-consumed field.

---

## 💻 How to Use (Quickstart)

Start a new match thread:
```bash
python -m src.core.ai.match_skill.main \
  --source demo \
  --job-id 123 \
  --requirements requirements.json \
  --profile-evidence profile.json
```

Resume after HITL review:
```bash
python -m src.core.ai.match_skill.main \
  --source demo \
  --job-id 123 \
  --resume \
  --review-payload review_payload.json
```

---

## 🚑 Troubleshooting

- **Graph fails to start**: ensure input JSON files conform to `RequirementInput` and `ProfileEvidence` schemas in `src/core/ai/match_skill/contracts.py`.
- **Studio connection failure**: check `langgraph.json` and API keys.
- **Studio runs but match produces dummy output**: `GOOGLE_API_KEY` is absent — the graph uses a deterministic demo chain. Set the key for real matching.
- **Missing artifacts**: ensure `data/jobs/` is writable; check `MatchArtifactStore` initialisation in `src/core/ai/match_skill/storage.py`.
