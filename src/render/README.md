# 🎨 Render Pipeline

This sub-module provides a unified, command-line interface for rendering tailored CVs (PDFs via LaTeX) and motivation letters (PDFs via DOCX).

## 🏗️ Architecture
It relies on two main components:
- **`render_cv.py`**: Compiles a LaTeX document using dynamically generated context from your base profile and job-specific overrides.
- **`render_letter.py`**: Injects localized markdown content into a DOCX template and converts it to PDF.

The central entry point is **`main.py`**, making it behave similarly to the `scraper` and `translator` modules.

## 🚀 CLI Usage

```bash
python -m src.render.main --action {cv|letter} --source {tuberlin|stepstone} --job-id {ID} [OPTIONS]
```

### CLI Arguments

| Argument | Description | Default |
| :--- | :--- | :--- |
| `--action` | **(Required)** Which document to render: `cv` or `letter`. | |
| `--source` | **(Required)** The job portal source folder (e.g. `tuberlin`). | |
| `--job-id` | **(Required)** The specific job ID inside the source folder. | |
| `--language` | Target language for the template (only applies to CV currently). Choices: `english`, `german`, `spanish`. | `english` |

## 📂 Output

Rendered files are automatically placed in the job's `application` directory:
- `data/jobs/tuberlin/{job-id}/application/cv.pdf`
- `data/jobs/tuberlin/{job-id}/application/motivation_letter.pdf`

*Note: Rendering a letter requires that `motivation_letter.md` already exists in the application directory.*
