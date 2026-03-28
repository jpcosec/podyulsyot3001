# ⚖️ Match Skill

This module provides a LangGraph + LangChain-native version of the matching loop, enabling a deterministic human-in-the-loop workflow without the need for manual markdown review files.

---

## 🏗️ Architecture & Features

The `match_skill` is designed as a reusable LangGraph subgraph:
- **`graph.py`**: Constructs the state graph with a `human_review_node` interrupt.
- **`prompt.py`**: Uses `ChatPromptTemplate` for clear, versioned LLM boundaries.
- **`storage.py`**: Persists immutable round artifacts as JSON for external UI integration (Studio, TUI, or Web).
- **LangGraph Native**: Uses standard checkpointers and interrupt logic for robust state persistence.

---

## ⚙️ Configuration

Set your LLM credentials in the root `.env` file:
```env
# Required for the graph logic and Studio
GOOGLE_API_KEY="your_gemini_api_key_here"
```

---

## 💻 How to Use (Quickstart)

To run a new match thread for a job:
```bash
python -m src.cli.run_match_skill \
  --source demo \
  --job-id 123 \
  --requirements requirements.json \
  --profile-evidence profile.json
```

To resume a paused thread with a human review decision:
```bash
python -m src.cli.run_match_skill \
  --source demo \
  --job-id 123 \
  --resume \
  --review-payload review_payload.json
```

---

## 🚀 CLI / Usage

| Argument | Description | Default |
|---|---|---|
| `--source` | The job portal source name (e.g. `stepstone`, `xing`). | `demo` |
| `--job-id` | Unique ID for the job posting being matched. | |
| `--resume` | If set, resumes the latest interrupted thread. | `False` |
| `--review-payload` | Path to a JSON file containing the `ReviewPayload` for resume. | |
| `--requirements` | Input requirements structure (for new threads). | |
| `--profile-evidence` | Your CV/profile evidence JSON (for new threads). | |

---

## 📝 The Data Contract

The matching engine consumes and produces standardized JSON envelopes:
- **`MatchState`**: The LangGraph state schema (requires `job_id`, `source`, `match_result`).
- **`ReviewPayload`**: Schema for human feedback, containing `approved`, `feedback`, and `decisions`.
- **`RoundArtifact`**: Immutable record of one iteration of LLM matching + human review.

---

## 📂 Artifacts & Storage

By default, all iterations are versioned under:
`output/match_skill/<source>/<job_id>/nodes/match_skill/`

Key persistent files:
- `approved/state.json`: Final approved state.
- `review/current.json`: Latest pending proposal.
- `review/rounds/round_<NNN>/proposal.json`: Historical iterations.

---

## 🛠️ How to Add / Extend

1.  **Modify Logic**: Update nodes in `src/match_skill/graph.py`.
2.  **Add Tools**: Register new LangChain tools in `src/match_skill/graph.py:create_match_skill_graph`.
3.  **Refine Prompts**: Update the system message template in `src/match_skill/prompt.py`.

---

## 🚑 Troubleshooting

- **Graph Fails to Start**: Ensure all input JSON files match the expected `MatchState` schema.
- **Studio Connection Failure**: Check your `langgraph.json` configuration and your API keys.
- **Missing Artifacts**: Ensure the `output/` directory is writable and the `MatchArtifactStore` in `storage.py` is initialized correctly.
