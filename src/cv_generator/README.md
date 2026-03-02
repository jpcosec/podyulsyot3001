# CV Generator

CV generation module with two rendering engines used in PDF build flows:

- `latex` (default engine)
- `docx` (DOCX render + LibreOffice PDF conversion)

## Canonical Inputs

- Profile source: `data/reference_data/profile/base_profile/profile_base_data.json`

The generator no longer uses `src/cv_generator/src/data/` as runtime source of truth.

## Outputs

All generated artifacts are job-scoped under:

- `data/pipelined_data/<source>/<job_id>/cv/rendered/`

Files:

- `cv.pdf` (final artifact in build flows)
- `cv.docx` (generated when using `--via docx`)
- `cv.tex` (generated when using `--via latex`)

## Commands

Preferred (CLI-first, ATS-first):

```bash
python src/cli/pipeline.py cv-build 201084 english --via docx --docx-template modern
python src/cli/pipeline.py cv-validate-ats 201084 --ats-target pdf
python src/cli/pipeline.py cv-pdf 201084 english --via docx --docx-template modern
```

Direct module commands (when needed):

```bash
python -m src.cv_generator status --job-id 201084
python -m src.cv_generator render english --job-id 201084 --via latex
python -m src.cv_generator build english --job-id 201084 --via docx --docx-template modern
python -m src.cv_generator validate-ats --job-id 201084 --ats-target pdf
python -m src.cv_generator test-template english --job-id 201084 --via docx --target docx --require-perfect
```

Arguments:

- `--job-id` defaults to `manual`
- `--source` defaults to `tu_berlin`
- `--via` defaults to `latex`
- `--docx-template classic|modern` selects built-in DOCX style profile
- `--docx-template-path` optional path to a real `.docx` file used as base template
- `--job-description` optional path used for ATS keyword matching (defaults to `data/pipelined_data/<source>/<job_id>/job.md` when present)
- `--with-ats` enables ATS report generation during render/build (ATS is otherwise a separate step)
- `--file-stem` selects rendered filename stem for ATS validation (default `cv`)
- `--ats-target docx|pdf` selects ATS extraction source (default `pdf`)
- `test-template` builds CV, compares `to_render.md` against deterministic extraction, and writes `cv/ats/template_test.json`
- `--target docx|pdf` selects artifact used for template score in `test-template`
- `--require-perfect` makes `test-template` fail unless score is exactly `100.0`
- `--ats-mode fallback|strict` controls ATS engine requirement policy
- `--ats-prompt` optional path to an LLM ATS prompt file (defaults to `data/reference_data/prompts/Academic_ATS_Prompt_Architecture.txt`)

## Notes

- Final output target is PDF.
- ATS-first recommendation: build via DOCX and validate ATS on final PDF.
- DOCX path supports style variants and optional real `.docx` templates.
- Render/build now auto-generates `data/pipelined_data/<source>/<job_id>/cv/to_render.md` as parity source.
- ATS reports are stored at `data/pipelined_data/<source>/<job_id>/cv/ats/report.json`.
- ATS deep dive: `docs/cv/ats_checker_deep_dive.md`.
- ATS now uses a dual engine report: `code` parser/readability checks + `llm` semantic scoring.
- In `fallback` mode, missing engines are tolerated and available engines are used.
- In `strict` mode, both engines must be available or the command fails.
- LaTeX rendering currently reuses legacy assets (`Einstellungen`, `Abbildungen`) from `src/cv_generator/DHIK_filled/` as compatibility support.
- The next cleanup step is moving those assets into a dedicated non-legacy location.

## Runtime Dependencies

- `python-docx` for DOCX rendering
- `pypdf` or `PyPDF2` for PDF text extraction in ATS checks
- `python-dotenv` for environment loading
- `spacy` for full deterministic analyzer quality (fallback path works without it)
- `libreoffice` (`soffice`) for DOCX -> PDF conversion (`--via docx`)
- `pdflatex` for LaTeX engine builds (`--via latex`)
