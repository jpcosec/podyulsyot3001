# 📄 Render Pipeline

The `src/render` module provides a typed, engine-agnostic document rendering pipeline, decoupling document logic from rendering backends (PDF, DOCX).

---

## 🏗️ Architecture & Features

The pipeline uses a **Coordinator Pattern** to orchestrate document resolution:
- **`coordinator.py`**: The central entry point. Resolves adapters, manifests, locale bundles, and output paths.
- **`documents/`**: Adapters that normalize domain inputs (CV, Letter) into a shared intermediate state.
- **`engines/`**: Backend-specific rendering logic (Pandoc, LaTeX, Docx).
- **`languages/`**: Typed locale bundles (`common`, `cv`, `letter`) using Pydantic validation.
- **`templates/`**: Central registry for style templates and their respective manifests.

---

## ⚙️ Configuration

Rendering requires external system dependencies:
```env
# No environment variables are strictly required, but the following paths must be on your $PATH:
# - pandoc (>= 2.x)
# - pdflatex (or xelatex)
# - libreoffice (only for docx -> pdf conversions)
```

---

## 💻 How to Use (Quickstart)

Render a localized CV from markdown:
```bash
python -m src.render.main cv \
  --source test_assets/cv/en.md \
  --language en \
  --template classic \
  --engine tex \
  --output output/cv-en.pdf
```

Render a professional letter:
```bash
python -m src.render.main letter \
  --source test_assets/letter/de.md \
  --language de \
  --template default \
  --engine tex \
  --output output/letter-de.pdf
```

---

## 🚀 CLI / Usage

| Argument | Description | Default |
|---|---|---|
| `cv \| letter` | **(Required)** The document type to render. | |
| `--source` | Path to the source file (Markdown or JSON). | |
| `--language` | ISO language code (e.g. `en`, `de`, `es`). | `en` |
| `--template` | Style template name (e.g. `classic`, `default`). | `classic` |
| `--engine` | Rendering backend (`tex`, `docx`, `pandoc`). | `tex` |
| `--output` | Destination path for the rendered file. | `output/rendered.pdf` |
| `--job-id` | (Optional) Job ID for automated folder resolution. | |

---

## 📝 The Data Contract

The pipeline operates on a unified **`RenderRequest`** model:
- **`DocumentType`**: Enum (`cv`, `letter`).
- **`RenderEngine`**: Enum (`tex`, `docx`).
- **`Locale`**: Standardized language and region metadata.
- **`TemplateManifest`**: JSON-based style declaration (found in `src/render/templates/**/manifest.json`).

---

## 🛠️ How to Add / Extend

1.  **Add a new Template**:
    - Create a new folder under `src/render/templates/{doc_type}/{template_name}/`.
    - Create a `manifest.json` defining the engine-specific files.
2.  **Add a Language**:
    - Create a new locale sub-package in `src/render/languages/{iso_code}/`.
    - Implement the `CvLocale`, `LetterLocale`, and `CommonLocale` bundles.
3.  **Add an Engine**:
    - Implement the `BaseRenderEngine` abstract class in `src/render/engines/`.

---

## 🚑 Troubleshooting

- **"Pandoc not found"**: Ensure the `pandoc` binary is in your system `PATH`.
- **LaTeX Compilation Errors**: Check `logs/render_*.log` for specific TeX errors. Often caused by missing character support in the selected font.
- **DOCX Formatting Issues**: The `pandoc` docx engine is sensitive to the reference document structure. Verify your template manifest points to a valid `.docx` reference file.
