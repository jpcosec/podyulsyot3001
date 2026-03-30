# 📝 Generate Documents

Generates tailored CV, motivation letter, and email body from approved match output. The core generation path works on in-memory payloads, while the schema-v0 pipeline and standalone CLI persist canonical artifacts under `data/jobs/<source>/<job_id>/...`.

---

## 🏗️ Architecture & Features

Post-approval document generation using structured LLM output + Jinja2 rendering.

- Graph node and chain wiring: `src/core/ai/generate_documents/graph.py`
- LLM prompt construction: `src/core/ai/generate_documents/prompt.py`
- Input/output contracts: `src/core/ai/generate_documents/contracts.py`
- Jinja2 templates (CV, letter, email): `src/core/ai/generate_documents/templates/`
- Deterministic review indicators: `src/core/ai/generate_documents/review.py`
- Artifact persistence helpers: `src/core/ai/generate_documents/storage.py`
- Schema-v0 CLI orchestration via the central data manager: `src/core/ai/generate_documents/main.py`

The pure generation helper is `generate_documents_bundle()` in `src/core/ai/generate_documents/graph.py`. It receives primitive or validated in-memory inputs and returns structured outputs. Persistence happens at the orchestration layer.

---

## ⚙️ Configuration

```env
GOOGLE_API_KEY="your_gemini_api_key_here"
```

Falls back to a demo chain when `GOOGLE_API_KEY` is absent (Studio/local preview only).

---

## 🚀 CLI / Usage

CLI arguments are defined in `_build_parser()` in `src/core/ai/generate_documents/main.py`. Run `python -m src.core.ai.generate_documents.main --help` for the full reference.

This module is invoked automatically after approved match output exists, and it can also be run standalone against the canonical schema-v0 artifacts already stored under `data/jobs/...`.

---

## 📝 Data Contract

Input and output schemas are defined in `src/core/ai/generate_documents/contracts.py`:

- `DocumentDeltas` — full structured LLM output (CV summary, injections, letter deltas, email body)
- `CVExperienceInjection` — per-experience bullet point additions
- `MotivationLetterDeltas` — structured letter sections
- `GeneratedDocuments` — rendered markdown outputs (CV, letter, email)
- `TextReviewAssistEnvelope` — deterministic review indicators for the HITL surface

---

## 📂 Artifacts & Storage

Schema-v0 pipeline outputs are written under `data/jobs/<source>/<job_id>/nodes/generate_documents/`:

- `deltas.json` — raw LLM structured output
- `cv.md` — rendered CV markdown
- `cover_letter.md` — rendered motivation letter
- `email_body.txt` — rendered email body
- `review/assist.json` — deterministic review indicators

---

## 🛠️ How to Add / Extend

1. **Modify templates**: edit files in `src/core/ai/generate_documents/templates/`.
2. **Refine prompts**: update `src/core/ai/generate_documents/prompt.py`.
3. **Add document types**: register new templates in `_render_documents_internal()` in `src/core/ai/generate_documents/graph.py` and add a corresponding contract in `src/core/ai/generate_documents/contracts.py`.

---

## 💻 How to Use (Quickstart)

Run after the match skill has approved matches for a job:

```bash
python -m src.core.ai.generate_documents.main \
  --source stepstone --job-id 12345
```

With optional context overrides:

```bash
python -m src.core.ai.generate_documents.main \
  --source stepstone --job-id 12345 \
  --city Berlin --receiver-name "Prof. Müller"
```

---

## 🚑 Troubleshooting

- **"No approved matches found"**: run the match skill and approve at least one match before generating documents.
- **Missing profile data**: provide `--profile` or ensure `data/reference_data/profile/base_profile/profile_base_data.json` exists; the CLI falls back to a minimal demo-safe profile structure for template rendering.
- **Template errors**: check Jinja2 syntax in `src/core/ai/generate_documents/templates/`.
- **LLM failures**: verify `GOOGLE_API_KEY` is set; falls back to demo chain if missing.
