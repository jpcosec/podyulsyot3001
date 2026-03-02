from __future__ import annotations

import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from shutil import which
from typing import Callable

from src.cv_generator.config import CVConfig
from src.cv_generator.loaders.profile_loader import load_base_profile
from src.cv_generator.pipeline import parse_reviewed_proposal
from src.models.motivation import EmailDraftOutput, MotivationLetterOutput
from src.models.pipeline_contract import ReviewedMapping
from src.prompts import load_prompt_with_context
from src.utils.gemini import GeminiClient


@dataclass
class MotivationGenerationResult:
    letter_path: Path
    analysis_path: Path


@dataclass
class MotivationPDFResult:
    pdf_path: Path
    tex_path: Path
    log_path: Path


@dataclass
class EmailDraftResult:
    email_path: Path


def _extract_json_object(text: str) -> dict:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise ValueError("No JSON object found in LLM response")
    return json.loads(text[start : end + 1])


def _escape_latex(value: str) -> str:
    replacements = {
        "\\": r"\\textbackslash{}",
        "&": r"\\&",
        "%": r"\\%",
        "$": r"\\$",
        "#": r"\\#",
        "_": r"\\_",
        "{": r"\\{",
        "}": r"\\}",
        "~": r"\\textasciitilde{}",
        "^": r"\\textasciicircum{}",
    }
    result = value
    for key, replacement in replacements.items():
        result = result.replace(key, replacement)
    return result


def _markdown_to_latex_body(markdown_text: str) -> str:
    lines = []
    for raw in markdown_text.splitlines():
        line = raw.strip()
        if not line:
            lines.append("")
            continue
        line = re.sub(r"^#+\s*", "", line)
        line = re.sub(r"^\*\s+", "", line)
        line = re.sub(r"^-\s+", "", line)
        line = line.replace("**", "")
        lines.append(_escape_latex(line))

    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
            continue
        current.append(line)
    if current:
        paragraphs.append(" ".join(current))
    return "\n\n".join(paragraphs)


