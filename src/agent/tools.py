"""Tool functions for the application agent.

Each function is a standalone operation the agent can invoke.
Tools are deterministic (scrape, render, score) or LLM-driven
(analyze fit, tailor CV, write motivation letter).
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from src.utils.config import CVConfig
from src.utils.loaders.profile_loader import load_base_profile
from src.utils.model import CVModel
from src.models.application import FitAnalysis
from src.models.job import JobPosting
from src.models.motivation import EmailDraftOutput, MotivationLetterOutput
from src.models.pipeline_contract import PipelineState
from src.prompts import load_prompt, load_prompt_with_context
from src.scraper.scrape_single_url import (
    parse_structured_from_markdown,
    run_for_url,
)

_gemini: Any = None


def _get_config(config: CVConfig | None) -> CVConfig:
    return config or CVConfig.from_defaults()


def _get_gemini() -> Any:
    global _gemini
    if _gemini is None:
        from src.utils.gemini import GeminiClient

        _gemini = GeminiClient()
    return _gemini


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model output")
    return text[start : end + 1]


def _error_jobposting(url: str, error: str) -> JobPosting:
    return JobPosting(
        title="",
        reference_number="",
        deadline="",
        institution="",
        department="",
        location="",
        contact_name="",
        contact_email="",
        requirements=[],
        themes=[],
        responsibilities=[],
        raw_text=f"scrape_error: {error}; url={url}",
    )


def _error_fit_analysis(error: str) -> FitAnalysis:
    return FitAnalysis(
        overall_score=0,
        eligibility="risk",
        alignment_summary=f"analyze_fit_error: {error}",
        top_matches=[],
        gaps=["analysis_failed"],
        recommendation="skip",
    )


def scrape_job(url: str, config: CVConfig | None = None) -> JobPosting:
    """Scrape a job posting URL and return structured job data.

    Downloads HTML, extracts markdown, parses to structured fields,
    writes raw artifacts to pipeline data directory.
    """
    cfg = _get_config(config)
    try:
        result = run_for_url(
            url=url,
            source="tu_berlin",
            pipeline_root=cfg.pipeline_root,
        )
        extracted_json_path = Path(result["extracted_json"])
        summary = json.loads(extracted_json_path.read_text(encoding="utf-8"))

        source_markdown = Path(result["source_text_md"]).read_text(encoding="utf-8")
        reparsed = parse_structured_from_markdown(
            source_markdown,
            url=url,
            job_id=str(summary.get("job_id", "")),
        )
        posting = JobPosting.from_summary_json(reparsed)
        posting.raw_text = source_markdown
        return posting
    except Exception as exc:
        return _error_jobposting(url=url, error=str(exc))


def scrape_jobs_batch(
    urls: list[str], config: CVConfig | None = None
) -> list[JobPosting]:
    """Scrape multiple job URLs in sequence. Returns list of parsed jobs."""
    cfg = _get_config(config)
    return [scrape_job(url, config=cfg) for url in urls]


def analyze_fit(job: JobPosting, profile_path: Path | None = None) -> FitAnalysis:
    """Analyze how well a candidate profile fits a job posting.

    Uses the ATS evaluation prompt with Gemini to score alignment.
    Returns structured fit analysis with score, matches, gaps.
    """
    cfg = CVConfig.from_defaults()
    try:
        profile_data = load_base_profile(profile_path or cfg.profile_path())
        model = CVModel.from_profile(profile_data)

        context = {
            "job": job.model_dump(),
            "candidate": {
                "name": model.full_name,
                "summary": model.summary,
                "skills": model.skills,
                "experience": [vars(item) for item in model.experience],
                "education": [vars(item) for item in model.education],
                "publications": [vars(item) for item in model.publications],
                "languages": [vars(item) for item in model.languages],
            },
        }

        prompt = load_prompt("ats_evaluation")
        schema = {
            "overall_score": 0,
            "eligibility": "pass|risk|fail",
            "alignment_summary": "string",
            "top_matches": [
                {
                    "requirement": "string",
                    "evidence": "string",
                    "coverage": "full|partial",
                }
            ],
            "gaps": ["string"],
            "recommendation": "strong_apply|apply|weak_apply|skip",
        }
        full_prompt = (
            f"{prompt}\n\n"
            "Return JSON only that matches this schema exactly:\n"
            f"{json.dumps(schema, indent=2, ensure_ascii=True)}\n\n"
            "Context JSON:\n"
            f"{json.dumps(context, indent=2, ensure_ascii=True)}"
        )
        response = _get_gemini().generate(full_prompt)
        return FitAnalysis.model_validate_json(_extract_json_object(response))
    except Exception as exc:
        return _error_fit_analysis(str(exc))


def rank_jobs(
    jobs: list[JobPosting], profile_path: Path | None = None
) -> list[tuple[JobPosting, FitAnalysis]]:
    """Rank multiple jobs by fit score. Returns sorted (job, fit) pairs."""
    ranked = [(job, analyze_fit(job, profile_path=profile_path)) for job in jobs]
    return sorted(ranked, key=lambda item: item[1].overall_score, reverse=True)


def tailor_cv(
    job: JobPosting,
    pipeline_state: PipelineState,
    config: CVConfig | None = None,
) -> PipelineState:
    """Run the multi-agent CV tailoring pipeline (MATCHER -> SELLER -> CHECKER).

    Takes a job and initial pipeline state (with evidence), returns
    the final state with approved claims.
    """
    cfg = _get_config(config)
    try:
        from src.utils.pipeline import CVMultiAgentPipeline

        with TemporaryDirectory(prefix="cv_tailor_") as temp_dir:
            temp_root = Path(temp_dir)
            profile_path = temp_root / "profile.json"
            profile_path.write_text(
                json.dumps(load_base_profile(cfg.profile_path()), indent=2) + "\n",
                encoding="utf-8",
            )

            job_path = temp_root / "job.md"
            job_payload = job.model_dump()
            job_path.write_text(
                json.dumps(job_payload, indent=2, ensure_ascii=True) + "\n",
                encoding="utf-8",
            )

            output_dir = temp_root / "out"
            output_dir.mkdir(parents=True, exist_ok=True)

            runner = CVMultiAgentPipeline(env_path=str(cfg.project_root / ".env"))
            output = runner.execute_pipeline(
                profile_path=str(profile_path),
                job_description_path=str(job_path),
                prompts_path=str(
                    cfg.project_root / "src" / "prompts" / "cv_multi_agent.txt"
                ),
                output_dir=str(output_dir),
            )
            return PipelineState.model_validate(output)
    except Exception:
        return pipeline_state


def render_cv(
    job_id: str,
    source: str = "tu_berlin",
    template: str = "modern",
    via: str = "docx",
    config: CVConfig | None = None,
) -> Path:
    """Render a CV to DOCX or LaTeX and convert to PDF.

    Returns path to the generated PDF.
    """
    cfg = _get_config(config)
    output_path = cfg.cv_render_dir(source=source, job_id=job_id, via=via) / "cv.pdf"
    try:
        from src.utils import cv_rendering as cv_main

        cv_main.build_cv(
            config=cfg,
            source=source,
            job_id=job_id,
            language="english",
            via=via,
            docx_template=template,
            docx_template_path=None,
            run_ats=False,
            job_description_path=None,
            ats_mode="fallback",
            ats_prompt=None,
        )
    except Exception:
        return output_path
    return output_path


def score_ats(
    job_id: str,
    source: str = "tu_berlin",
    ats_target: str = "pdf",
    config: CVConfig | None = None,
) -> dict:
    """Run ATS validation on a rendered CV.

    Returns the ATS report dict with code_score, llm_score, combined, parity.
    """
    cfg = _get_config(config)
    try:
        from src.utils import cv_rendering as cv_main
        from src.utils.ats import run_ats_analysis
        from src.render.pdf import extract_docx_text, extract_pdf_text

        paths = cv_main.resolve_output_paths(
            config=cfg,
            source=source,
            job_id=job_id,
            file_stem="cv",
            via="docx",
        )

        if ats_target == "pdf":
            cv_text = extract_pdf_text(paths["pdf"])
        else:
            cv_text = extract_docx_text(paths["docx"])

        job_description = cv_main.load_job_description(
            config=cfg,
            source=source,
            job_id=job_id,
            path_override=None,
        )
        report = run_ats_analysis(cv_text=cv_text, job_description=job_description)
        report["ats_target"] = ats_target
        return report
    except Exception as exc:
        return {
            "success": False,
            "ats_target": ats_target,
            "score": 0,
            "error": str(exc),
        }


def write_motivation_letter(
    job_id: str,
    source: str = "tu_berlin",
    config: CVConfig | None = None,
) -> MotivationLetterOutput:
    """Generate the final motivation letter using the motivation agent.

    Returns structured letter output with subject, salutation, body.
    """
    cfg = _get_config(config)
    try:
        from src.steps.motivation_service import MotivationLetterService

        service = MotivationLetterService(config=cfg)
        context = service.build_context(job_id=job_id, source=source)
        context_json = json.dumps(context, indent=2, ensure_ascii=True)
        prompt = load_prompt_with_context("motivation_letter", context_json)
        response = _get_gemini().generate(prompt)
        return MotivationLetterOutput.model_validate_json(
            _extract_json_object(response)
        )
    except Exception as exc:
        return MotivationLetterOutput(
            subject="",
            salutation="Dear Hiring Committee,",
            fit_signals=[],
            risk_notes=[f"write_motivation_letter_error: {exc}"],
            letter_markdown="",
        )


def build_motivation_pdf(
    job_id: str,
    source: str = "tu_berlin",
    config: CVConfig | None = None,
) -> Path:
    """Render a motivation letter markdown to PDF via LaTeX.

    Returns path to the generated PDF.
    """
    cfg = _get_config(config)
    output_path = (
        cfg.pipeline_root / source / job_id / "output" / "motivation_letter.pdf"
    )
    try:
        from src.steps.motivation_service import MotivationLetterService

        result = MotivationLetterService(config=cfg).build_pdf_for_job(
            job_id=job_id,
            source=source,
        )
        return result.pdf_path
    except Exception:
        return output_path


def generate_email_draft(
    job_id: str,
    source: str = "tu_berlin",
    config: CVConfig | None = None,
) -> EmailDraftOutput:
    """Generate an application email draft using the email agent.

    Returns structured email with subject, body, signature.
    """
    cfg = _get_config(config)
    try:
        from src.steps.motivation_service import MotivationLetterService

        service = MotivationLetterService(config=cfg)
        context = service.build_context(job_id=job_id, source=source)
        context_json = json.dumps(context, indent=2, ensure_ascii=True)
        prompt = load_prompt_with_context("email_draft", context_json)
        response = _get_gemini().generate(prompt)
        return EmailDraftOutput.model_validate_json(_extract_json_object(response))
    except Exception:
        candidate = {"name": "", "contact": {"email": "", "phone": ""}}
        try:
            from src.steps.motivation_service import MotivationLetterService

            service = MotivationLetterService(config=cfg)
            context = service.build_context(job_id=job_id, source=source)
            candidate = context.get("candidate", candidate)
        except Exception:
            pass
        return EmailDraftOutput(
            to="",
            subject="",
            salutation="Dear Hiring Committee,",
            body="",
            closing="Best regards,",
            sender_name=str(candidate.get("name", "")),
            sender_email=str(candidate.get("contact", {}).get("email", "")),
            sender_phone=str(candidate.get("contact", {}).get("phone", "")),
        )


def merge_pdfs(output_path: Path, *pdf_paths: Path) -> Path:
    """Merge multiple PDFs into one. Returns output path."""
    try:
        from src.utils import pdf_merger as legacy_pdf_merger

        pdf_list = [str(path) for path in pdf_paths]
        temp_merged = legacy_pdf_merger.merge_pdfs(pdf_list, str(output_path))
        legacy_pdf_merger.compress_pdf(
            temp_merged, str(output_path), resolution="ebook"
        )
    except Exception:
        return output_path
    return output_path
