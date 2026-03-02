import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from src.ats_tester import DeterministicContentEvaluator
from src.prompts import load_prompt


def load_ats_prompt() -> str:
    return load_prompt("ats_evaluation")


def _extract_json_object(text: str) -> str:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in model response")
    return text[start : end + 1]


def run_code_engine(cv_text: str, job_description: str = "") -> dict[str, Any]:
    try:
        evaluator = DeterministicContentEvaluator(lang="en")
        result = evaluator.analyze_cv(cv_text, job_description)
        return {
            "available": True,
            "engine": "deterministic_content_evaluator",
            "score": result["score"],
            "used_fallback": False,
            "raw": result,
        }
    except Exception as exc:
        fallback = fallback_ats_analysis(cv_text, job_description)
        return {
            "available": True,
            "engine": "fallback_code",
            "score": int(fallback.get("score", 0)),
            "used_fallback": True,
            "reason": str(exc),
            "raw": fallback,
        }


def run_llm_engine(
    cv_text: str, job_description: str, prompt_text: str
) -> dict[str, Any]:
    try:
        from src.utils.gemini import GeminiClient

        client = GeminiClient()
    except (ImportError, ValueError) as exc:
        return {"available": False, "engine": "gemini", "reason": str(exc)}

    try:
        schema = (
            "Return JSON only with this schema: "
            '{"eligibility":{"status":"Pass|Risk|Fail","justification":""},'
            '"scores":{"alignment":0,"methodological_depth":0,"publications":0,'
            '"infrastructure_fair":0,"communication":0,"final":0},'
            '"risk_level":"Low|Moderate|High","highlights":[""],"gaps":[""],'
            '"recommendations":[""],"reasoning_summary":""}'
        )
        content = (
            f"{prompt_text}\n\n{schema}\n"
            f"\nAcademic Job Description:\n{job_description}\n"
            f"\nCandidate CV:\n{cv_text}\n"
        )
        response_text = client.generate(content)
        parsed = json.loads(_extract_json_object(response_text))
        score = int(parsed.get("scores", {}).get("final", 0))
        return {
            "available": True,
            "engine": client.model_name,
            "score": max(0, min(100, score)),
            "raw": parsed,
        }
    except Exception as exc:
        return {"available": False, "engine": "gemini", "reason": str(exc)}


def run_ats_analysis(
    cv_text: str,
    job_description: str = "",
    prompt_path: Path | None = None,
    ats_mode: str = "fallback",
    weights: tuple[float, float] = (0.6, 0.4),
) -> dict[str, Any]:
    prompt_file = prompt_path or Path("src/prompts/ats_evaluation.txt")
    prompt_text = load_ats_prompt()

    code_engine = run_code_engine(cv_text=cv_text, job_description=job_description)
    llm_engine = run_llm_engine(
        cv_text=cv_text,
        job_description=job_description,
        prompt_text=prompt_text,
    )

    missing = []
    if not code_engine.get("available"):
        missing.append("code")
    if not llm_engine.get("available"):
        missing.append("llm")
    if ats_mode == "strict" and missing:
        raise RuntimeError(
            f"Strict ATS mode failed; missing engines: {', '.join(missing)}"
        )

    code_weight, llm_weight = weights
    weighted_sum = 0.0
    active_weight = 0.0

    if code_engine.get("available"):
        weighted_sum += int(code_engine.get("score", 0)) * code_weight
        active_weight += code_weight
    if llm_engine.get("available"):
        weighted_sum += int(llm_engine.get("score", 0)) * llm_weight
        active_weight += llm_weight

    final_score = int(round(weighted_sum / active_weight)) if active_weight else 0

    return {
        "id": f"ats_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "success": True,
        "analysis_date": datetime.now().isoformat(),
        "ats_mode": ats_mode,
        "prompt_file": str(prompt_file),
        "weights": {"code": code_weight, "llm": llm_weight},
        "engines": {
            "code": code_engine,
            "llm": llm_engine,
        },
        "score": final_score,
        "summary": "Combined ATS analysis from code and LLM engines.",
    }


def fallback_ats_analysis(cv_text: str, job_description: str = "") -> dict[str, Any]:
    text_lower = cv_text.lower()
    sections = ["education", "experience", "skills", "publications", "contact"]
    sections_found = [s for s in sections if s in text_lower]
    section_score = min(30, len(sections_found) * 6)

    has_email = bool(re.search(r"[\w\.-]+@[\w\.-]+\.\w+", cv_text))
    has_phone = bool(re.search(r"\+?[\d\s()\-]{7,}", cv_text))
    has_bullets = bool(re.search(r"(^|\n)\s*[\-\*\u2022]", cv_text))
    format_score = (
        section_score
        + (20 if has_bullets else 0)
        + (10 if has_email else 0)
        + (10 if has_phone else 0)
    )

    job_tokens = (
        set(re.findall(r"[a-zA-Z][a-zA-Z\+\#\.\-]{2,}", job_description.lower()))
        if job_description
        else set()
    )
    cv_tokens = set(re.findall(r"[a-zA-Z][a-zA-Z\+\#\.\-]{2,}", text_lower))
    job_tokens = {t for t in job_tokens if len(t) > 2}
    matched = sorted(job_tokens.intersection(cv_tokens))
    missing = sorted(job_tokens.difference(cv_tokens))
    keyword_score = int((len(matched) / len(job_tokens)) * 100) if job_tokens else 65

    overall = round((0.45 * keyword_score) + (0.55 * min(100, format_score)), 1)
    recommendations = []
    if not has_email or not has_phone:
        recommendations.append("Add both email and phone in the top section.")
    if not has_bullets:
        recommendations.append(
            "Use bullet points for achievements in experience sections."
        )
    if len(sections_found) < 3:
        recommendations.append(
            "Use clear section titles: Education, Experience, Skills."
        )
    if missing[:5]:
        recommendations.append(
            f"Consider adding relevant JD keywords: {', '.join(missing[:5])}."
        )

    return {
        "id": f"ats_{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "success": True,
        "analysis_date": datetime.now().isoformat(),
        "score": int(overall),
        "summary": "ATS fallback analysis generated from CV text structure and keyword overlap.",
        "score_breakdown": {
            "keyword_score": int(keyword_score),
            "format_score": int(min(100, format_score)),
            "content_score": int(overall),
            "readability_score": int(min(100, format_score)),
        },
        "skills_comparison": {
            "match_percentage": int(keyword_score),
            "matching_keywords": matched[:50],
            "missing_keywords": missing[:50],
        },
        "recommendations": recommendations,
        "identified_sections": sections_found,
    }


def write_ats_report(report_path: Path, analysis: dict[str, Any]) -> None:
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as handle:
        json.dump(analysis, handle, indent=2)