class MotivationLetterService:
    def __init__(
        self,
        config: CVConfig | None = None,
        generator: Callable[[str], str] | None = None,
    ):
        self.config = config or CVConfig.from_defaults()
        self._generator = generator
        self.gemini = GeminiClient() if generator is None else None

    def _generate(self, prompt: str) -> str:
        if self._generator is not None:
            return self._generator(prompt)
        if self.gemini is None:
            raise RuntimeError("Gemini generator is not initialized")
        return self.gemini.generate(prompt)

    def _job_dir(self, job_id: str, source: str) -> Path:
        job_dir = self.config.pipeline_root / source / job_id
        if not job_dir.exists():
            raise FileNotFoundError(
                f"Job directory not found: {job_dir} (source={source}, job_id={job_id})"
            )
        return job_dir

    @staticmethod
    def _parse_frontmatter(markdown_text: str) -> tuple[dict[str, str], str]:
        if not markdown_text.startswith("---\n"):
            return {}, markdown_text
        parts = markdown_text.split("\n---\n", 1)
        if len(parts) != 2:
            return {}, markdown_text

        frontmatter: dict[str, str] = {}
        for line in parts[0].replace("---\n", "", 1).splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            frontmatter[key.strip()] = value.strip()
        return frontmatter, parts[1]

    @staticmethod
    def _extract_heading_title(body: str) -> str:
        for line in body.splitlines():
            if line.startswith("# "):
                return line[2:].strip()
        return ""

    @staticmethod
    def _extract_checklist_items(body: str, heading: str) -> list[str]:
        lines = body.splitlines()
        target = heading.strip().lower()
        inside = False
        result: list[str] = []

        for raw in lines:
            line = raw.strip()
            if line.startswith("## "):
                inside = line[3:].strip().lower() == target
                continue
            if not inside:
                continue
            if line.startswith("- [ ] "):
                result.append(line[6:].strip())
        return result

    @staticmethod
    def _build_evidence_catalog(profile: dict) -> list[dict[str, str]]:
        catalog: list[dict[str, str]] = []
        index = 1

        def add(kind: str, text: str, source_ref: str = "profile") -> None:
            nonlocal index
            if not text.strip():
                return
            catalog.append(
                {
                    "id": f"E{index}",
                    "type": kind,
                    "text": text.strip(),
                    "source_ref": source_ref,
                }
            )
            index += 1

        for edu in profile.get("education", []):
            add("education", f"{edu.get('degree', '')} {edu.get('specialization', '')}")
            add("education", edu.get("equivalency_note", ""))

        for exp in profile.get("experience", []):
            add("role", f"{exp.get('role', '')} at {exp.get('organization', '')}")
            for achievement in exp.get("achievements", []):
                add("cv_line", achievement)

        for pub in profile.get("publications", []):
            add("publication", f"{pub.get('title', '')} {pub.get('venue', '')}")

        for category, items in profile.get("skills", {}).items():
            for item in items:
                add("skill", item, source_ref=category)

        return catalog

    @staticmethod
    def _requirement_coverage(
        requirements: list[str],
        evidence_catalog: list[dict[str, str]],
    ) -> list[dict[str, str]]:
        evidence_text = " ".join(item["text"].lower() for item in evidence_catalog)
        coverage: list[dict[str, str]] = []
        for requirement in requirements:
            req_words = [
                word for word in re.findall(r"[a-zA-Z]{4,}", requirement.lower())
            ]
            hits = [word for word in req_words if word in evidence_text]
            level = "full" if len(hits) >= 2 else "partial" if hits else "none"
            coverage.append(
                {
                    "requirement": requirement,
                    "coverage": level,
                    "matched_terms": ", ".join(hits[:5]),
                }
            )
        return coverage

    @staticmethod
    def _format_insights(job_dir: Path) -> dict[str, list[str]]:
        return {
            "strengths": [
                "Use concise academic style with explicit fit statements.",
                "Keep one clear argument per paragraph.",
            ],
            "improvements": [
                "Avoid repeating CV bullets verbatim.",
                "Reference concrete project context from the posting.",
            ],
        }

    def _load_reviewed_mapping(self, job_dir: Path) -> ReviewedMapping | None:
        reviewed_path = job_dir / "planning" / "reviewed_mapping.json"
        if reviewed_path.exists():
            payload = json.loads(reviewed_path.read_text(encoding="utf-8"))
            return ReviewedMapping.model_validate(payload)

        proposal_path = job_dir / "planning" / "match_proposal.md"
        if proposal_path.exists():
            return parse_reviewed_proposal(proposal_path)
        return None

    def build_context(self, job_id: str, source: str = "tu_berlin") -> dict:
        job_dir = self._job_dir(job_id, source)
        job_md_path = job_dir / "job.md"
        if not job_md_path.exists():
            raise FileNotFoundError(f"job.md not found: {job_md_path}")

        profile = load_base_profile(self.config.profile_path())
        job_md = job_md_path.read_text(encoding="utf-8")
        frontmatter, body = self._parse_frontmatter(job_md)
        requirements = self._extract_checklist_items(
            body, "Their Requirements (Profile)"
        )
        if not requirements:
            requirements = self._extract_checklist_items(body, "Requirements")

        evidence_catalog = self._build_evidence_catalog(profile)
        coverage = self._requirement_coverage(requirements, evidence_catalog)
        reviewed_mapping = self._load_reviewed_mapping(job_dir)

        owner = profile.get("owner", {})
        contact = owner.get("contact", {})
        context = {
            "job": {
                "title": self._extract_heading_title(body),
                "reference_number": frontmatter.get("reference_number", ""),
                "deadline": frontmatter.get("deadline", ""),
                "contact_name": frontmatter.get("contact_person", ""),
                "contact_email": frontmatter.get("contact_email", ""),
                "url": frontmatter.get("url", ""),
                "requirements": requirements,
                "full_description": body,
            },
            "candidate": {
                "name": owner.get("full_name", ""),
                "tagline": owner.get("tagline", ""),
                "summary": owner.get("professional_summary", ""),
                "email": contact.get("email", ""),
                "phone": contact.get("phone", ""),
                "profile": profile,
                "evidence_catalog": evidence_catalog,
            },
            "analysis": {
                "requirement_coverage": coverage,
                "format_insights": self._format_insights(job_dir),
            },
            "reviewed_mapping": (
                reviewed_mapping.model_dump() if reviewed_mapping is not None else None
            ),
            "approved_claims": [
                claim.model_dump()
                for claim in (reviewed_mapping.claims if reviewed_mapping else [])
                if claim.decision in {"approved", "edited"}
            ],
            "acknowledged_gaps": reviewed_mapping.gaps if reviewed_mapping else [],
            "candidate_summary": reviewed_mapping.summary if reviewed_mapping else "",
            "cv_content": (job_dir / "cv" / "to_render.md").read_text(encoding="utf-8")
            if (job_dir / "cv" / "to_render.md").exists()
            else "",
        }
        return context

    def generate_for_job(
        self, job_id: str, source: str = "tu_berlin"
    ) -> MotivationGenerationResult:
        context = self.build_context(job_id=job_id, source=source)
        
        # Check if reviewed mapping exists but is not approved
        reviewed = context.get("reviewed_mapping")
        if reviewed is not None and reviewed.get("status") != "approved":
            raise ValueError(
                "Match proposal exists but is not approved. "
                "Run 'match-approve' to lock the reviewed mapping before generating the letter."
            )
        
        prompt = load_prompt_with_context(
            "motivation_letter",
            json.dumps(context, indent=2, ensure_ascii=True),
        )
        response = self._generate(prompt)
        payload = _extract_json_object(response)
        parsed = MotivationLetterOutput.model_validate(payload)

        job_dir = self._job_dir(job_id, source)
        planning_dir = job_dir / "planning"
        planning_dir.mkdir(parents=True, exist_ok=True)

        letter_path = planning_dir / "motivation_letter.md"
        letter_path.write_text(parsed.letter_markdown.strip() + "\n", encoding="utf-8")

        analysis_path = planning_dir / "motivation_letter.analysis.json"
        analysis_path.write_text(
            json.dumps(parsed.model_dump(), indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        return MotivationGenerationResult(
            letter_path=letter_path, analysis_path=analysis_path
        )

    def build_pdf_for_job(
        self,
        job_id: str,
        source: str = "tu_berlin",
        letter_name: str = "motivation_letter.md",
        pdf_name: str = "motivation_letter.pdf",
    ) -> MotivationPDFResult:
        pdflatex = which("pdflatex")
        if not pdflatex:
            raise RuntimeError("PDF build requires pdflatex in PATH")

        job_dir = self._job_dir(job_id, source)
        planning_path = job_dir / "planning" / letter_name
        if not planning_path.exists():
            raise FileNotFoundError(f"Motivation markdown not found: {planning_path}")

        build_dir = job_dir / "build" / "motivation_letter"
        build_dir.mkdir(parents=True, exist_ok=True)

        latex_body = _markdown_to_latex_body(planning_path.read_text(encoding="utf-8"))
        tex_path = build_dir / "motivation_letter.tex"
        tex_path.write_text(
            "\n".join(
                [
                    "\\documentclass[11pt,a4paper]{article}",
                    "\\usepackage[utf8]{inputenc}",
                    "\\usepackage[T1]{fontenc}",
                    "\\usepackage[margin=2.4cm]{geometry}",
                    "\\setlength{\\parskip}{0.8em}",
                    "\\setlength{\\parindent}{0pt}",
                    "\\begin{document}",
                    latex_body,
                    "\\end{document}",
                    "",
                ]
            ),
            encoding="utf-8",
        )

        result = subprocess.run(
            [pdflatex, "-interaction=nonstopmode", tex_path.name],
            cwd=build_dir,
            capture_output=True,
            text=True,
        )
        generated_pdf = build_dir / "motivation_letter.pdf"
        if result.returncode != 0 and not generated_pdf.exists():
            raise RuntimeError(
                "pdflatex failed for motivation letter: "
                + (result.stderr.strip() or result.stdout[-1000:])
            )

        output_dir = job_dir / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_pdf = output_dir / pdf_name
        output_pdf.write_bytes(generated_pdf.read_bytes())

        return MotivationPDFResult(
            pdf_path=output_pdf,
            tex_path=tex_path,
            log_path=build_dir / "motivation_letter.log",
        )

    def generate_email_draft(
        self, job_id: str, source: str = "tu_berlin"
    ) -> EmailDraftResult:
        context = self.build_context(job_id=job_id, source=source)
        job = context["job"]
        candidate = context["candidate"]

        payload = EmailDraftOutput(
            to=job.get("contact_email", "") or "application@tu-berlin.de",
            subject=(
                f"Application for {job.get('title', 'Research Assistant')} "
                f"({job.get('reference_number', 'N/A')})"
            ),
            salutation=(
                f"Dear {job.get('contact_name')},"
                if job.get("contact_name")
                else "Dear Hiring Committee,"
            ),
            body=(
                "I am writing to submit my application for the role. "
                "Please find attached my motivation letter and CV."
            ),
            closing="Best regards,",
            sender_name=candidate.get("name", ""),
            sender_email=candidate.get("email", ""),
            sender_phone=candidate.get("phone", ""),
        )

        job_dir = self._job_dir(job_id, source)
        planning_dir = job_dir / "planning"
        planning_dir.mkdir(parents=True, exist_ok=True)
        email_path = planning_dir / "application_email.md"
        email_path.write_text(
            "\n".join(
                [
                    f"To: {payload.to}",
                    f"Subject: {payload.subject}",
                    "",
                    payload.salutation,
                    "",
                    payload.body,
                    "",
                    payload.closing,
                    payload.sender_name,
                    payload.sender_email,
                    payload.sender_phone,
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return EmailDraftResult(email_path=email_path)
