# 🌐 Translator

Deterministic, modular pipeline for translating scraped job posting artifacts (JSON fields and Markdown bodies) into a target language.

---

## 🏗️ Architecture & Features

A coordinator delegates translation to provider-specific adapters, with chunking and retry handling at the base level.

- Abstract base adapter (chunking, retries, `translate_text`, `translate_fields`): `src/tools/translator/base.py`
- CLI entry point and provider registry: `src/tools/translator/main.py`
- Provider implementations: `src/tools/translator/providers/`
- Default provider: `GoogleTranslatorAdapter` (uses `deep-translator`)

---

## ⚙️ Configuration

No environment variables required for the default Google adapter. Requires an active internet connection and `deep-translator` installed.

```bash
pip install deep-translator
```

---

## 🚀 CLI / Usage

CLI arguments are defined in `src/tools/translator/main.py`. Run `python -m src.tools.translator.main --help` for the full reference.

---

## 📝 Data Contract

The adapter contract is `BaseTranslatorAdapter` in `src/tools/translator/base.py`. Operational limits (chunk size, retry budget) are exposed as `@property` on the base class.

Input artifacts per job (read from `data/source/<source>/<job_id>/`):
- `extracted_data.json` — fields listed in `P_FIELDS_TO_TRANSLATE` in `src/tools/translator/main.py`
- `content.md` — full job description body

Output artifacts (written to the same job folder):
- `extracted_data_en.json`
- `content_en.md`

---

## 🛠️ How to Add / Extend (New Provider)

1. Create `src/tools/translator/providers/{new_provider}/`.
2. Implement `adapter.py` inheriting from `BaseTranslatorAdapter` in `src/tools/translator/base.py`.
3. Implement required methods: `provider_name`, `translate_chunk`.
4. Register the provider in the `PROVIDERS` dict in `src/tools/translator/main.py`.

---

## 💻 How to Use (Quickstart)

```bash
python -m src.tools.translator.main --source stepstone
python -m src.tools.translator.main --source tuberlin --provider google --target_lang en
```

---

## 🚑 Troubleshooting

- **"ImportError: deep-translator is required"** — run `pip install deep-translator`.
- **"Translation failed after N attempts"** — rate limit or network issue. Check internet connection or increase `retry_delay_seconds` on the adapter.
- **Missing translated fields** — ensure the missing fields are listed in `P_FIELDS_TO_TRANSLATE` in `src/tools/translator/main.py`.
