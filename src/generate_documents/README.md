# 📝 Generate Documents

This module provides LangGraph-native document generation for tailored CV, motivation letter, and email outputs based on approved matches from the match_skill pipeline.

---

## 🏗️ Architecture & Features

The `generate_documents` module is designed as a post-approval LangGraph subgraph:
- **`graph.py`**: Constructs the generation node with LLM structured output + Jinja2 rendering.
- **`prompt.py`**: Uses strict system prompts with anti-fluff constraints.
- **`contracts.py`**: Pydantic schemas for LLM structured output (`DocumentDeltas`).
- **`storage.py`**: Persists rendered documents and review indicators.
- **`templates/`**: Jinja2 templates for CV, cover letter, and email.
- **Studio Ready**: Exposed via `create_studio_graph()` in `langgraph.json`.

---

## ⚙️ Configuration

Set your LLM credentials in the root `.env` file:
```env
# Required for document generation
GOOGLE_API_KEY="your_gemini_api_key_here"
```

---

## 💻 How to Use (Quickstart)

The graph runs automatically after match_skill approval, but can also be triggered manually:

```bash
# Via API (after match_skill approval)
curl -X POST "http://localhost:8124/threads/<thread_id>/runs" \
  -H "Content-Type: application/json" \
  -d '{
    "assistant_id": "<generate_documents_assistant_id>",
    "input": {
      "source": "stepstone",
      "job_id": "12345",
      "requirements": [],
      "profile_base_data": {},
      "review_payload": {},
      "artifact_refs": {}
    }
  }'
```

---

## 🚀 CLI / Usage

This module is typically invoked via LangGraph Studio or API after match_skill approval. Direct CLI invocation is not currently provided.

---

## 📝 The Data Contract

### Input State
- **`source`**: Job portal source (e.g. `stepstone`, `xing`).
- **`job_id`**: Unique job posting ID.
- **`requirements`**: List of job requirements.
- **`profile_base_data`**: Candidate's base CV/profile.
- **`review_payload`**: Human feedback from match_skill review phase.

### Output State
- **`document_deltas`**: Raw LLM structured output (`DocumentDeltas`).
- **`generated_documents`**: Rendered markdown (CV, letter, email).
- **`artifact_refs`**: File paths to persisted artifacts.
- **`status`**: `"documents_generated"` on success.

---

## 📂 Artifacts & Storage

All outputs are versioned under:
`output/<source>/<job_id>/nodes/generate_documents/`

Key persistent files:
- `deltas.json`: Raw LLM output.
- `cv.md`: Rendered CV markdown.
- `cover_letter.md`: Rendered motivation letter.
- `email_body.txt`: Rendered email body.
- `review/assist.json`: Deterministic review indicators.

---

## 🛠️ How to Add / Extend

1. **Modify Templates**: Edit files in `src/generate_documents/templates/`.
2. **Refine Prompts**: Update system/user prompts in `src/generate_documents/prompt.py`.
3. **Add Document Types**: Register new templates in `graph.py:_render_documents_internal`.
4. **Add Validation**: Extend `contracts.py` with new Pydantic models.

---

## 🚑 Troubleshooting

- **Missing Profile Data**: Ensure `profile_base_data` is provided or `data/reference_data/profile/base_profile/profile_base_data.json` exists.
- **No Approved Matches**: Generate documents only runs after match_skill approval writes to `output/<source>/<job_id>/approved/state.json`.
- **Template Errors**: Check Jinja2 syntax in `templates/` files.
- **LLM Failures**: Verify `GOOGLE_API_KEY` is set; falls back to demo chain if missing.
