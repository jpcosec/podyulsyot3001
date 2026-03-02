#!/usr/bin/env python3
"""CV build CLI with canonical profile and pipelined outputs."""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from shutil import copy2, copytree
from shutil import which

# Add project root to sys.path to allow imports
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from dotenv import load_dotenv

from src.ats_tester import DeterministicContentEvaluator
from src.cv_generator.ats import run_ats_analysis, write_ats_report
from src.utils.config import CVConfig
from src.utils.loaders.profile_loader import load_base_profile
from src.utils.model import CVModel
from src.render.docx import DocumentRenderer
from src.render.latex import render_to_file
from src.render.pdf import extract_docx_text, extract_pdf_text


def resolve_output_paths(
    config: CVConfig, source: str, job_id: str, file_stem: str, via: str = "docx"
) -> dict[str, Path]:
    render_dir = config.cv_render_dir(source=source, job_id=job_id, via=via)
    cv_root = render_dir.parent.parent  # rendered/<via>/../.. = cv/
    return {
        "cv_root": cv_root,
        "render_dir": render_dir,
        "docx": render_dir / f"{file_stem}.docx",
        "tex": render_dir / f"{file_stem}.tex",
        "pdf": render_dir / f"{file_stem}.pdf",
        "ats": cv_root / "ats" / "report.json",
    }


def resolve_job_description_path(
    config: CVConfig, source: str, job_id: str, path_override: str | None
) -> Path | None:
    if path_override:
        path = Path(path_override)
        return path if path.exists() else None
    candidate = config.pipeline_root / source / job_id / "job.md"
    return candidate if candidate.exists() else None


def load_job_description(
    config: CVConfig, source: str, job_id: str, path_override: str | None
) -> str:
    path = resolve_job_description_path(config, source, job_id, path_override)
    if not path:
        return ""
    return path.read_text(encoding="utf-8")


def load_canonical_context(config: CVConfig) -> CVModel:
    profile = load_base_profile(config.profile_path())
    return CVModel.from_profile(profile)


def _non_empty_lines(lines: list[str]) -> list[str]:
    return [line.strip() for line in lines if line and line.strip()]


def build_to_render_markdown(model: CVModel) -> str:
    lines: list[str] = []

    lines.append(f"# {model.full_name}")
    if model.tagline:
        lines.append(model.tagline)

    # Contact section mirrors PDF extraction format (Phone:/Email:/Address: labels)
    lines.append("## CONTACT")
    if model.contact.phone:
        lines.append(f"Phone: {model.contact.phone}")
    if model.contact.email:
        lines.append(f"Email: {model.contact.email}")
    if model.contact.address:
        lines.append(f"Address: {model.contact.address}")

    if model.summary:
        lines.extend(["## SUMMARY", model.summary])

    # Section order matches template: Education before Work Experience
    lines.append("## EDUCATION")
    for edu in model.education:
        label = (
            f"{edu.degree} ({edu.specialization})" if edu.specialization else edu.degree
        )
        lines.append(f"{edu.start_date} - {edu.end_date}")
        lines.append(f"{label} - {edu.institution}, {edu.location}".strip())
        if edu.equivalency_note:
            lines.append(edu.equivalency_note)

    # Section name mirrors template: "Work Experience"
    lines.append("## WORK EXPERIENCE")
    for exp in model.experience:
        end_date = exp.end_date or "Present"
        location = f" - {exp.location}" if exp.location else ""
        # Format matches moderncv \cventry extraction: date first, then role, org, location
        lines.append(
            f"### {exp.start_date} - {exp.role} - {exp.organization}{location}"
        )
        lines.append(end_date)
        lines.extend(f"- {item}" for item in exp.achievements if item)

    if model.publications:
        lines.append("## PUBLICATIONS")
        for pub in sorted(model.publications, key=lambda item: item.year, reverse=True):
            line = f"{pub.year} - {pub.title}"
            if pub.venue:
                line = f"{line} {pub.venue}"
            lines.append(line)

    if model.languages:
        lines.append("## LANGUAGES")
        for lang in model.languages:
            line = f"* {lang.name}: {lang.level}"
            if lang.note:
                line = f"{line} ({lang.note})"
            lines.append(line)

    # Section name mirrors template: "Technical Skills"
    if model.skills:
        lines.append("## TECHNICAL SKILLS")
        for category, items in model.skills.items():
            label = category.replace("_", " ").title()
            lines.append(f"* {label}")
            lines.append(", ".join(items))

    return "\n".join(_non_empty_lines(lines)) + "\n"


