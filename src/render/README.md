# Render Pipeline

`src/render` now uses a typed request/coordinator flow so document type, engine, style, and language are resolved independently instead of being mixed inside per-document services.

## Structure

```text
src/render/
├── coordinator.py
├── request.py
├── registry.py
├── documents/
│   ├── base.py
│   ├── cv/
│   └── letter/
├── engines/
│   ├── docx/
│   ├── latex/
│   └── pandoc/
├── languages/
│   ├── models.py
│   ├── registry.py
│   ├── en/
│   ├── es/
│   └── de/
├── templates/
│   ├── cv/
│   ├── letter/
│   └── shared/
├── shared/
├── main.py
└── __init__.py
```

- `coordinator.py` resolves adapters, manifests, locale bundles, and paths.
- `documents/` contains document adapters that normalize CV and letter inputs.
- `engines/` contains backend adapters and rendering helpers.
- `languages/` contains typed locale bundles split by `common`, `cv`, and `letter`.
- `templates/` is the root registry for style templates and manifests.
- `shared/` contains reusable filesystem and metadata helpers.

## Current Model

- `cv`: Markdown-first via Pandoc, with a coordinator-managed legacy JSON -> LaTeX fallback for job-based rendering.
- `letter`: Markdown-first via Pandoc for PDF and DOCX output.
- `classic` CV style: root-level template manifest plus the familiar legacy `moderncv` asset set.
- `language`: handled through typed locale bundles, not hardcoded template labels.

## CLI Usage

Direct source rendering:

```bash
python -m src.render.main cv --source test_assets/cv/en.md --language en --template classic --engine tex --output output/cv-en.pdf
python -m src.render.main cv --source test_assets/cv/es.md --language es --template classic --engine tex --output output/cv-es.pdf
python -m src.render.main cv --source test_assets/cv/de.md --language de --template classic --engine tex --output output/cv-de.pdf
python -m src.render.main letter --source test_assets/letter/en.md --language en --template default --engine tex --output output/letter-en.pdf
python -m src.render.main letter --source test_assets/letter/es.md --language es --template default --engine tex --output output/letter-es.pdf
python -m src.render.main letter --source test_assets/letter/de.md --language de --template default --engine tex --output output/letter-de.pdf
```

DOCX smoke examples:

```bash
python -m src.render.main cv --source test_assets/cv/es.md --language es --template classic --engine docx --output output/cv-es.docx
python -m src.render.main letter --source test_assets/letter/de.md --language de --template default --engine docx --output output/letter-de.docx
```

Legacy job-based rendering:

```bash
python -m src.render.main --action cv --source stepstone --job-id 12345 --language en --template classic
python -m src.render.main --action letter --source stepstone --job-id 12345 --language de --template default
```

## Notes

- `--engine` and `--motor` are aliases.
- `--extra-vars KEY=VALUE` can be repeated to inject Pandoc metadata.
- the coordinator, not the engines, is responsible for output and build path creation.
- Pandoc and a working TeX installation are required for the Markdown -> PDF flow.
- LibreOffice is still used when a DOCX -> PDF conversion is needed.

## Test Assets

Create localized test markdown files under `test_assets/cv/` and `test_assets/letter/` for testing the pipeline.

## Localization Model

- language bundles live under `src/render/languages/` and are split into `common.py`, `cv.py`, and `letter.py` per locale.
- Pydantic models in `src/render/languages/models.py` validate the structure and support style-aware overrides.
- style manifests under `src/render/templates/**/manifest.json` declare templates, assets, and Lua filters independently from the engines.
