# 🌐 Translator

Deterministic, modular pipeline for translating scraped job posting artifacts (JSON fields and Markdown bodies) into a target language.

---

## 🏗️ Architecture & Features

A coordinator delegates translation to provider-specific adapters, with chunking and retry handling at the base level.

- Abstract base adapter (chunking, retries, `translate_text`, `translate_fields`): `src/core/tools/translator/base.py`
- CLI entry point and provider registry: `src/core/tools/translator/main.py`
- Provider implementations: `src/core/tools/translator/providers/`
- Default provider: `GoogleTranslatorAdapter` (uses `deep-translator`)

---

## ⚙️ Configuration

No environment variables required for the default Google adapter. Requires an active internet connection and `deep-translator` installed.

```bash
pip install deep-translator
```

---

## 🚀 CLI / Usage

CLI arguments are defined in `src/core/tools/translator/main.py`. Run `python -m src.core.tools.translator.main --help` for the full reference.

---

## 📝 Data Contract

The translator interacts with the canonical job storage via the `DataManager`.

**Input Artifacts** (read from `nodes/ingest/proposed/`):
- `state.json` — Job metadata/payload including fields defined in `P_FIELDS_TO_TRANSLATE`.
- `content.md` — Full job description text in the original language.

**Output Artifacts** (written to `nodes/translate/proposed/`):
- `state.json` — Translated fields, with `original_language` set to the target language (default `en`).
- `content.md` — Full job description translated to the target language.

---

## 🏗️ Architecture

1. **Base Framework** (`src/core/tools/translator/base.py`): Handles chunking (max 4500 chars), retries, and high-level `translate_text`/`translate_fields` logic.
2. **Providers** (`src/core/tools/translator/providers/`): Specific implementations (e.g., `google` via `deep-translator`).
3. **CLI Wrapper** (`src/core/tools/translator/main.py`): Standalone utility that translates existing canonical ingest artifacts.
4. **Operator Integration** (`src/cli/main.py`): Higher-level workflows can invoke translation before later pipeline stages.

---

## 🚀 Usage

### Via CLI (Batch Processing)
```bash
python -m src.core.tools.translator.main --source stepstone --target_lang en
```

---

## 🚑 Troubleshooting

- **"ImportError: deep-translator is required"** — Run `pip install deep-translator`.
- **"Translation failed after N attempts"** — Network timeout or rate limit. The retry mechanism handles transient issues, but check your internet connection.
- **Fields not translating** — Ensure the field name is included in `P_FIELDS_TO_TRANSLATE` within `src/core/tools/translator/main.py`.
