# 📝 Generate Documents

<!-- # TODO(future): update the module README to match the standalone graph/runtime role and current storage layout — see future_docs/issues/standards_alignment_followups.md -->

Generates tailored CV, motivation letter, and email body from approved match skill output. Runs as a LangGraph node embedded in the match skill pipeline, and can also be invoked standalone via CLI.

---

## 🏗️ Architecture & Features

Post-approval document generation using structured LLM output + Jinja2 rendering.

- Graph node and chain wiring: `src/ai/generate_documents/graph.py`
- LLM prompt construction: `src/ai/generate_documents/prompt.py`
- Input/output contracts: `src/ai/generate_documents/contracts.py`
- Jinja2 templates (CV, letter, email): `src/ai/generate_documents/templates/`
- Deterministic review indicators: `src/ai/generate_documents/review.py`
- Artifact persistence: `src/ai/generate_documents/storage.py`

Reads approved match artifacts written by `MatchArtifactStore` (`src/ai/match_skill/storage.py`). Writes rendered documents to `DocumentArtifactStore`.

---

## ⚙️ Configuration

```env
GOOGLE_API_KEY="your_gemini_api_key_here"
```

Falls back to a demo chain when `GOOGLE_API_KEY` is absent (Studio/local preview only).

---

## 🚀 CLI / Usage

CLI arguments are defined in `_build_parser()` in `src/ai/generate_documents/main.py`. Run `python -m src.ai.generate_documents.main --help` for the full reference.

This module is also invoked automatically as a node in the match skill graph after an approve decision — no CLI call needed in that path.

---

## 📝 Data Contract

Input and output schemas are defined in `src/ai/generate_documents/contracts.py`:

- `DocumentDeltas` — full structured LLM output (CV summary, injections, letter deltas, email body)
- `CVExperienceInjection` — per-experience bullet point additions
- `MotivationLetterDeltas` — structured letter sections
- `GeneratedDocuments` — rendered markdown outputs (CV, letter, email)
- `TextReviewAssistEnvelope` — deterministic review indicators for the HITL surface

---

## 📂 Artifacts & Storage

Outputs are written under `output/<source>/<job_id>/nodes/generate_documents/`:

- `deltas.json` — raw LLM structured output
- `cv.md` — rendered CV markdown
- `cover_letter.md` — rendered motivation letter
- `email_body.txt` — rendered email body
- `review/assist.json` — deterministic review indicators

---

## 🛠️ How to Add / Extend

1. **Modify templates**: edit files in `src/ai/generate_documents/templates/`.
2. **Refine prompts**: update `src/ai/generate_documents/prompt.py`.
3. **Add document types**: register new templates in `_render_documents_internal()` in `src/ai/generate_documents/graph.py` and add a corresponding contract in `src/ai/generate_documents/contracts.py`.

---

## 💻 How to Use (Quickstart)

Run after the match skill has approved matches for a job:

```bash
python -m src.ai.generate_documents.main \
  --source stepstone --job-id 12345
```

With optional context overrides:

```bash
python -m src.ai.generate_documents.main \
  --source stepstone --job-id 12345 \
  --city Berlin --receiver-name "Prof. Müller"
```

---

## 🚑 Troubleshooting

- **"No approved matches found"**: run the match skill and approve at least one match before generating documents.
- **Missing profile data**: provide `--profile` or ensure `data/reference_data/profile/base_profile/profile_base_data.json` exists.
- **Template errors**: check Jinja2 syntax in `src/ai/generate_documents/templates/`.
- **LLM failures**: verify `GOOGLE_API_KEY` is set; falls back to demo chain if missing.
