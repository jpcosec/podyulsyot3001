# Pipeline CLI

Unified command-line interface for the PhD application workflow.

## Command

```bash
python src/cli/pipeline.py <command>
```

## Main Commands

- `run`: execute multi-stage pipeline (fetch -> optional regenerate -> translate -> backup -> validate)
- `fetch`: run only scraper stage (`filtered` or `fixed`)
- `translate`: run only translation stage (`rules`, `deep`, `both`)
- `regenerate`: rebuild `job.md` files from local raw HTML
- `backup`: regenerate `data/reference_data/backup/backup_compendium.json`
- `cv-tailor`: generate `cv_tailoring.md` and job-local TeX CV sources under `data/pipelined_data/tu_berlin/<job_id>/latex/`
- `cv-render`: render final CV PDF (via `latex` or `docx`)
- `cv-build`: render/build final CV PDF (via `latex` or `docx`)
- `cv-validate-ats`: run ATS validation on `pdf` (default) or `docx`
- `cv-pdf`: shortcut for build + ATS validation (default engine `docx`, configurable)
- `cv-template-test`: build CV and run deterministic template parity scoring (`0-100%`)
- `status`: print pipeline health and artifact counts
- `validate`: fail if required per-job files are missing

## Examples

```bash
python src/cli/pipeline.py run
python src/cli/pipeline.py run --fetch filtered --translate rules --regenerate
python src/cli/pipeline.py cv-tailor 201084
python src/cli/pipeline.py cv-build 201084 english --via docx --docx-template modern
python src/cli/pipeline.py cv-render 201084 english --via docx --docx-template-path data/reference_data/application_assets/templates/cv_base_template.docx
python src/cli/pipeline.py cv-validate-ats 201084 --ats-target pdf
python src/cli/pipeline.py cv-pdf 201084 english --via docx --docx-template modern
python src/cli/pipeline.py cv-template-test 201084 english --via docx --docx-template modern --target docx --require-perfect
python src/cli/pipeline.py status
python src/cli/pipeline.py validate
```

Notes:

- Default CV behavior is final PDF generation.
- ATS-first recommendation is `--via docx`, then `cv-validate-ats --ats-target pdf`.
- `cv-template-test --target docx --require-perfect` enforces 100% deterministic parity for DOCX template testing.
- ATS is a separate step by default (`cv-validate-ats`).
- `--with-ats` can be used on `cv-render`/`cv-build` for immediate ATS execution.

Further docs:

- End-to-end flow: `docs/pipeline/end_to_end_pipeline_deep_dive.md`
- ATS checker internals: `docs/cv/ats_checker_deep_dive.md`