def write_to_render_markdown(
    config: CVConfig,
    source: str,
    job_id: str,
    model: CVModel,
) -> Path:
    to_render_path = config.pipeline_root / source / job_id / "cv" / "to_render.md"
    to_render_path.parent.mkdir(parents=True, exist_ok=True)
    to_render_path.write_text(build_to_render_markdown(model), encoding="utf-8")
    return to_render_path


def show_status(config: CVConfig, source: str, job_id: str) -> None:
    model = load_canonical_context(config)
    paths = resolve_output_paths(config, source, job_id, "cv")

    print("\n" + "=" * 70)
    print("CV COMPILATION STATUS")
    print("=" * 70)
    print(f"\nProfile source: {config.profile_path()}")
    print(f"Render output: {paths['render_dir']}")

    print("\nPERSONAL INFORMATION:")
    print(f"  Name: {model.full_name}")
    print(f"  Tagline: {model.tagline}")
    print(f"  Email: {model.contact.email}")
    print(f"  Phone: {model.contact.phone}")

    print("\nCV CONTENT:")
    print(f"  Education entries: {len(model.education)}")
    print(f"  Work experiences: {len(model.experience)}")
    print(f"  Publications: {len(model.publications)}")
    print(f"  Language skills: {len(model.languages)}")

    templates_dir = Path(__file__).resolve().parents[2] / "src" / "render" / "templates"
    print("\nAVAILABLE TEMPLATES:")
    for template_file in [
        "german.tex.jinja2",
        "english.tex.jinja2",
        "spanish.tex.jinja2",
    ]:
        template_path = templates_dir / template_file
        status = "OK" if template_path.exists() else "MISSING"
        print(f"  {status:8} {template_file}")

    print("=" * 70 + "\n")


def render_docx(
    model: CVModel,
    output_path: Path,
    template_name: str,
    template_path: Path | None,
) -> None:
    assets_dir = project_root / "data" / "reference_data" / "application_assets"
    photo_path = assets_dir / "Photoportrait_circular.png"
    renderer = DocumentRenderer(
        photo_path=str(photo_path) if photo_path.exists() else None,
        template_name=template_name,
        template_path=template_path,
    )
    contact_parts = [model.contact.phone, model.contact.email]
    contact_info = " | ".join(p for p in contact_parts if p)
    renderer.render_header(
        name=model.full_name,
        titles=model.tagline,
        contact_info=contact_info,
    )
    if model.summary:
        renderer.render_summary(model.summary)
    renderer.render_experience([vars(e) for e in model.experience])
    renderer.render_education([vars(e) for e in model.education])
    renderer.render_publications([vars(p) for p in model.publications])
    renderer.render_languages([vars(l) for l in model.languages])
    renderer.render_skills({k: v for k, v in model.skills.items()})
    renderer.save(output_path)


def prepare_latex_assets(render_dir: Path) -> None:
    legacy_root = Path(__file__).resolve().parents[2] / "src" / "render" / "assets"
    # Einstellungen: always sync — these are framework config files that may change
    settings_src = legacy_root / "Einstellungen"
    if settings_src.exists():
        copytree(settings_src, render_dir / "Einstellungen", dirs_exist_ok=True)
    # Abbildungen: only create once — photo is overwritten separately below
    abbildungen_src = legacy_root / "Abbildungen"
    abbildungen_dst = render_dir / "Abbildungen"
    if abbildungen_src.exists() and not abbildungen_dst.exists():
        copytree(abbildungen_src, abbildungen_dst)
    compile_sh = legacy_root / "compile.sh"
    if compile_sh.exists():
        copy2(compile_sh, render_dir / "compile.sh")
    # Always overwrite profile photo with the actual one when available
    actual_photo = (
        project_root
        / "data"
        / "reference_data"
        / "application_assets"
        / "Photoportrait_circular.png"
    )
    abbildungen = render_dir / "Abbildungen"
    if actual_photo.exists() and abbildungen.exists():
        subprocess.run(
            ["convert", str(actual_photo), str(abbildungen / "profile.jpg")],
            capture_output=True,
            check=True,
        )


