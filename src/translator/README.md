# 🌐 Modular Translator Pipeline

This sub-module provides a deterministic way to translate the JSON records and Markdown artifacts extracted by the scraper. It implements a robust architecture modeled exactly after the Scraper adapter system.

## 🏗️ Architecture

Each translation provider (e.g., `GoogleTranslatorAdapter`, `GeminiTranslatorAdapter`) inherits from `BaseTranslatorAdapter`. The framework handles all the robust mechanics natively:
- **Automatic Text Chunking:** Extremely long texts are safely split based on API character limits (`max_chunk_chars`).
- **Resilience:** Built-in bounded retries and exponential fallbacks if a chunk fails to translate due to API rate limits.
- **Deep Translation:** Capable of translating both raw Markdown texts (`translate_text()`) and nested JSON payload dictionaries (`translate_fields()`), effortlessly handling `JobPosting` data contracts.

## 🚀 CLI Usage

After scraping jobs, you can translate them in bulk using `main.py`:

```bash
python -m src.translator.main --source {tuberlin|stepstone|xing} [OPTIONS]
```

### CLI Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--source` | **(Required)** The job portal source folder to scan in `data/source/`. | |
| `--provider` | The translation provider to use (currently `google`). | `google` |
| `--target_lang` | The ISO language code to translate into. | `en` |
| `--data_dir` | The root data directory containing the scraped outputs. | `data/source` |
| `--force` | Force re-translation even if `_en` translated artifacts already exist. | `False` |

## 📂 Output

For every job folder processed (e.g. `data/source/tuberlin/12345/`), the pipeline detects the `original_language` field in `extracted_data.json`.
- If the original language matches the target language, it skips translation and creates standard copies.
- If it does not match, it translates the fields and the markdown content.

The output inside the job folder will be:
- `extracted_data_en.json`: Translated Pydantic-compliant schema.
- `content_en.md`: Translated Job Description.
