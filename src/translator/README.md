# 🌐 Translator Pipeline

The `src/translator` module provides a deterministic, modular pipeline for translating JSON records and Markdown artifacts extracted by the scraper.

---

## 🏗️ Architecture & Features

The translation engine consists of a central coordinator and provider-specific adapters:
- **`BaseTranslatorAdapter`**: An abstract base class defining the contract for translation providers.
- **`GoogleTranslatorAdapter`**: A default adapter powered by `deep-translator`.
- **Automatic Text Chunking**: Extremely long texts (like job descriptions) are safely split based on API character limits (`max_chunk_chars`).
- **Resilience**: Built-in bounded retries and exponential fallbacks to handle transient API rate limits.
- **Deep Translation**: Capable of translating both raw Markdown (`translate_text()`) and nested JSON dictionaries (`translate_fields()`).

---

## ⚙️ Configuration

Set your translation source and credentials in the root `.env` file:
```env
# No environment variables are strictly required for the default Google adapter,
# but it requires an active internet connection and certain packages:
# - deep-translator (pip install deep-translator)
```

---

## 💻 How to Use (Quickstart)

Translate all scraped jobs from a specific source:
```bash
# Translate StepStone results into English
python -m src.translator.main --source stepstone

# Translate TU Berlin results using a specific provider
python -m src.translator.main --source tuberlin --provider google --target_lang en
```

---

## 🚀 CLI / Usage

| Argument | Description | Default |
|---|---|---|
| `--source` | **(Required)** The job portal source folder (e.g. `stepstone`, `xing`) in `data/source/`. | |
| `--provider` | The translation provider to use (currently `google`). | `google` |
| `--target_lang` | The ISO language code to translate into. | `en` |
| `--data_dir` | The root data directory containing the scraped outputs. | `data/source` |
| `--force` | Force re-translation even if `_en` translated artifacts already exist. | `False` |

---

## 📝 The Data Contract

The pipeline translates the following standard artifacts:
- **`extracted_data.json`**: Translates string fields defined in `P_FIELDS_TO_TRANSLATE` (e.g., `job_title`, `responsibilities`).
- **`content.md`**: Translates the full body text of the job description.
- **Result**: Generates `extracted_data_en.json` and `content_en.md` in the original job folder.

---

## 🛠️ How to Add / Extend (New Provider)

1.  Create a folder under `src/translator/providers/{new_provider}/`.
2.  Implement `adapter.py` by inheriting from `BaseTranslatorAdapter`.
3.  Implement the required methods: `provider_name` and `translate_chunk`.
4.  Register your provider in the `PROVIDERS` dictionary in `src/translator/main.py`.

---

## 🚑 Troubleshooting

- **"ImportError: deep-translator is required"**:
    - *Symptom:* The Google adapter fails to import.
    - *Solution:* Run `pip install deep-translator`.
- **"Translation failed after N attempts"**:
    - *Symptom:* Logs show multiple retry warnings then a final failure.
    - *Diagnosis:* API rate limits or network issues.
    - *Solution:* Check your internet connection or increase `retry_delay_seconds` in the adapter.
- **Missing Translations**:
    - *Symptom:* Only some fields in the JSON are translated.
    - *Solution:* Ensure the missing fields are listed in `P_FIELDS_TO_TRANSLATE` in `src/translator/main.py`.