def _extract_city(address: str) -> str:
    """Best-effort city extraction from a full address string."""
    parts = [p.strip() for p in address.split(",") if p.strip()]
    # Typically "Street, PostalCode City, Country" → second-to-last part, strip postal code prefix
    if len(parts) >= 2:
        candidate = parts[-2]
        # Drop leading postal code digits if present (e.g. "12459 Berlin")
        tokens = candidate.split()
        if tokens and tokens[0].isdigit():
            return " ".join(tokens[1:])
        return candidate
    return ""


def _model_to_latex_context(model: CVModel) -> dict:
    return {
        "personal": {
            "full_name": model.full_name,
            "first_name": model.full_name.split()[0],
            "last_name": " ".join(model.full_name.split()[1:]),
            "tagline": model.tagline,
            "email": model.contact.email,
            "phone": model.contact.phone,
            "address": model.contact.address,
            "city": _extract_city(model.contact.address),
        },
        "summary": model.summary,
        "education": [vars(e) for e in model.education],
        "experience": [vars(e) for e in model.experience],
        "publications": [vars(p) for p in model.publications],
        "skills": model.skills,
        "languages": [vars(l) for l in model.languages],
    }


def render_latex(model: CVModel, language: str, output_path: Path) -> None:
    template_name = f"{language}.tex.jinja2"
    template_dir = Path(__file__).resolve().parents[2] / "src" / "render" / "templates"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prepare_latex_assets(output_path.parent)
    render_to_file(
        template_name=template_name,
        template_dir=template_dir,
        context=_model_to_latex_context(model),
        output_path=output_path,
    )


def build_latex_pdf(tex_path: Path) -> None:
    result = subprocess.run(
        ["pdflatex", "-interaction=nonstopmode", "-shell-escape", tex_path.name],
        cwd=tex_path.parent,
        capture_output=True,
        text=True,
    )
    pdf_path = tex_path.with_suffix(".pdf")
    if result.returncode != 0 and not pdf_path.exists():
        log_tail = result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout
        raise RuntimeError(f"pdflatex failed for {tex_path}:\n{log_tail}")


def convert_docx_to_pdf(docx_path: Path, pdf_path: Path) -> None:
    soffice = which("soffice")
    if not soffice:
        raise RuntimeError(
            "DOCX to PDF conversion requires LibreOffice ('soffice') in PATH"
        )

    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [
            soffice,
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            str(pdf_path.parent),
            str(docx_path),
        ],
        capture_output=True,
        text=True,
    )
    generated_pdf = docx_path.with_suffix(".pdf")
    if result.returncode != 0 or not generated_pdf.exists():
        message = (result.stderr or result.stdout or "unknown conversion error").strip()
        raise RuntimeError(f"DOCX to PDF conversion failed: {message}")
    if generated_pdf != pdf_path:
        generated_pdf.replace(pdf_path)


def run_ats_for_rendered_output(
    config: CVConfig,
    source: str,
    job_id: str,
    paths: dict[str, Path],
    job_description_path: str | None,
    ats_mode: str,
    ats_prompt: str | None,
    ats_target: str = "docx",
) -> Path:
    jd = load_job_description(config, source, job_id, job_description_path)
    if ats_target == "pdf":
        if not paths["pdf"].exists():
            raise FileNotFoundError(f"PDF not found for ATS validation: {paths['pdf']}")
        text = extract_pdf_text(paths["pdf"])
    else:
        if not paths["docx"].exists():
            raise FileNotFoundError(
                f"DOCX not found for ATS validation: {paths['docx']}"
            )
        text = extract_docx_text(paths["docx"])
    prompt_path = Path(ats_prompt) if ats_prompt else None
    analysis = run_ats_analysis(
        cv_text=text,
        job_description=jd,
        prompt_path=prompt_path,
        ats_mode=ats_mode,
    )
    analysis["ats_target"] = ats_target
    write_ats_report(paths["ats"], analysis)
    return paths["ats"]


