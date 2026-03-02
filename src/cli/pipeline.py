#!/usr/bin/env python3
"""Unified CLI for the PhD application data pipeline."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
PIPELINE_ROOT = REPO_ROOT / "data" / "pipelined_data" / "tu_berlin"
MANIFEST_PATH = (
    REPO_ROOT / "data" / "reference_data" / "backup" / "backup_compendium.json"
)
COMMENT_PATTERN = re.compile(r"<!--(.*?)-->", flags=re.DOTALL)

FETCH_SCRIPTS = {
    "filtered": "src/scraper/fetch_all_filtered_jobs.py",
    "fixed": "src/scraper/fetch_and_parse_all.py",
}

SINGLE_URL_SCRAPER = "src/scraper/scrape_single_url.py"

TRANSLATE_SCRIPTS = {
    "rules": "src/scraper/translate_markdowns.py",
    "deep": "src/scraper/deep_translate_jobs.py",
}


def run_python_script(
    script_relative_path: str, extra_args: list[str] | None = None
) -> None:
    command = [sys.executable, str(REPO_ROOT / script_relative_path)]
    if extra_args:
        command.extend(extra_args)
    print(f"[run] {' '.join(command)}")
    subprocess.run(command, check=True)


def run_cv_command(args: list[str]) -> None:
    command = [sys.executable, "-m", "src.cv_generator", *args]
    print(f"[run] {' '.join(command)}")
    subprocess.run(command, check=True, cwd=REPO_ROOT)


def run_fetch(mode: str) -> None:
    run_python_script(FETCH_SCRIPTS[mode])


def run_fetch_url(urls: list[str], source: str, strict_english: bool) -> None:
    extra_args = [*urls, "--source", source]
    if strict_english:
        extra_args.append("--strict-english")
    run_python_script(SINGLE_URL_SCRAPER, extra_args=extra_args)


def run_translate(mode: str) -> None:
    if mode in {"rules", "both"}:
        run_python_script(TRANSLATE_SCRIPTS["rules"])
    if mode in {"deep", "both"}:
        run_python_script(TRANSLATE_SCRIPTS["deep"])


def run_regenerate() -> None:
    run_python_script("src/scraper/generate_populated_tracker.py")


def run_backup() -> None:
    run_python_script("src/utils/build_backup_compendium.py")


def ensure_repo_import_path() -> None:
    repo_root_str = str(REPO_ROOT)
    if repo_root_str not in sys.path:
        sys.path.insert(0, repo_root_str)


def warn_if_not_phd_cv_env() -> None:
    env_name = os.getenv("CONDA_DEFAULT_ENV", "")
    in_phd_cv_executable = "/envs/phd-cv/" in sys.executable
    if env_name == "phd-cv" or in_phd_cv_executable:
        return

    print("[warn] Recommended environment for this pipeline is conda env 'phd-cv'.")
    print("[warn] Use: conda run -n phd-cv python src/cli/pipeline.py <command>")


def get_pipeline_root_for_source(source: str) -> Path:
    return REPO_ROOT / "data" / "pipelined_data" / source


def get_job_dir(source: str, job_id: str) -> Path:
    return get_pipeline_root_for_source(source) / job_id


def get_app_dirs(job_dir: Path) -> dict[str, Path]:
    output_root = job_dir / "output"
    return {
        "output_root": output_root,
        "prep": output_root / "prep",
        "review": output_root / "review",
        "final": output_root / "final",
        "reports": output_root / "reports",
        "state": output_root / "state.md",
    }


def ensure_app_dirs(job_dir: Path) -> dict[str, Path]:
    dirs = get_app_dirs(job_dir)
    for key in ("output_root", "prep", "review", "final", "reports"):
        dirs[key].mkdir(parents=True, exist_ok=True)
    return dirs


def copy_into(src: Path, dst: Path) -> Path:
    if not src.exists():
        raise FileNotFoundError(f"Expected artifact not found: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return dst


def append_state_entry(
    state_path: Path,
    stage: str,
    target: str,
    status: str,
    details: list[str],
) -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    if not state_path.exists():
        state_path.write_text(
            "# Application Pipeline State\n\n"
            "This file tracks the prepare -> review -> renderize workflow.\n\n",
            encoding="utf-8",
        )

    lines = [
        f"## {timestamp} | stage={stage} | target={target} | status={status}",
    ]
    lines.extend([f"- {item}" for item in details])
    lines.append("")

    with state_path.open("a", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def write_prep_instructions(prep_dir: Path) -> Path:
    path = prep_dir / "README.md"
    content = (
        "# Prep Review Instructions\n\n"
        "Add review notes as HTML comments inside prep markdown files.\n"
        "Example: `<!-- clarify this claim with proof link -->`\n\n"
        "Flow:\n"
        "1. Run `app-prepare`\n"
        "2. Add comments in `output/prep/**/*.md`\n"
        "3. Run `app-review` to collect unresolved comments\n"
        "4. Remove comments after applying corrections\n"
        "5. Run `app-renderize` when review reports zero comments\n"
    )
    path.write_text(content, encoding="utf-8")
    return path


def collect_prep_comments(prep_dir: Path, target: str = "all") -> list[dict[str, str]]:
    comments: list[dict[str, str]] = []
    for file_path in sorted(prep_dir.rglob("*.md")):
        if file_path.name.lower() == "readme.md":
            continue
        relative = file_path.relative_to(prep_dir)
        if target != "all":
            if not relative.parts or relative.parts[0] != target:
                continue
        text = file_path.read_text(encoding="utf-8")
        for match in COMMENT_PATTERN.finditer(text):
            comment = match.group(1).strip()
            if not comment:
                continue
            comments.append(
                {
                    "file": relative.as_posix(),
                    "comment": comment,
                }
            )
    return comments


def write_review_comments(review_dir: Path, comments: list[dict[str, str]]) -> Path:
    path = review_dir / "comments.md"
    lines = ["# Review Comments", ""]
    if not comments:
        lines.append("No unresolved HTML comments found in prep artifacts.")
    else:
        lines.append(f"Found {len(comments)} unresolved comments:")
        lines.append("")
        for index, item in enumerate(comments, start=1):
            lines.append(f"{index}. `{item['file']}`")
            lines.append(f"   - {item['comment']}")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    return path


def write_json_report(path: Path, payload: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )
    return path


def parse_state_entries(state_path: Path) -> list[dict[str, str]]:
    if not state_path.exists():
        return []

    pattern = re.compile(
        r"^##\s+(?P<timestamp>.+?)\s+\|\s+stage=(?P<stage>[^|]+)\s+\|\s+target=(?P<target>[^|]+)\s+\|\s+status=(?P<status>[^|]+)$"
    )
    entries: list[dict[str, str]] = []
    for raw_line in state_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        match = pattern.match(line)
        if not match:
            continue
        payload = {key: value.strip() for key, value in match.groupdict().items()}
        entries.append(payload)
    return entries


def run_app_status(job_id: str, source: str, target: str) -> int:
    warn_if_not_phd_cv_env()
    job_dir = get_job_dir(source, job_id)
    dirs = get_app_dirs(job_dir)

    entries = parse_state_entries(dirs["state"])
    if not entries:
        print(
            f"[status] no state found for source={source} job_id={job_id}. "
            "Run app-prepare first."
        )
        return 1

    latest_by_stage: dict[str, dict[str, str]] = {}
    for entry in entries:
        latest_by_stage[entry["stage"]] = entry

    unresolved_comments = 0
    prep_dir = dirs["prep"]
    if prep_dir.exists():
        unresolved_comments = len(collect_prep_comments(prep_dir, target=target))

    last = entries[-1]
    print(f"[status] source={source} job_id={job_id} target={target}")
    print(f"[status] latest stage={last['stage']} status={last['status']}")
    for stage_name in ("prepare", "review", "renderize"):
        entry = latest_by_stage.get(stage_name)
        if not entry:
            print(f"[status] {stage_name}: not_started")
            continue
        print(f"[status] {stage_name}: {entry['status']} at {entry['timestamp']}")
    print(f"[status] unresolved prep comments: {unresolved_comments}")
    print(f"[status] state file: {dirs['state']}")
    return 0


def build_jobs_index(source: str = "all") -> dict[str, list[str]]:
    root = REPO_ROOT / "data" / "pipelined_data"
    if not root.exists():
        return {}

    source_dirs = [path for path in root.iterdir() if path.is_dir()]
    index: dict[str, list[str]] = {}
    for source_dir in sorted(source_dirs):
        source_name = source_dir.name
        if source != "all" and source_name != source:
            continue
        job_ids = sorted(
            [
                path.name
                for path in source_dir.iterdir()
                if path.is_dir() and path.name.isdigit()
            ]
        )
        if job_ids:
            index[source_name] = job_ids
    return index


def write_jobs_index_reports(index: dict[str, list[str]]) -> tuple[Path, Path]:
    root = REPO_ROOT / "data" / "pipelined_data"
    json_path = root / "job_ids_index.json"
    md_path = root / "job_ids_index.md"

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "sources": [
            {"source": source, "count": len(job_ids), "job_ids": job_ids}
            for source, job_ids in sorted(index.items())
        ],
    }
    json_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Job IDs Index",
        "",
        f"Generated at: {payload['generated_at_utc']}",
        "",
    ]
    if not index:
        lines.append("No job folders found.")
    else:
        for source_name, job_ids in sorted(index.items()):
            lines.append(f"## {source_name} ({len(job_ids)} jobs)")
            lines.append("")
            lines.extend([f"- {job_id}" for job_id in job_ids])
            lines.append("")
    md_path.write_text("\n".join(lines), encoding="utf-8")
    return json_path, md_path


def run_jobs_index(source: str) -> int:
    index = build_jobs_index(source=source)
    json_path, md_path = write_jobs_index_reports(index)
    total_jobs = sum(len(ids) for ids in index.values())
    print(f"[done] indexed {total_jobs} jobs across {len(index)} source folder(s)")
    print(f"[done] wrote {json_path}")
    print(f"[done] wrote {md_path}")
    return 0


def run_motivation_pre(job_id: str, source: str, output_name: str) -> Path:
    warn_if_not_phd_cv_env()
    ensure_repo_import_path()
    from src.motivation_letter import MotivationLetterService

    service = MotivationLetterService()
    result = service.create_pre_letter(
        job_id=job_id,
        source=source,
        output_name=output_name,
    )
    print(f"[done] wrote {result.pre_letter_path}")
    print(f"[done] wrote {result.analysis_path}")
    print(f"[done] updated {result.evidence_bank_path}")
    return result.pre_letter_path


def run_motivation_build(
    job_id: str,
    source: str,
    output_name: str,
    skip_pdf: bool,
    skip_email: bool,
) -> Path:
    warn_if_not_phd_cv_env()
    ensure_repo_import_path()
    from src.motivation_letter import MotivationLetterService

    service = MotivationLetterService()
    result = service.generate_for_job(
        job_id=job_id,
        source=source,
        output_name=output_name,
    )
    print(f"[done] wrote {result.letter_path}")
    print(f"[done] wrote {result.analysis_path}")

    if not skip_pdf:
        pdf_result = service.build_pdf_for_job(
            job_id=job_id,
            source=source,
            letter_name=output_name,
            pdf_name=f"{Path(output_name).stem}.pdf",
        )
        print(f"[done] wrote {pdf_result.pdf_path}")

    if not skip_email:
        email_result = service.generate_email_draft(job_id=job_id, source=source)
        print(f"[done] wrote {email_result.email_path}")

    return result.letter_path


def run_app_prepare(job_id: str, source: str, target: str, ats_mode: str) -> int:
    warn_if_not_phd_cv_env()
    ensure_repo_import_path()

    from src.cv_generator.__main__ import (
        build_to_render_markdown,
        load_canonical_context,
    )
    from src.cv_generator.ats import run_ats_analysis
    from src.cv_generator.config import CVConfig
    from src.motivation_letter import MotivationLetterService

    job_dir = get_job_dir(source, job_id)
    job_md = job_dir / "job.md"
    if not job_md.exists():
        raise FileNotFoundError(f"job.md not found for source={source} job_id={job_id}")

    dirs = ensure_app_dirs(job_dir)
    instructions = write_prep_instructions(dirs["prep"])
    details = [f"Prep instructions: {instructions}"]
    job_description = job_md.read_text(encoding="utf-8")

    if target in {"motivation", "all"}:
        service = MotivationLetterService()
        pre_result = service.create_pre_letter(job_id=job_id, source=source)
        prep_motivation_dir = dirs["prep"] / "motivation"
        prep_letter = copy_into(
            pre_result.pre_letter_path,
            prep_motivation_dir / "motivation_letter.pre.md",
        )
        copy_into(
            pre_result.analysis_path,
            prep_motivation_dir / "motivation_letter.pre.analysis.json",
        )
        motivation_text = prep_letter.read_text(encoding="utf-8")
        motivation_ats = run_ats_analysis(
            cv_text=motivation_text,
            job_description=job_description,
            ats_mode=ats_mode,
        )
        motivation_ats["stage"] = "prepare"
        motivation_ats["target"] = "motivation"
        write_json_report(dirs["reports"] / "motivation_ats_pre.json", motivation_ats)
        details.append(f"Prepared motivation pre-file: {prep_letter}")

    if target in {"cv", "all"}:
        cv_config = CVConfig.from_defaults()
        model = load_canonical_context(cv_config)
        cv_to_render = build_to_render_markdown(model)
        prep_cv_dir = dirs["prep"] / "cv"
        prep_cv_dir.mkdir(parents=True, exist_ok=True)
        prep_cv_path = prep_cv_dir / "cv.to_render.md"
        prep_cv_path.write_text(cv_to_render, encoding="utf-8")

        tailoring_path = build_cv_tailoring(job_id=job_id, source=source)
        copy_into(tailoring_path, prep_cv_dir / "cv_tailoring.md")

        cv_ats = run_ats_analysis(
            cv_text=cv_to_render,
            job_description=job_description,
            ats_mode=ats_mode,
        )
        cv_ats["stage"] = "prepare"
        cv_ats["target"] = "cv"
        write_json_report(dirs["reports"] / "cv_ats_pre.json", cv_ats)
        details.append(f"Prepared CV pre-files under: {prep_cv_dir}")

    append_state_entry(
        state_path=dirs["state"],
        stage="prepare",
        target=target,
        status="ready_for_review",
        details=details,
    )
    print(f"[done] prep artifacts available at {dirs['prep']}")
    return 0


def run_app_review(job_id: str, source: str, target: str) -> int:
    warn_if_not_phd_cv_env()
    ensure_repo_import_path()

    job_dir = get_job_dir(source, job_id)
    dirs = ensure_app_dirs(job_dir)
    comments = collect_prep_comments(dirs["prep"], target=target)
    comments_path = write_review_comments(dirs["review"], comments)

    status = "needs_corrections" if comments else "ready_to_renderize"
    details = [
        f"Review report: {comments_path}",
        f"Unresolved comments: {len(comments)}",
    ]
    append_state_entry(
        state_path=dirs["state"],
        stage="review",
        target=target,
        status=status,
        details=details,
    )

    if comments:
        print(f"[review] found {len(comments)} unresolved comments")
        print(f"[review] details: {comments_path}")
        return 1

    print("[review] no unresolved comments found; ready to renderize")
    print(f"[review] details: {comments_path}")
    return 0


def run_app_renderize(
    job_id: str,
    source: str,
    target: str,
    ats_mode: str,
    language: str,
    via: str,
    docx_template: str,
    docx_template_path: str | None,
) -> int:
    warn_if_not_phd_cv_env()
    ensure_repo_import_path()

    from src.cv_generator.ats import run_ats_analysis
    from src.motivation_letter import MotivationLetterService
    from src.render.pdf import extract_docx_text, extract_pdf_text

    job_dir = get_job_dir(source, job_id)
    job_md = job_dir / "job.md"
    if not job_md.exists():
        raise FileNotFoundError(f"job.md not found for source={source} job_id={job_id}")
    dirs = ensure_app_dirs(job_dir)

    comments = collect_prep_comments(dirs["prep"], target=target)
    if comments:
        comments_path = write_review_comments(dirs["review"], comments)
        raise RuntimeError(
            "Cannot renderize while prep comments are unresolved. "
            + f"See {comments_path}"
        )

    details: list[str] = []
    job_description = job_md.read_text(encoding="utf-8")

    if target in {"motivation", "all"}:
        service = MotivationLetterService()
        generation = service.generate_for_job(job_id=job_id, source=source)
        pdf_result = service.build_pdf_for_job(
            job_id=job_id,
            source=source,
            letter_name=generation.letter_path.name,
            pdf_name="motivation_letter.pdf",
        )
        email_result = service.generate_email_draft(job_id=job_id, source=source)

        final_motivation_dir = dirs["final"] / "motivation"
        final_markdown = copy_into(
            generation.letter_path,
            final_motivation_dir / "motivation_letter.md",
        )
        final_pdf = copy_into(
            pdf_result.pdf_path,
            final_motivation_dir / "motivation_letter.pdf",
        )
        final_email = copy_into(
            email_result.email_path,
            final_motivation_dir / "application_email.md",
        )

        motivation_text = extract_pdf_text(final_pdf)
        motivation_ats = run_ats_analysis(
            cv_text=motivation_text,
            job_description=job_description,
            ats_mode=ats_mode,
        )
        motivation_ats["stage"] = "renderize"
        motivation_ats["target"] = "motivation"
        motivation_ats["artifact"] = str(final_pdf)
        write_json_report(
            dirs["reports"] / "motivation_ats_final.json",
            motivation_ats,
        )
        details.extend(
            [
                f"Final motivation markdown: {final_markdown}",
                f"Final motivation pdf: {final_pdf}",
                f"Final application email draft: {final_email}",
            ]
        )

    if target in {"cv", "all"}:
        run_cv_build(
            job_id=job_id,
            source=source,
            language=language,
            via=via,
            docx_template=docx_template,
            docx_template_path=docx_template_path,
            with_ats=False,
        )

        cv_render_dir = job_dir / "cv" / "rendered" / via
        cv_docx = cv_render_dir / "cv.docx"
        cv_pdf = cv_render_dir / "cv.pdf"
        cv_to_render = job_dir / "cv" / "to_render.md"

        final_cv_dir = dirs["final"] / "cv"
        if cv_to_render.exists():
            copy_into(cv_to_render, final_cv_dir / "cv.to_render.md")
        if cv_docx.exists():
            copy_into(cv_docx, final_cv_dir / "cv.docx")
        if cv_pdf.exists():
            final_cv_pdf = copy_into(cv_pdf, final_cv_dir / "cv.pdf")
            cv_text = extract_pdf_text(final_cv_pdf)
            cv_artifact = final_cv_pdf
        elif cv_docx.exists():
            final_cv_docx = final_cv_dir / "cv.docx"
            cv_text = extract_docx_text(final_cv_docx)
            cv_artifact = final_cv_docx
        else:
            raise FileNotFoundError("No CV artifacts found after render/build")

        cv_ats = run_ats_analysis(
            cv_text=cv_text,
            job_description=job_description,
            ats_mode=ats_mode,
        )
        cv_ats["stage"] = "renderize"
        cv_ats["target"] = "cv"
        cv_ats["artifact"] = str(cv_artifact)
        write_json_report(dirs["reports"] / "cv_ats_final.json", cv_ats)
        details.append(f"Final CV artifacts: {final_cv_dir}")

    append_state_entry(
        state_path=dirs["state"],
        stage="renderize",
        target=target,
        status="completed",
        details=details,
    )
    print(f"[done] final artifacts available at {dirs['final']}")
    return 0


def run_app_run(
    job_id: str,
    source: str,
    target: str,
    ats_mode: str,
    language: str,
    via: str,
    docx_template: str,
    docx_template_path: str | None,
) -> int:
    print(f"[stage] app-prepare ({target})")
    prepare_code = run_app_prepare(
        job_id=job_id,
        source=source,
        target=target,
        ats_mode=ats_mode,
    )
    if prepare_code != 0:
        return prepare_code

    print(f"[stage] app-review ({target})")
    review_code = run_app_review(
        job_id=job_id,
        source=source,
        target=target,
    )
    if review_code != 0:
        print(
            "[error] app-run stopped at review stage. "
            "Resolve comments in output/prep and rerun."
        )
        return review_code

    print(f"[stage] app-renderize ({target})")
    return run_app_renderize(
        job_id=job_id,
        source=source,
        target=target,
        ats_mode=ats_mode,
        language=language,
        via=via,
        docx_template=docx_template,
        docx_template_path=docx_template_path,
    )


def run_apply_to(args):
    """Guided application workflow: scrape -> plan -> review -> execute."""
    from src.agent.orchestrator import ApplicationAgent

    agent = ApplicationAgent()
    urls = args.urls

    # -- Phase 1: Scrape and Plan ------------------------------------------------
    print(f"\n{'=' * 60}")
    print(f"  PHASE 1: Scraping {len(urls)} job(s) and analyzing fit")
    print(f"{'=' * 60}\n")

    batch = agent.plan(urls)

    print(f"\nFound {len(batch.plans)} viable job(s), skipped {len(batch.skipped)}.")
    print(f"Batch report: {agent.config.pipeline_root / 'batch_report.md'}")

    if not batch.plans:
        print("No jobs to apply to. Exiting.")
        return

    # Print summary
    for plan in batch.plans:
        marker = ">>>" if plan.fit.recommendation == "strong_apply" else "  >"
        print(
            f"  {marker} [{plan.priority}] {plan.job.title} — score {plan.fit.overall_score}/100 ({plan.fit.recommendation})"
        )

    if batch.skipped:
        print(f"\n  Skipped:")
        for s in batch.skipped:
            print(
                f"      {s.get('job', {}).get('title', '?')} — score {s.get('score', '?')}"
            )

    # -- Human Checkpoint 1 ------------------------------------------------------
    if not args.auto:
        print(
            f"\nReview the batch report, then press Enter to continue (or Ctrl+C to abort)..."
        )
        input()

    # -- Phase 2: Execute Each Plan ----------------------------------------------
    for plan in batch.plans:
        job_id = plan.job.reference_number or "manual"
        print(f"\n{'=' * 60}")
        print(f"  PHASE 2: Processing {plan.job.title} ({job_id})")
        print(f"{'=' * 60}\n")

        try:
            results = agent.execute_plan(
                plan,
                source=args.source,
                via=args.via,
                docx_template=args.docx_template,
            )

            print(f"\n  Results for {job_id}:")
            print(f"    CV:          {results.get('cv_pdf', 'N/A')}")
            print(f"    Letter:      {results.get('letter_pdf', 'N/A')}")
            print(f"    ATS Score:   {results.get('ats_score', 'N/A')}")
            print(f"    Tailoring:   {results.get('tailoring', 'N/A')}")

        except Exception as e:
            print(f"\n  ERROR processing {job_id}: {e}")
            print(f"  Continuing with next job...\n")
            continue

        # -- Human Checkpoint 2 (per job) ----------------------------------------
        if not args.auto and plan != batch.plans[-1]:
            print(
                f"\nReview outputs for {job_id}, then press Enter for next job (or Ctrl+C to stop)..."
            )
            input()

    # -- Summary -----------------------------------------------------------------
    print(f"\n{'=' * 60}")
    print(f"  DONE — Processed {len(batch.plans)} application(s)")
    print(f"{'=' * 60}")
    print(f"\nNext steps:")
    print(
        f"  1. Review generated documents in data/pipelined_data/{args.source}/<job_id>/"
    )
    print(f"  2. Run 'pipeline.py cv-validate-ats <job_id>' for detailed ATS reports")
    print(f"  3. Merge final PDFs with 'python src/utils/pdf_merger.py'")


def run_cv_render(
    job_id: str,
    source: str,
    language: str,
    via: str,
    docx_template: str,
    docx_template_path: str | None,
    with_ats: bool,
) -> None:
    cmd = [
        "render",
        language,
        "--job-id",
        job_id,
        "--source",
        source,
        "--via",
        via,
        "--docx-template",
        docx_template,
    ]
    if docx_template_path:
        cmd.extend(["--docx-template-path", docx_template_path])
    if with_ats:
        cmd.append("--with-ats")
    run_cv_command(cmd)


def run_cv_build(
    job_id: str,
    source: str,
    language: str,
    via: str,
    docx_template: str,
    docx_template_path: str | None,
    with_ats: bool,
) -> None:
    cmd = [
        "build",
        language,
        "--job-id",
        job_id,
        "--source",
        source,
        "--via",
        via,
        "--docx-template",
        docx_template,
    ]
    if docx_template_path:
        cmd.extend(["--docx-template-path", docx_template_path])
    if with_ats:
        cmd.append("--with-ats")
    run_cv_command(cmd)


def run_cv_validate_ats(
    job_id: str, source: str, file_stem: str, ats_target: str, via: str = "docx"
) -> None:
    run_cv_command(
        [
            "validate-ats",
            "--job-id",
            job_id,
            "--source",
            source,
            "--file-stem",
            file_stem,
            "--ats-target",
            ats_target,
            "--via",
            via,
        ]
    )


def run_cv_pdf_pipeline(
    job_id: str,
    source: str,
    language: str,
    file_stem: str,
    via: str,
    docx_template: str,
    docx_template_path: str | None,
) -> None:
    run_cv_build(
        job_id=job_id,
        source=source,
        language=language,
        via=via,
        docx_template=docx_template,
        docx_template_path=docx_template_path,
        with_ats=False,
    )
    run_cv_validate_ats(
        job_id=job_id, source=source, file_stem=file_stem, ats_target="pdf", via=via
    )


def run_cv_template_test(
    job_id: str,
    source: str,
    language: str,
    via: str,
    docx_template: str,
    docx_template_path: str | None,
    file_stem: str,
    target: str,
    require_perfect: bool,
) -> None:
    cmd = [
        "test-template",
        language,
        "--job-id",
        job_id,
        "--source",
        source,
        "--via",
        via,
        "--docx-template",
        docx_template,
        "--file-stem",
        file_stem,
        "--target",
        target,
    ]
    if docx_template_path:
        cmd.extend(["--docx-template-path", docx_template_path])
    if require_perfect:
        cmd.append("--require-perfect")
    run_cv_command(cmd)


def build_cv_tailoring(job_id: str, source: str = "tu_berlin") -> Path:
    from src.cv_generator.pipeline import CVTailoringPipeline

    pipeline = CVTailoringPipeline()
    pipeline.execute(job_id=job_id, source=source)
    return get_job_dir(source, job_id) / "planning" / "cv_tailoring.md"


def collect_pipeline_stats() -> tuple[int, int, dict[str, list[str]], bool]:
    if not PIPELINE_ROOT.exists():
        return 0, 0, {}, False

    required_files = ("raw.html", "proposal_text.md", "job.md", "summary.json")
    job_dirs = sorted(
        path
        for path in PIPELINE_ROOT.iterdir()
        if path.is_dir() and path.name.isdigit()
    )
    missing_by_job: dict[str, list[str]] = {}

    for job_dir in job_dirs:
        missing = [name for name in required_files if not (job_dir / name).exists()]
        if missing:
            missing_by_job[job_dir.name] = missing

    summary_exists = (PIPELINE_ROOT / "summary.csv").exists()
    return (
        len(job_dirs),
        len(job_dirs) - len(missing_by_job),
        missing_by_job,
        summary_exists,
    )


def print_pipeline_status() -> tuple[int, int, dict[str, list[str]], bool]:
    total, complete, missing_by_job, summary_exists = collect_pipeline_stats()
    print(f"[status] pipeline root: {PIPELINE_ROOT}")
    print(f"[status] total job directories: {total}")
    print(f"[status] complete job directories: {complete}")
    print(f"[status] summary.csv present: {summary_exists}")
    print(f"[status] backup manifest present: {MANIFEST_PATH.exists()}")

    if missing_by_job:
        print("[status] missing required files:")
        for job_id, files in missing_by_job.items():
            print(f"  - {job_id}: {', '.join(files)}")

    return total, complete, missing_by_job, summary_exists


def handle_run(args: argparse.Namespace) -> int:
    if args.fetch != "skip":
        print(f"[stage] fetch ({args.fetch})")
        run_fetch(args.fetch)

    if args.regenerate:
        print("[stage] regenerate")
        run_regenerate()

    if args.translate != "skip":
        print(f"[stage] translate ({args.translate})")
        run_translate(args.translate)

    if not args.skip_backup:
        print("[stage] backup manifest")
        run_backup()

    if not args.skip_validate:
        print("[stage] validate")
        _, _, missing_by_job, summary_exists = print_pipeline_status()
        if missing_by_job or not summary_exists:
            print("[error] pipeline validation failed")
            return 1

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="PhD application pipeline CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run a full pipeline sequence")
    run_parser.add_argument(
        "--fetch",
        choices=["filtered", "fixed", "skip"],
        default="filtered",
        help="Fetch mode for job scraping",
    )
    run_parser.add_argument(
        "--translate",
        choices=["rules", "deep", "both", "skip"],
        default="rules",
        help="Translation stage mode",
    )
    run_parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Regenerate job.md files from existing raw HTML",
    )
    run_parser.add_argument(
        "--skip-backup",
        action="store_true",
        help="Skip backup compendium manifest generation",
    )
    run_parser.add_argument(
        "--skip-validate",
        action="store_true",
        help="Skip post-run validation",
    )

    fetch_parser = subparsers.add_parser("fetch", help="Run only fetch stage")
    fetch_parser.add_argument("mode", choices=["filtered", "fixed"], help="Fetch mode")

    fetch_url_parser = subparsers.add_parser(
        "fetch-url",
        help="Deterministically fetch and extract one job URL",
    )
    fetch_url_parser.add_argument("urls", nargs="+", help="One or more full job URLs")
    fetch_url_parser.add_argument(
        "--source", default="tu_berlin", help="Pipeline source namespace"
    )
    fetch_url_parser.add_argument(
        "--strict-english",
        action="store_true",
        help="Fail if extracted text is not confidently English",
    )

    apply_parser = subparsers.add_parser(
        "apply-to",
        help="Scrape job URLs, analyze fit, and generate application documents",
    )
    apply_parser.add_argument(
        "urls",
        nargs="+",
        help="One or more job posting URLs to process",
    )
    apply_parser.add_argument(
        "--source",
        default="tu_berlin",
        help="Source namespace (default: tu_berlin)",
    )
    apply_parser.add_argument(
        "--auto",
        action="store_true",
        help="Skip human review checkpoints (not recommended)",
    )
    apply_parser.add_argument(
        "--via",
        default="docx",
        choices=["docx", "latex"],
        help="CV rendering engine (default: docx)",
    )
    apply_parser.add_argument(
        "--docx-template",
        default="modern",
        choices=["classic", "modern", "harvard", "executive"],
        help="DOCX template style (default: modern)",
    )

    translate_parser = subparsers.add_parser(
        "translate", help="Run only translation stage"
    )
    translate_parser.add_argument(
        "mode", choices=["rules", "deep", "both"], help="Translation mode"
    )

    subparsers.add_parser("regenerate", help="Regenerate trackers from local raw HTML")
    subparsers.add_parser("backup", help="Regenerate backup compendium manifest")
    cv_parser = subparsers.add_parser(
        "cv-tailor", help="Generate CV tailoring brief for a job"
    )
    cv_parser.add_argument(
        "job_id", help="Numeric job id under data/pipelined_data/tu_berlin"
    )
    cv_parser.add_argument(
        "--source", default="tu_berlin", help="Pipeline source namespace"
    )
    motivation_pre_parser = subparsers.add_parser(
        "motivation-pre",
        help="Generate synthetic motivation-letter pre-scaffold",
    )
    motivation_pre_parser.add_argument(
        "job_id", help="Job id under data/pipelined_data/<source>"
    )
    motivation_pre_parser.add_argument(
        "--source", default="tu_berlin", help="Pipeline source namespace"
    )
    motivation_pre_parser.add_argument(
        "--output-name",
        default="motivation_letter.pre.md",
        help="Pre-letter output filename under planning/",
    )

    motivation_build_parser = subparsers.add_parser(
        "motivation-build",
        help="Generate final motivation letter from pre-scaffold",
    )
    motivation_build_parser.add_argument(
        "job_id", help="Job id under data/pipelined_data/<source>"
    )
    motivation_build_parser.add_argument(
        "--source", default="tu_berlin", help="Pipeline source namespace"
    )
    motivation_build_parser.add_argument(
        "--output-name",
        default="motivation_letter.md",
        help="Final letter output filename under planning/",
    )
    motivation_build_parser.add_argument(
        "--skip-pdf",
        action="store_true",
        help="Skip PDF generation for the motivation letter",
    )
    motivation_build_parser.add_argument(
        "--skip-email",
        action="store_true",
        help="Skip generation of the application email draft",
    )

    app_prepare_parser = subparsers.add_parser(
        "app-prepare",
        help="Prepare CV/motivation artifacts in output/prep",
    )
    app_prepare_parser.add_argument(
        "job_id", help="Job id under data/pipelined_data/<source>"
    )
    app_prepare_parser.add_argument(
        "--source", default="tu_berlin", help="Pipeline source namespace"
    )
    app_prepare_parser.add_argument(
        "--target",
        choices=["motivation", "cv", "all"],
        default="all",
        help="Target artifact scope",
    )
    app_prepare_parser.add_argument(
        "--ats-mode",
        choices=["fallback", "strict"],
        default="fallback",
        help="ATS mode for prep-stage analysis",
    )

    app_review_parser = subparsers.add_parser(
        "app-review",
        help="Collect HTML comments from output/prep for correction flow",
    )
    app_review_parser.add_argument(
        "job_id", help="Job id under data/pipelined_data/<source>"
    )
    app_review_parser.add_argument(
        "--source", default="tu_berlin", help="Pipeline source namespace"
    )
    app_review_parser.add_argument(
        "--target",
        choices=["motivation", "cv", "all"],
        default="all",
        help="Target artifact scope",
    )

    app_status_parser = subparsers.add_parser(
        "app-status",
        help="Show current prepare/review/renderize state for one job",
    )
    app_status_parser.add_argument(
        "job_id", help="Job id under data/pipelined_data/<source>"
    )
    app_status_parser.add_argument(
        "--source", default="tu_berlin", help="Pipeline source namespace"
    )
    app_status_parser.add_argument(
        "--target",
        choices=["motivation", "cv", "all"],
        default="all",
        help="Target artifact scope for unresolved comment count",
    )

    app_renderize_parser = subparsers.add_parser(
        "app-renderize",
        help="Render final artifacts from prep when review has zero comments",
    )
    app_renderize_parser.add_argument(
        "job_id", help="Job id under data/pipelined_data/<source>"
    )
    app_renderize_parser.add_argument(
        "--source", default="tu_berlin", help="Pipeline source namespace"
    )
    app_renderize_parser.add_argument(
        "--target",
        choices=["motivation", "cv", "all"],
        default="all",
        help="Target artifact scope",
    )
    app_renderize_parser.add_argument(
        "--ats-mode",
        choices=["fallback", "strict"],
        default="fallback",
        help="ATS mode for render-stage analysis",
    )
    app_renderize_parser.add_argument(
        "--language",
        choices=["german", "english", "spanish"],
        default="english",
        help="CV language used when target includes cv",
    )
    app_renderize_parser.add_argument(
        "--via",
        choices=["latex", "docx"],
        default="docx",
        help="CV rendering engine used when target includes cv",
    )
    app_renderize_parser.add_argument(
        "--docx-template",
        choices=["classic", "modern", "harvard", "executive"],
        default="modern",
        help="DOCX renderer style used when target includes cv and --via docx",
    )
    app_renderize_parser.add_argument(
        "--docx-template-path",
        default=None,
        help="Optional path to .docx file used as base template",
    )

    app_run_parser = subparsers.add_parser(
        "app-run",
        help="Run app-prepare + app-review + app-renderize in one command",
    )
    app_run_parser.add_argument(
        "job_id", help="Job id under data/pipelined_data/<source>"
    )
    app_run_parser.add_argument(
        "--source", default="tu_berlin", help="Pipeline source namespace"
    )
    app_run_parser.add_argument(
        "--target",
        choices=["motivation", "cv", "all"],
        default="all",
        help="Target artifact scope",
    )
    app_run_parser.add_argument(
        "--ats-mode",
        choices=["fallback", "strict"],
        default="fallback",
        help="ATS mode for both prep and renderize stages",
    )
    app_run_parser.add_argument(
        "--language",
        choices=["german", "english", "spanish"],
        default="english",
        help="CV language used when target includes cv",
    )
    app_run_parser.add_argument(
        "--via",
        choices=["latex", "docx"],
        default="docx",
        help="CV rendering engine used when target includes cv",
    )
    app_run_parser.add_argument(
        "--docx-template",
        choices=["classic", "modern", "harvard", "executive"],
        default="modern",
        help="DOCX renderer style used when target includes cv and --via docx",
    )
    app_run_parser.add_argument(
        "--docx-template-path",
        default=None,
        help="Optional path to .docx file used as base template",
    )

    jobs_index_parser = subparsers.add_parser(
        "jobs-index",
        help="Generate central job_id index by source folder",
    )
    jobs_index_parser.add_argument(
        "--source",
        default="all",
        help="Source folder name or 'all'",
    )

    subparsers.add_parser("status", help="Show pipeline status summary")
    subparsers.add_parser("validate", help="Validate required per-job pipeline files")

    cv_render_parser = subparsers.add_parser(
        "cv-render", help="Render CV artifacts via CV generator CLI"
    )
    cv_render_parser.add_argument(
        "job_id", help="Job id under data/pipelined_data/tu_berlin"
    )
    cv_render_parser.add_argument(
        "language", choices=["german", "english", "spanish"], help="CV language"
    )
    cv_render_parser.add_argument(
        "--source", default="tu_berlin", help="Pipeline source namespace"
    )
    cv_render_parser.add_argument(
        "--via",
        choices=["latex", "docx"],
        default="latex",
        help="Engine used to produce final PDF",
    )
    cv_render_parser.add_argument(
        "--docx-template",
        choices=["classic", "modern", "harvard", "executive"],
        default="classic",
        help="DOCX renderer style (used when --via docx)",
    )
    cv_render_parser.add_argument(
        "--docx-template-path",
        default=None,
        help="Optional path to .docx file used as base template",
    )
    cv_render_parser.add_argument(
        "--with-ats",
        action="store_true",
        help="Also run ATS immediately after rendering",
    )

    cv_build_parser = subparsers.add_parser(
        "cv-build", help="Build CV artifacts via CV generator CLI"
    )
    cv_build_parser.add_argument(
        "job_id", help="Job id under data/pipelined_data/tu_berlin"
    )
    cv_build_parser.add_argument(
        "language", choices=["german", "english", "spanish"], help="CV language"
    )
    cv_build_parser.add_argument(
        "--source", default="tu_berlin", help="Pipeline source namespace"
    )
    cv_build_parser.add_argument(
        "--via",
        choices=["latex", "docx"],
        default="latex",
        help="Engine used to produce final PDF",
    )
    cv_build_parser.add_argument(
        "--docx-template",
        choices=["classic", "modern", "harvard", "executive"],
        default="classic",
        help="DOCX renderer style (used when --via docx)",
    )
    cv_build_parser.add_argument(
        "--docx-template-path",
        default=None,
        help="Optional path to .docx file used as base template",
    )
    cv_build_parser.add_argument(
        "--with-ats",
        action="store_true",
        help="Also run ATS immediately after build",
    )

    cv_validate_parser = subparsers.add_parser(
        "cv-validate-ats", help="Run ATS validation on rendered CV"
    )
    cv_validate_parser.add_argument(
        "job_id", help="Job id under data/pipelined_data/tu_berlin"
    )
    cv_validate_parser.add_argument(
        "--source", default="tu_berlin", help="Pipeline source namespace"
    )
    cv_validate_parser.add_argument(
        "--file-stem", default="cv", help="Rendered file stem"
    )
    cv_validate_parser.add_argument(
        "--ats-target",
        choices=["docx", "pdf"],
        default="pdf",
        help="ATS target artifact",
    )
    cv_validate_parser.add_argument(
        "--via",
        choices=["latex", "docx"],
        default="docx",
        help="Rendering subdirectory to read artifacts from",
    )

    cv_pdf_parser = subparsers.add_parser(
        "cv-pdf", help="Build PDF and run ATS validation (engine selectable)"
    )
    cv_pdf_parser.add_argument(
        "job_id", help="Job id under data/pipelined_data/tu_berlin"
    )
    cv_pdf_parser.add_argument(
        "language", choices=["german", "english", "spanish"], help="CV language"
    )
    cv_pdf_parser.add_argument(
        "--source", default="tu_berlin", help="Pipeline source namespace"
    )
    cv_pdf_parser.add_argument(
        "--via",
        choices=["latex", "docx"],
        default="docx",
        help="Engine used to produce final PDF",
    )
    cv_pdf_parser.add_argument(
        "--docx-template",
        choices=["classic", "modern", "harvard", "executive"],
        default="classic",
        help="DOCX renderer style (used when --via docx)",
    )
    cv_pdf_parser.add_argument(
        "--docx-template-path",
        default=None,
        help="Optional path to .docx file used as base template",
    )
    cv_pdf_parser.add_argument("--file-stem", default="cv", help="Rendered file stem")

    cv_template_test_parser = subparsers.add_parser(
        "cv-template-test",
        help="Build CV and test deterministic template parity",
    )
    cv_template_test_parser.add_argument(
        "job_id", help="Job id under data/pipelined_data/tu_berlin"
    )
    cv_template_test_parser.add_argument(
        "language", choices=["german", "english", "spanish"], help="CV language"
    )
    cv_template_test_parser.add_argument(
        "--source", default="tu_berlin", help="Pipeline source namespace"
    )
    cv_template_test_parser.add_argument(
        "--via",
        choices=["latex", "docx"],
        default="docx",
        help="Engine used to produce final PDF",
    )
    cv_template_test_parser.add_argument(
        "--docx-template",
        choices=["classic", "modern", "harvard", "executive"],
        default="classic",
        help="DOCX renderer style (used when --via docx)",
    )
    cv_template_test_parser.add_argument(
        "--docx-template-path",
        default=None,
        help="Optional path to .docx file used as base template",
    )
    cv_template_test_parser.add_argument(
        "--file-stem", default="cv", help="Rendered file stem"
    )
    cv_template_test_parser.add_argument(
        "--target",
        choices=["docx", "pdf"],
        default="pdf",
        help="Artifact used for deterministic template score",
    )
    cv_template_test_parser.add_argument(
        "--require-perfect",
        action="store_true",
        help="Fail unless deterministic template score is exactly 100 percent",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "run":
        return handle_run(args)
    if args.command == "fetch":
        run_fetch(args.mode)
        return 0
    if args.command == "fetch-url":
        try:
            run_fetch_url(
                urls=args.urls,
                source=args.source,
                strict_english=args.strict_english,
            )
            return 0
        except Exception as exc:
            print(f"[error] fetch-url failed: {exc}")
            return 1
    if args.command == "apply-to":
        run_apply_to(args)
        return 0
    if args.command == "translate":
        run_translate(args.mode)
        return 0
    if args.command == "regenerate":
        run_regenerate()
        return 0
    if args.command == "backup":
        run_backup()
        return 0
    if args.command == "cv-tailor":
        output_path = build_cv_tailoring(args.job_id, source=args.source)
        print(f"[done] wrote {output_path}")
        return 0
    if args.command == "motivation-pre":
        try:
            run_motivation_pre(
                job_id=args.job_id,
                source=args.source,
                output_name=args.output_name,
            )
            return 0
        except Exception as exc:
            print(f"[error] motivation-pre failed: {exc}")
            return 1
    if args.command == "motivation-build":
        try:
            run_motivation_build(
                job_id=args.job_id,
                source=args.source,
                output_name=args.output_name,
                skip_pdf=args.skip_pdf,
                skip_email=args.skip_email,
            )
            return 0
        except Exception as exc:
            print(f"[error] motivation-build failed: {exc}")
            return 1
    if args.command == "app-prepare":
        try:
            return run_app_prepare(
                job_id=args.job_id,
                source=args.source,
                target=args.target,
                ats_mode=args.ats_mode,
            )
        except Exception as exc:
            print(f"[error] app-prepare failed: {exc}")
            return 1
    if args.command == "app-review":
        try:
            return run_app_review(
                job_id=args.job_id,
                source=args.source,
                target=args.target,
            )
        except Exception as exc:
            print(f"[error] app-review failed: {exc}")
            return 1
    if args.command == "app-status":
        try:
            return run_app_status(
                job_id=args.job_id,
                source=args.source,
                target=args.target,
            )
        except Exception as exc:
            print(f"[error] app-status failed: {exc}")
            return 1
    if args.command == "app-renderize":
        try:
            return run_app_renderize(
                job_id=args.job_id,
                source=args.source,
                target=args.target,
                ats_mode=args.ats_mode,
                language=args.language,
                via=args.via,
                docx_template=args.docx_template,
                docx_template_path=args.docx_template_path,
            )
        except Exception as exc:
            print(f"[error] app-renderize failed: {exc}")
            return 1
    if args.command == "app-run":
        try:
            return run_app_run(
                job_id=args.job_id,
                source=args.source,
                target=args.target,
                ats_mode=args.ats_mode,
                language=args.language,
                via=args.via,
                docx_template=args.docx_template,
                docx_template_path=args.docx_template_path,
            )
        except Exception as exc:
            print(f"[error] app-run failed: {exc}")
            return 1
    if args.command == "jobs-index":
        try:
            return run_jobs_index(source=args.source)
        except Exception as exc:
            print(f"[error] jobs-index failed: {exc}")
            return 1
    if args.command == "status":
        print_pipeline_status()
        return 0
    if args.command == "validate":
        _, _, missing_by_job, summary_exists = print_pipeline_status()
        return 0 if not missing_by_job and summary_exists else 1
    if args.command == "cv-render":
        run_cv_render(
            job_id=args.job_id,
            source=args.source,
            language=args.language,
            via=args.via,
            docx_template=args.docx_template,
            docx_template_path=args.docx_template_path,
            with_ats=args.with_ats,
        )
        return 0
    if args.command == "cv-build":
        run_cv_build(
            job_id=args.job_id,
            source=args.source,
            language=args.language,
            via=args.via,
            docx_template=args.docx_template,
            docx_template_path=args.docx_template_path,
            with_ats=args.with_ats,
        )
        return 0
    if args.command == "cv-validate-ats":
        run_cv_validate_ats(
            job_id=args.job_id,
            source=args.source,
            file_stem=args.file_stem,
            ats_target=args.ats_target,
            via=args.via,
        )
        return 0
    if args.command == "cv-pdf":
        run_cv_pdf_pipeline(
            job_id=args.job_id,
            source=args.source,
            language=args.language,
            file_stem=args.file_stem,
            via=args.via,
            docx_template=args.docx_template,
            docx_template_path=args.docx_template_path,
        )
        return 0
    if args.command == "cv-template-test":
        run_cv_template_test(
            job_id=args.job_id,
            source=args.source,
            language=args.language,
            via=args.via,
            docx_template=args.docx_template,
            docx_template_path=args.docx_template_path,
            file_stem=args.file_stem,
            target=args.target,
            require_perfect=args.require_perfect,
        )
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
