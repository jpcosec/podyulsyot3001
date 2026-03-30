# 📄 Render Pipeline

Typed, engine-agnostic document rendering pipeline. Decouples document logic from rendering backends (PDF via LaTeX, DOCX via Pandoc).

---

## 🏗️ Architecture & Features

Uses a Coordinator pattern — one entry point resolves adapters, manifests, locale bundles, and output paths.

- Central coordinator (facade, orchestrates the full render): `src/core/tools/render/coordinator.py`
- Unified request model: `src/core/tools/render/request.py`
- Adapter and manifest registry: `src/core/tools/render/registry.py`
- Document adapters (CV, Letter — normalize inputs to intermediate state): `src/core/tools/render/documents/`
- Rendering backends (LaTeX/Pandoc): `src/core/tools/render/engines/`
- Typed locale bundles (common, cv, letter): `src/core/tools/render/languages/`
- Style templates and manifests: `src/core/tools/render/templates/`
- CLI entry point: `src/core/tools/render/main.py`

---

## ⚙️ Configuration

No environment variables required. The following binaries must be on `$PATH`:

- `pandoc` (>= 2.x)
- `pdflatex` or `xelatex`
- `libreoffice` (only for DOCX → PDF conversions)

---

## 🚀 CLI / Usage

CLI arguments are defined in `_build_parser()` in `src/core/tools/render/main.py`. Run `python -m src.core.tools.render.main --help` for the full reference.

---

## 📝 Data Contract

The request contract is `RenderRequest` in `src/core/tools/render/request.py`. All renders go through `RenderCoordinator.render(request)` in `src/core/tools/render/coordinator.py`.

---

## 🛠️ How to Add / Extend

1. **New template**: create `src/core/tools/render/templates/{doc_type}/{name}/` with a `manifest.json`.
2. **New language**: create `src/core/tools/render/languages/{iso_code}/` and implement `CvLocale`, `LetterLocale`, `CommonLocale`.
3. **New engine**: implement `BaseRenderEngine` in `src/core/tools/render/engines/` and register it in `src/core/tools/render/registry.py`.

---

## 💻 How to Use (Quickstart)

```bash
python -m src.core.tools.render.main cv \
  --source test_assets/cv/en.md --language en --engine tex

python -m src.core.tools.render.main letter \
  --source test_assets/letter/de.md --language de --engine tex
```

---

## 🚑 Troubleshooting

- **"Pandoc not found"** — ensure `pandoc` is on `$PATH`.
- **LaTeX compilation errors** — check `logs/render_*.log` for TeX errors. Often caused by missing character support in the selected font.
- **DOCX formatting issues** — the Pandoc DOCX engine is sensitive to the reference document. Verify your template manifest points to a valid `.docx` reference file.