def _load_to_render_text(config: CVConfig, source: str, job_id: str) -> str:
    candidate = config.pipeline_root / source / job_id / "cv" / "to_render.md"
    if not candidate.exists():
        return ""
    return candidate.read_text(encoding="utf-8")


def _validate_render_parity(
    config: CVConfig,
    source: str,
    job_id: str,
    paths: dict[str, Path],
) -> dict[str, object]:
    to_render = _load_to_render_text(config, source, job_id)
    if not to_render.strip():
        return {
            "available": False,
            "reason": "to_render.md not found or empty",
        }

    evaluator = DeterministicContentEvaluator(lang="en")
    checks: dict[str, object] = {"available": True}

    if paths["docx"].exists():
        checks["docx"] = evaluator.compare_texts(
            to_render, extract_docx_text(paths["docx"])
        )
    else:
        checks["docx"] = {"available": False, "reason": "docx not found"}

    if paths["pdf"].exists():
        checks["pdf"] = evaluator.compare_texts(
            to_render, extract_pdf_text(paths["pdf"])
        )
    else:
        checks["pdf"] = {"available": False, "reason": "pdf not found"}

    if not paths["docx"].exists() and not paths["pdf"].exists():
        checks["available"] = False
        checks["reason"] = "no rendered artifacts found for parity check"

    return checks


def render_cv(
    config: CVConfig,
    source: str,
    job_id: str,
    language: str,
    via: str,
    docx_template: str,
    docx_template_path: str | None,
    run_ats: bool,
    job_description_path: str | None,
    ats_mode: str,
    ats_prompt: str | None,
) -> None:
    model = load_canonical_context(config)
    paths = resolve_output_paths(config, source, job_id, "cv", via)
    resolved_docx_template_path = (
        Path(docx_template_path) if docx_template_path else None
    )
    to_render_path = write_to_render_markdown(config, source, job_id, model)
    print(f"Generated: {to_render_path}")

    if via == "docx":
        render_docx(
            model,
            paths["docx"],
            template_name=docx_template,
            template_path=resolved_docx_template_path,
        )
        print(f"Generated: {paths['docx']}")
        convert_docx_to_pdf(paths["docx"], paths["pdf"])
        print(f"Generated: {paths['pdf']}")
        if run_ats:
            report_path = run_ats_for_rendered_output(
                config,
                source,
                job_id,
                paths,
                job_description_path,
                ats_mode,
                ats_prompt,
                ats_target="pdf",
            )
            print(f"ATS report: {report_path}")
        return

    render_latex(model, language, paths["tex"])
    print(f"Generated: {paths['tex']}")
    build_latex_pdf(paths["tex"])
    print(f"Generated: {paths['pdf']}")


def build_cv(
    config: CVConfig,
    source: str,
    job_id: str,
    language: str,
    via: str,
    docx_template: str,
    docx_template_path: str | None,
    run_ats: bool,
    job_description_path: str | None,
    ats_mode: str,
    ats_prompt: str | None,
) -> None:
    render_cv(
        config,
        source,
        job_id,
        language,
        via,
        docx_template,
        docx_template_path,
        run_ats,
        job_description_path,
        ats_mode,
        ats_prompt,
    )


def validate_ats(
    config: CVConfig,
    source: str,
    job_id: str,
    file_stem: str,
    job_description_path: str | None,
    ats_mode: str,
    ats_prompt: str | None,
    ats_target: str,
    via: str = "docx",
) -> None:
    paths = resolve_output_paths(config, source, job_id, file_stem, via)
    report_path = run_ats_for_rendered_output(
        config,
        source,
        job_id,
        paths,
        job_description_path,
        ats_mode,
        ats_prompt,
        ats_target=ats_target,
    )

    analysis = json.loads(report_path.read_text(encoding="utf-8"))
    analysis["content_parity"] = _validate_render_parity(
        config=config,
        source=source,
        job_id=job_id,
        paths=paths,
    )
    write_ats_report(report_path, analysis)

    print(f"ATS report: {report_path}")


def _template_score(parity_entry: dict[str, object]) -> float:
    def _as_float(value: object) -> float:
        if isinstance(value, (int, float)):
            return float(value)
        if isinstance(value, str):
            try:
                return float(value)
            except ValueError:
                return 0.0
        return 0.0

    overlap = _as_float(parity_entry.get("line_overlap_pct", 0.0))
    order = _as_float(parity_entry.get("order_match_pct", 0.0))
    return min(overlap, order)


def test_template(
    config: CVConfig,
    source: str,
    job_id: str,
    language: str,
    via: str,
    docx_template: str,
    docx_template_path: str | None,
    file_stem: str,
    target: str,
    require_perfect: bool,
) -> None:
    build_cv(
        config=config,
        source=source,
        job_id=job_id,
        language=language,
        via=via,
        docx_template=docx_template,
        docx_template_path=docx_template_path,
        run_ats=False,
        job_description_path=None,
        ats_mode="fallback",
        ats_prompt=None,
    )

    paths = resolve_output_paths(config, source, job_id, file_stem, via)
    parity = _validate_render_parity(
        config=config, source=source, job_id=job_id, paths=paths
    )

    if not parity.get("available"):
        raise RuntimeError(
            f"Template test unavailable: {parity.get('reason', 'unknown reason')}"
        )

    target_result = parity.get(target)
    if not isinstance(target_result, dict):
        raise RuntimeError(f"Template test missing target result: {target}")
    if not target_result.get("available", True):
        raise RuntimeError(
            f"Template test target unavailable ({target}): {target_result.get('reason', 'unknown reason')}"
        )

    score = _template_score(target_result)
    report = {
        "source": source,
        "job_id": job_id,
        "language": language,
        "via": via,
        "docx_template": docx_template,
        "docx_template_path": docx_template_path,
        "target": target,
        "template_score_pct": score,
        "is_perfect": score == 100.0,
        "parity": parity,
    }

    template_report = paths["ats"].parent / "template_test.json"
    template_report.parent.mkdir(parents=True, exist_ok=True)
    template_report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(f"Template score ({target}): {score:.2f}%")
    print(f"Template test report: {template_report}")

    if require_perfect and score < 100.0:
        raise RuntimeError(
            f"Template test failed: expected 100.0%, got {score:.2f}% on target '{target}'"
        )


def main() -> None:
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    config = CVConfig.from_defaults()

    parser = argparse.ArgumentParser(
        description="Compile CV from canonical profile data"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument(
        "--job-id", default="manual", help="Target job id for pipelined output"
    )
    shared.add_argument(
        "--source", default="tu_berlin", help="Pipeline source namespace"
    )
    shared.add_argument(
        "--via",
        choices=["latex", "docx"],
        default="latex",
        help="Rendering engine used to produce final PDF",
    )
    shared.add_argument(
        "--docx-template",
        choices=["classic", "modern", "harvard", "executive"],
        default="classic",
        help="DOCX template variant (used only with --via docx)",
    )
    shared.add_argument(
        "--docx-template-path",
        default=None,
        help="Optional path to a .docx file used as base template when --via docx",
    )
    shared.add_argument(
        "--job-description", default=None, help="Path to job description markdown/text"
    )
    shared.add_argument(
        "--with-ats",
        action="store_true",
        help="Also run ATS during render/build (otherwise use validate-ats step)",
    )
    shared.add_argument(
        "--ats-mode",
        choices=["fallback", "strict"],
        default="fallback",
        help="ATS engine requirement mode",
    )
    shared.add_argument(
        "--ats-prompt", default=None, help="Optional path to ATS LLM prompt file"
    )

    subparsers.add_parser(
        "status", parents=[shared], help="Show CV source and render status"
    )

    render_parser = subparsers.add_parser("render", parents=[shared], help="Render CV")
    render_parser.add_argument(
        "language", choices=["german", "english", "spanish"], help="CV language"
    )

    build_parser = subparsers.add_parser(
        "build", parents=[shared], help="Render and compile CV"
    )
    build_parser.add_argument(
        "language", choices=["german", "english", "spanish"], help="CV language"
    )

    validate_parser = subparsers.add_parser(
        "validate-ats", help="Generate ATS report from existing rendered artifact"
    )
    validate_parser.add_argument(
        "--job-id", default="manual", help="Target job id for pipelined output"
    )
    validate_parser.add_argument(
        "--source", default="tu_berlin", help="Pipeline source namespace"
    )
    validate_parser.add_argument(
        "--job-description", default=None, help="Path to job description markdown/text"
    )
    validate_parser.add_argument(
        "--ats-mode",
        choices=["fallback", "strict"],
        default="fallback",
        help="ATS engine requirement mode",
    )
    validate_parser.add_argument(
        "--ats-prompt", default=None, help="Optional path to ATS LLM prompt file"
    )
    validate_parser.add_argument(
        "--file-stem",
        default="cv",
        help="Rendered file base name under rendered directory",
    )
    validate_parser.add_argument(
        "--ats-target",
        choices=["docx", "pdf"],
        default="pdf",
        help="Rendered artifact to evaluate for ATS",
    )
    validate_parser.add_argument(
        "--via",
        choices=["latex", "docx"],
        default="docx",
        help="Rendering subdirectory to read artifacts from",
    )

    template_test_parser = subparsers.add_parser(
        "test-template",
        help="Build CV and test deterministic parity against rendered output",
    )
    template_test_parser.add_argument(
        "language", choices=["german", "english", "spanish"], help="CV language"
    )
    template_test_parser.add_argument(
        "--job-id", default="manual", help="Target job id for pipelined output"
    )
    template_test_parser.add_argument(
        "--source", default="tu_berlin", help="Pipeline source namespace"
    )
    template_test_parser.add_argument(
        "--via",
        choices=["latex", "docx"],
        default="docx",
        help="Rendering engine used to produce final PDF",
    )
    template_test_parser.add_argument(
        "--docx-template",
        choices=["classic", "modern", "harvard", "executive"],
        default="classic",
        help="DOCX template variant (used only with --via docx)",
    )
    template_test_parser.add_argument(
        "--docx-template-path",
        default=None,
        help="Optional path to a .docx file used as base template when --via docx",
    )
    template_test_parser.add_argument(
        "--file-stem",
        default="cv",
        help="Rendered file base name under rendered directory",
    )
    template_test_parser.add_argument(
        "--target",
        choices=["docx", "pdf"],
        default="pdf",
        help="Rendered artifact target used for template score",
    )
    template_test_parser.add_argument(
        "--require-perfect",
        action="store_true",
        help="Fail command unless template score is exactly 100 percent",
    )

    args = parser.parse_args()

    if args.command == "status" or not args.command:
        show_status(config, source=args.source, job_id=args.job_id)
    elif args.command == "render":
        render_cv(
            config,
            source=args.source,
            job_id=args.job_id,
            language=args.language,
            via=args.via,
            docx_template=args.docx_template,
            docx_template_path=args.docx_template_path,
            run_ats=args.with_ats,
            job_description_path=args.job_description,
            ats_mode=args.ats_mode,
            ats_prompt=args.ats_prompt,
        )
    elif args.command == "build":
        build_cv(
            config,
            source=args.source,
            job_id=args.job_id,
            language=args.language,
            via=args.via,
            docx_template=args.docx_template,
            docx_template_path=args.docx_template_path,
            run_ats=args.with_ats,
            job_description_path=args.job_description,
            ats_mode=args.ats_mode,
            ats_prompt=args.ats_prompt,
        )
    elif args.command == "validate-ats":
        validate_ats(
            config,
            source=args.source,
            job_id=args.job_id,
            file_stem=args.file_stem,
            job_description_path=args.job_description,
            ats_mode=args.ats_mode,
            ats_prompt=args.ats_prompt,
            ats_target=args.ats_target,
            via=args.via,
        )
    elif args.command == "test-template":
        test_template(
            config=config,
            source=args.source,
            job_id=args.job_id,
            language=args.language,
            via=args.via,
            docx_template=args.docx_template,
            docx_template_path=args.docx_template_path,
            file_stem=args.file_stem,
            target=args.target,
            require_perfect=args.require_perfect,
        )
    else:
        parser.print_help()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"Error: {exc}")
        sys.exit(1)
