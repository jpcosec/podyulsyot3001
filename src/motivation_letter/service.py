from __future__ import annotations

import hashlib
import json
import re
import subprocess
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from shutil import which
from typing import Any, Callable

from src.cv_generator.config import CVConfig
from src.cv_generator.loaders.profile_loader import load_base_profile
from src.cv_generator.model import CVModel
from src.models.motivation import EmailDraftOutput, MotivationLetterOutput
from src.prompts import load_prompt_with_context

_TOKEN_STOPWORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "to",
    "with",
}


@dataclass(frozen=True)
class MotivationGenerationResult:
    letter_path: Path
    analysis_path: Path


@dataclass(frozen=True)
class MotivationPreLetterResult:
    pre_letter_path: Path
    analysis_path: Path


@dataclass(frozen=True)
class MotivationPdfResult:
    tex_path: Path
    pdf_path: Path


@dataclass(frozen=True)
class MotivationEmailResult:
    email_path: Path
    subject: str


class MotivationLetterService:
    def __init__(
        self,
        config: CVConfig | None = None,
        generator: Callable[[str], str] | None = None,
    ) -> None:
        self.config = config or CVConfig.from_defaults()
        self.gemini = self._build_gemini_client()
        self.evidence_bank_path = self.config.project_root / Path(
            "data/reference_data/profile/evidence/evidence_bank.json"
        )
        self._generator = generator or self._default_generator

    @staticmethod
    def _build_gemini_client() -> Any:
        try:
            from src.utils.gemini import GeminiClient
        except ImportError:
            return None
        try:
            return GeminiClient()
        except Exception:
            return None

    def build_context(self, job_id: str, source: str = "tu_berlin") -> dict[str, Any]:
        job_dir = self.config.pipeline_root / source / job_id
        job_md_path = job_dir / "job.md"
        if not job_md_path.exists():
            raise FileNotFoundError(
                f"job.md not found for source={source} job_id={job_id}"
            )

        inspiration_path = job_dir / "planning" / "motivation_letter copy.md"

        profile = load_base_profile(self.config.profile_path())
        model = CVModel.from_profile(profile)
        job_content = job_md_path.read_text(encoding="utf-8")
        frontmatter = self._parse_frontmatter(job_content)

        requirements = self._extract_checklist_items(job_content, "Their Requirements")
        responsibilities = self._extract_checklist_items(
            job_content, "Area of Responsibility"
        )
        fit_signals = self._extract_bullet_items(job_content, "How I Match")
        evidence_catalog = self._build_evidence_catalog(model=model, profile=profile)
        requirement_coverage = self._analyze_requirement_coverage(
            requirements=requirements,
            evidence_catalog=evidence_catalog,
        )
        format_insights = self._build_inspiration_insights(inspiration_path)

        planning_dir = job_dir / "planning"
        return {
            "meta": {
                "generated_on": str(date.today()),
                "source": source,
                "job_id": job_id,
            },
            "job": {
                "title": self._extract_posting_title(
                    job_content, default=f"Job {job_id}"
                ),
                "reference_number": frontmatter.get("reference_number", ""),
                "university": frontmatter.get("university", ""),
                "deadline": frontmatter.get("deadline", ""),
                "contact_email": frontmatter.get("contact_email", ""),
                "contact_name": "",
                "url": frontmatter.get("url", ""),
                "requirements": requirements,
                "responsibilities": responsibilities,
                "fit_signals_from_job_tracker": fit_signals,
            },
            "candidate": {
                **self._build_candidate_payload(model=model, profile=profile),
                "evidence_catalog": evidence_catalog,
            },
            "analysis": {
                "requirement_coverage": requirement_coverage,
                "format_insights": format_insights,
            },
            "artifacts": {
                "job_md": str(job_md_path.relative_to(self.config.project_root)),
                "planning_dir": str(planning_dir.relative_to(self.config.project_root)),
                "cv_tailoring_md": str(
                    (planning_dir / "cv_tailoring.md").relative_to(
                        self.config.project_root
                    )
                ),
                "previous_motivation_md": str(
                    (planning_dir / "motivation_letter.md").relative_to(
                        self.config.project_root
                    )
                ),
                "pre_motivation_md": str(
                    (planning_dir / "motivation_letter.pre.md").relative_to(
                        self.config.project_root
                    )
                ),
                "evidence_bank_json": str(
                    self.evidence_bank_path.relative_to(self.config.project_root)
                ),
                "inspiration_letter": str(
                    inspiration_path.relative_to(self.config.project_root)
                ),
            },
            "constraints": {
                "max_words": 520,
                "min_words": 320,
                "must_include_reference_in_subject_when_available": True,
                "body_style": "formal_paragraphs_only",
            },
        }

    def build_prompt(self, context: dict[str, Any]) -> str:
        context_json = json.dumps(context, indent=2, ensure_ascii=True)
        return load_prompt_with_context("motivation_letter", context_json)

    def create_pre_letter(
        self, job_id: str, source: str = "tu_berlin"
    ) -> MotivationPreLetterResult:
        """Generate a motivation letter plan using the pre-letter agent.

        Instead of hardcoded keyword matching, the agent analyzes
        the job and profile to produce a section plan with evidence assignments.
        """
        context = self.build_context(job_id=job_id, source=source)
        context_json = json.dumps(context, indent=2, default=str)
        prompt = load_prompt_with_context("motivation_pre_letter", context_json)

        if self.gemini is None:
            raise RuntimeError("Gemini client is not available in this environment")
        response = self.gemini.generate(prompt)
        plan = json.loads(response)

        job_dir = self.config.pipeline_root / source / job_id
        planning_dir = job_dir / "planning"
        planning_dir.mkdir(parents=True, exist_ok=True)

        plan_path = planning_dir / "motivation_letter.pre.json"
        plan_path.write_text(json.dumps(plan, indent=2), encoding="utf-8")

        md_path = planning_dir / "motivation_letter.pre.md"
        md_path.write_text(self._plan_to_markdown(plan, context), encoding="utf-8")

        return MotivationPreLetterResult(
            pre_letter_path=md_path,
            analysis_path=plan_path,
        )

    def generate_for_job(
        self, job_id: str, source: str = "tu_berlin"
    ) -> MotivationGenerationResult:
        """Generate the final motivation letter using the LLM agent.

        If a pre-letter plan exists, inject it into the context
        so the agent expands the plan into final prose.
        """
        context = self.build_context(job_id=job_id, source=source)

        job_dir = self.config.pipeline_root / source / job_id
        plan_path = job_dir / "planning" / "motivation_letter.pre.json"
        if plan_path.exists():
            context["pre_letter"] = json.loads(plan_path.read_text(encoding="utf-8"))

        context_json = json.dumps(context, indent=2, default=str)
        prompt = load_prompt_with_context("motivation_letter", context_json)

        response = self._generator(prompt)
        result = MotivationLetterOutput.model_validate_json(response)

        planning_dir = job_dir / "planning"
        planning_dir.mkdir(parents=True, exist_ok=True)

        letter_path = planning_dir / "motivation_letter.md"
        letter_path.write_text(result.letter_markdown, encoding="utf-8")

        analysis_path = planning_dir / "motivation_letter.analysis.json"
        analysis_path.write_text(result.model_dump_json(indent=2), encoding="utf-8")

        return MotivationGenerationResult(
            letter_path=letter_path,
            analysis_path=analysis_path,
        )

    def build_pdf_for_job(
        self,
        job_id: str,
        source: str = "tu_berlin",
        letter_name: str = "motivation_letter.md",
        pdf_name: str = "motivation_letter.pdf",
    ) -> MotivationPdfResult:
        pdflatex = which("pdflatex")
        if not pdflatex:
            raise RuntimeError("PDF build requires 'pdflatex' available in PATH")

        job_dir = self.config.pipeline_root / source / job_id
        planning_dir = job_dir / "planning"
        letter_path = planning_dir / letter_name
        if not letter_path.exists():
            raise FileNotFoundError(
                f"Motivation letter markdown not found: {letter_path}"
            )

        build_dir = job_dir / "build" / "motivation_letter"
        output_dir = job_dir / "output"
        build_dir.mkdir(parents=True, exist_ok=True)
        output_dir.mkdir(parents=True, exist_ok=True)

        tex_stem = Path(pdf_name).stem
        tex_path = build_dir / f"{tex_stem}.tex"
        temp_pdf_path = build_dir / f"{tex_stem}.pdf"
        output_pdf_path = output_dir / pdf_name

        markdown_text = letter_path.read_text(encoding="utf-8")
        tex_path.write_text(self._render_letter_tex(markdown_text), encoding="utf-8")

        result = subprocess.run(
            [pdflatex, "-interaction=nonstopmode", "-halt-on-error", tex_path.name],
            cwd=build_dir,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0 and not temp_pdf_path.exists():
            tail = result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout
            err = result.stderr.strip()
            message = err or tail or "unknown pdflatex failure"
            raise RuntimeError(f"pdflatex failed for {tex_path}:\n{message}")
        if not temp_pdf_path.exists():
            raise RuntimeError(
                f"Expected PDF not produced by pdflatex: {temp_pdf_path}"
            )

        if output_pdf_path.exists():
            output_pdf_path.unlink()
        temp_pdf_path.replace(output_pdf_path)
        return MotivationPdfResult(tex_path=tex_path, pdf_path=output_pdf_path)

    def generate_email_draft(
        self, job_id: str, source: str = "tu_berlin"
    ) -> MotivationEmailResult:
        """Generate an application email draft using the email agent."""
        context = self.build_context(job_id=job_id, source=source)

        email_context = {
            "job": context["job"],
            "candidate": context["candidate"],
        }
        context_json = json.dumps(email_context, indent=2, default=str)
        prompt = load_prompt_with_context("email_draft", context_json)

        if self.gemini is None:
            raise RuntimeError("Gemini client is not available in this environment")
        response = self.gemini.generate(prompt)
        result = EmailDraftOutput.model_validate_json(response)

        job_dir = self.config.pipeline_root / source / job_id
        planning_dir = job_dir / "planning"
        planning_dir.mkdir(parents=True, exist_ok=True)
        email_path = planning_dir / "application_email.md"

        email_lines = [
            f"To: {result.to}",
            f"Subject: {result.subject}",
            "",
            result.salutation,
            "",
            result.body,
            "",
            result.closing,
            result.sender_name,
            result.sender_email,
            result.sender_phone,
        ]
        email_path.write_text("\n".join(email_lines).strip() + "\n", encoding="utf-8")

        return MotivationEmailResult(email_path=email_path, subject=result.subject)

    def _plan_to_markdown(self, plan: dict[str, Any], context: dict[str, Any]) -> str:
        """Convert the pre-letter plan JSON to human-readable markdown."""
        lines = ["# Motivation Letter Plan", ""]
        evidence_by_id = {
            item["id"]: item
            for item in context.get("candidate", {}).get("evidence_catalog", [])
        }
        for section, data in plan.get("sections", {}).items():
            lines.append(f"## {section.replace('_', ' ').title()}")
            lines.append(f"**Angle:** {data.get('planning_note', '')}")
            for evidence_id in data.get("evidence_ids", []):
                evidence = evidence_by_id.get(evidence_id, {})
                lines.append(f"- [{evidence_id}] {evidence.get('text', 'unknown')}")
            lines.append("")

        if plan.get("gaps"):
            lines.append("## Gaps")
            for gap in plan["gaps"]:
                lines.append(f"- **{gap['severity']}**: {gap['requirement']}")
        return "\n".join(lines)

    def _default_generator(self, prompt: str) -> str:
        if self.gemini is None:
            raise RuntimeError("Gemini client is not available in this environment")
        return self.gemini.generate(prompt)

    def _update_evidence_bank(
        self,
        source: str,
        job_id: str,
        evidence_catalog: list[dict[str, Any]],
        requirement_coverage: list[dict[str, Any]],
    ) -> Path:
        self.evidence_bank_path.parent.mkdir(parents=True, exist_ok=True)
        bank = self._load_evidence_bank()
        now_utc = datetime.now(timezone.utc).isoformat()
        job_key = f"{source}/{job_id}"

        fingerprint_to_item = {
            item["fingerprint"]: item for item in bank.get("items", [])
        }
        next_index = self._next_evidence_bank_index(bank.get("items", []))

        runtime_id_to_bank_id: dict[str, str] = {}
        for evidence in evidence_catalog:
            fingerprint = self._fingerprint(evidence["category"], evidence["text"])
            runtime_id = evidence["id"]
            item = fingerprint_to_item.get(fingerprint)

            if item is None:
                bank_id = f"EB{next_index:05d}"
                next_index += 1
                item = {
                    "bank_id": bank_id,
                    "fingerprint": fingerprint,
                    "category": evidence["category"],
                    "text": evidence["text"],
                    "tags": sorted(set(evidence.get("tags", []))),
                    "source_refs": [evidence.get("source_ref", "")],
                    "first_seen_utc": now_utc,
                    "last_seen_utc": now_utc,
                    "used_in_jobs": [job_key],
                    "linked_requirements": [],
                }
                bank.setdefault("items", []).append(item)
                fingerprint_to_item[fingerprint] = item
            else:
                item["last_seen_utc"] = now_utc
                item["used_in_jobs"] = self._merge_unique(
                    item.get("used_in_jobs", []), [job_key]
                )
                item["source_refs"] = self._merge_unique(
                    item.get("source_refs", []), [evidence.get("source_ref", "")]
                )
                item["tags"] = self._merge_unique(
                    item.get("tags", []), evidence.get("tags", [])
                )

            runtime_id_to_bank_id[runtime_id] = item["bank_id"]

        linked_entries: list[dict[str, Any]] = []
        for entry in requirement_coverage:
            if entry.get("coverage") == "none":
                continue
            bank_ids = [
                runtime_id_to_bank_id[eid]
                for eid in entry.get("evidence_ids", [])
                if eid in runtime_id_to_bank_id
            ]
            if not bank_ids:
                continue

            linked_entries.append(
                {
                    "requirement": entry.get("requirement", ""),
                    "coverage": entry.get("coverage", "partial"),
                    "evidence_bank_ids": sorted(set(bank_ids)),
                }
            )

            for bank_id in bank_ids:
                item = self._find_bank_item(bank, bank_id)
                if item is not None:
                    item["linked_requirements"] = self._merge_unique(
                        item.get("linked_requirements", []),
                        [entry.get("requirement", "")],
                    )

        bank.setdefault("job_runs", []).append(
            {
                "run_id": f"{job_key}/{now_utc}",
                "source": source,
                "job_id": job_id,
                "generated_at_utc": now_utc,
                "linked_requirements": linked_entries,
            }
        )
        bank["updated_at_utc"] = now_utc

        self.evidence_bank_path.write_text(
            json.dumps(bank, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )
        return self.evidence_bank_path

    def _load_evidence_bank(self) -> dict[str, Any]:
        if not self.evidence_bank_path.exists():
            return {
                "version": "1.0",
                "updated_at_utc": "",
                "items": [],
                "job_runs": [],
            }

        payload = json.loads(self.evidence_bank_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Evidence bank file must contain a JSON object")

        payload.setdefault("items", [])
        payload.setdefault("job_runs", [])
        payload.setdefault("version", "1.0")
        payload.setdefault("updated_at_utc", "")
        return payload

    @staticmethod
    def _find_bank_item(bank: dict[str, Any], bank_id: str) -> dict[str, Any] | None:
        for item in bank.get("items", []):
            if item.get("bank_id") == bank_id:
                return item
        return None

    @staticmethod
    def _next_evidence_bank_index(items: list[dict[str, Any]]) -> int:
        max_index = 0
        for item in items:
            bank_id = item.get("bank_id", "")
            match = re.match(r"^EB(\d+)$", bank_id)
            if not match:
                continue
            max_index = max(max_index, int(match.group(1)))
        return max_index + 1

    @staticmethod
    def _render_format_insights_lines(format_insights: dict[str, Any]) -> list[str]:
        strengths = format_insights.get("strengths", [])
        improvements = format_insights.get("improvements", [])
        detected = format_insights.get("detected_structure", {})

        lines = ["- Preserve strengths:"]
        for item in strengths[:5]:
            lines.append(f"  - {item}")

        lines.append("- Apply improvements:")
        for item in improvements[:5]:
            lines.append(f"  - {item}")

        if detected:
            lines.append(
                "- Detected metrics: "
                + f"paragraphs={detected.get('body_paragraph_count', 0)}, "
                + f"avg_sentence_words={detected.get('avg_sentence_words', 0)}"
            )

        source_exists = format_insights.get("source_exists")
        source_path = format_insights.get("source_path", "")
        if source_path:
            lines.append(
                f"- Inspiration source: {source_path} (exists={str(source_exists).lower()})"
            )

        return lines

    @staticmethod
    def _render_evidence_lines(evidence_refs: list[dict[str, str]]) -> list[str]:
        if not evidence_refs:
            return ["- [no strong evidence selected yet]"]

        lines: list[str] = []
        for item in evidence_refs:
            lines.append(f"- [{item['id']}] ({item['category']}) {item['text']}")
        return lines

    @staticmethod
    def _render_evidence_cards(evidence_catalog: list[dict[str, Any]]) -> list[str]:
        lines: list[str] = []
        for item in evidence_catalog:
            tags = ", ".join(item.get("tags", [])[:8])
            lines.extend(
                [
                    f"### {item['id']} - {item['category']}",
                    f"- Evidence: {item['text']}",
                    f"- Source: {item.get('source_ref', '')}",
                    f"- Tags: {tags}",
                    "- Link to proof: [ADD LINK]",
                    "- Reuse notes: [ADD NOTE FOR CV/LETTER REUSE]",
                    "",
                ]
            )
        return lines

    @staticmethod
    def _parse_frontmatter(markdown_text: str) -> dict[str, str]:
        match = re.search(
            r"^---\n(.*?)\n---", markdown_text, flags=re.DOTALL | re.MULTILINE
        )
        if not match:
            return {}

        result: dict[str, str] = {}
        for line in match.group(1).splitlines():
            if ":" not in line:
                continue
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip()
        return result

    @staticmethod
    def _extract_posting_title(markdown_text: str, default: str) -> str:
        match = re.search(r"^#\s+(.+)$", markdown_text, flags=re.MULTILINE)
        if not match:
            return default
        return match.group(1).strip()

    @staticmethod
    def _extract_section_block(markdown_text: str, section_fragment: str) -> str:
        escaped = re.escape(section_fragment)
        pattern = re.compile(
            rf"^##[^\n]*{escaped}[^\n]*\n(.*?)(?=^##\s|\Z)",
            flags=re.IGNORECASE | re.MULTILINE | re.DOTALL,
        )
        match = pattern.search(markdown_text)
        return match.group(1).strip() if match else ""

    def _extract_checklist_items(
        self, markdown_text: str, section_fragment: str
    ) -> list[str]:
        block = self._extract_section_block(markdown_text, section_fragment)
        if not block:
            return []

        items: list[str] = []
        for line in block.splitlines():
            match = re.match(r"^-\s*\[[xX\s]\]\s+(.*)$", line.strip())
            if match:
                items.append(match.group(1).strip())
        return items

    def _extract_bullet_items(
        self, markdown_text: str, section_fragment: str
    ) -> list[str]:
        block = self._extract_section_block(markdown_text, section_fragment)
        if not block:
            return []

        items: list[str] = []
        for line in block.splitlines():
            stripped = line.strip()
            if not stripped.startswith("- "):
                continue
            if re.match(r"^-\s*\[[xX\s]\]", stripped):
                continue
            items.append(stripped[2:].strip())
        return items

    @staticmethod
    def _build_candidate_payload(
        model: CVModel, profile: dict[str, Any]
    ) -> dict[str, Any]:
        education = [
            {
                "degree": entry.degree,
                "specialization": entry.specialization,
                "institution": entry.institution,
                "start_date": entry.start_date,
                "end_date": entry.end_date,
                "equivalency_note": entry.equivalency_note,
            }
            for entry in model.education
        ]

        experience = []
        for entry in model.experience:
            experience.append(
                {
                    "role": entry.role,
                    "organization": entry.organization,
                    "location": entry.location,
                    "start_date": entry.start_date,
                    "end_date": entry.end_date,
                    "achievements": entry.achievements,
                }
            )

        publications = [
            {"year": pub.year, "title": pub.title, "venue": pub.venue, "url": pub.url}
            for pub in model.publications
        ]

        return {
            "name": model.full_name,
            "tagline": model.tagline,
            "summary": model.summary,
            "contact": {
                "email": model.contact.email,
                "phone": model.contact.phone,
                "address": model.contact.address,
                "linkedin": model.contact.linkedin,
                "github": model.contact.github,
            },
            "education": education,
            "experience": experience,
            "publications": publications,
            "languages": [
                {"name": item.name, "level": item.level, "note": item.note}
                for item in model.languages
            ],
            "skills": model.skills,
            "legal_status": profile.get("owner", {}).get("legal_status", {}),
        }

    def _build_inspiration_insights(self, inspiration_path: Path) -> dict[str, Any]:
        insights = {
            "source_path": str(inspiration_path.relative_to(self.config.project_root)),
            "source_exists": inspiration_path.exists(),
            "strengths": [],
            "improvements": [],
            "target_structure": [
                "Header and date",
                "Recipient block",
                "Subject with reference number",
                "Salutation",
                "Body paragraph 1: role alignment hook",
                "Body paragraph 2: formal eligibility",
                "Body paragraph 3: technical fit",
                "Body paragraph 4: project motivation",
                "Body paragraph 5: closing",
                "Signature block",
            ],
            "detected_structure": {},
        }

        if not inspiration_path.exists():
            insights["strengths"] = [
                "Use explicit role and reference targeting in the opening.",
                "Keep requirement-to-evidence mapping concrete and concise.",
            ]
            insights["improvements"] = [
                "Add lab-specific links and quantified evidence where possible.",
            ]
            return insights

        letter_text = inspiration_path.read_text(encoding="utf-8")
        detected = self._analyze_inspiration_letter(letter_text)
        insights["detected_structure"] = detected

        strengths: list[str] = []
        if detected["has_reference_in_subject"]:
            strengths.append(
                "Clear role targeting with explicit job reference in the opening."
            )
        if detected["has_formal_eligibility_signal"]:
            strengths.append(
                "Early formal eligibility handling (degree equivalency or compliance)."
            )
        if detected["has_technical_fit_signal"]:
            strengths.append(
                "Direct requirement-to-evidence mapping in technical-fit paragraph."
            )
        if detected["has_project_motivation_signal"]:
            strengths.append(
                "Project-motivation paragraph tied to scientific direction and doctoral intent."
            )
        if detected["has_professional_closing"]:
            strengths.append("Professional and concise closing with explicit interest.")

        improvements: list[str] = []
        if not detected["has_external_links"]:
            improvements.append(
                "Add 1-2 concrete lab or group references (paper/project links)."
            )
        if not detected["has_quantified_signal"]:
            improvements.append(
                "Increase quantified evidence where available (scale, outcomes, metrics)."
            )
        if detected["avg_sentence_words"] > 24:
            improvements.append("Split long dense sentences for recruiter readability.")
        if not detected["has_proof_link_signal"]:
            improvements.append("Attach explicit proof links to high-impact claims.")

        insights["strengths"] = strengths or [
            "Keep exact role/reference targeting and concrete evidence mapping.",
        ]
        insights["improvements"] = improvements or [
            "Maintain concise paragraphs and evidence-backed claims.",
        ]
        return insights

    @staticmethod
    def _analyze_inspiration_letter(letter_text: str) -> dict[str, Any]:
        lines = [line.rstrip() for line in letter_text.splitlines()]
        lower_text = letter_text.lower()

        subject_line = next(
            (
                line.strip()
                for line in lines
                if line.strip().lower().startswith("subject:")
            ),
            "",
        )
        salutation_index = next(
            (
                index
                for index, line in enumerate(lines)
                if line.strip().lower().startswith("dear ")
            ),
            -1,
        )
        closing_index = next(
            (
                index
                for index, line in enumerate(lines)
                if line.strip().lower() in {"sincerely,", "kind regards,"}
            ),
            -1,
        )

        body_start = salutation_index + 1 if salutation_index >= 0 else 0
        body_end = closing_index if closing_index >= 0 else len(lines)
        body_lines = lines[body_start:body_end]
        body_paragraphs = MotivationLetterService._split_paragraphs(body_lines)

        sentence_count = max(1, len(re.findall(r"[.!?]", "\n".join(body_paragraphs))))
        word_count = len(re.findall(r"\b\w+\b", "\n".join(body_paragraphs)))
        avg_sentence_words = round(word_count / sentence_count, 2)

        return {
            "has_subject": bool(subject_line),
            "has_reference_in_subject": bool(
                re.search(r"[A-Za-z]+-\d+/\d+|\b\d{5,}\b", subject_line)
            ),
            "has_salutation": salutation_index >= 0,
            "body_paragraph_count": len(body_paragraphs),
            "avg_sentence_words": avg_sentence_words,
            "has_formal_eligibility_signal": any(
                token in lower_text
                for token in ("anabin", "equivalent", "equivalency", "mobility rule")
            ),
            "has_technical_fit_signal": any(
                token in lower_text
                for token in (
                    "python",
                    "airflow",
                    "mlops",
                    "orchestration",
                    "deployment",
                )
            ),
            "has_project_motivation_signal": any(
                token in lower_text
                for token in ("fair", "interdisciplinary", "doctoral", "phd")
            ),
            "has_professional_closing": closing_index >= 0,
            "has_external_links": bool(re.search(r"https?://|www\.", letter_text)),
            "has_proof_link_signal": any(
                token in lower_text
                for token in ("attached", "certificate", "supporting documents")
            ),
            "has_quantified_signal": bool(
                re.search(r"\b\d+(?:\.\d+)?%?\b", letter_text)
            ),
        }

    @staticmethod
    def _split_paragraphs(lines: list[str]) -> list[str]:
        paragraphs: list[str] = []
        buffer: list[str] = []
        for line in lines:
            stripped = line.strip()
            if not stripped:
                if buffer:
                    paragraphs.append(" ".join(buffer).strip())
                    buffer = []
                continue
            buffer.append(stripped)

        if buffer:
            paragraphs.append(" ".join(buffer).strip())
        return paragraphs

    def _build_evidence_catalog(
        self, model: CVModel, profile: dict[str, Any]
    ) -> list[dict[str, Any]]:
        items: list[dict[str, Any]] = []

        def add(category: str, text: str, source_ref: str) -> None:
            normalized = text.strip()
            if not normalized:
                return

            evidence_id = f"EV{len(items) + 1:03d}"
            items.append(
                {
                    "id": evidence_id,
                    "category": category,
                    "text": normalized,
                    "source_ref": source_ref,
                    "tags": self._build_search_tags(normalized),
                }
            )

        add("summary", model.summary, "profile.owner.professional_summary")
        add("tagline", model.tagline, "profile.owner.tagline")

        for edu in model.education:
            text = (
                f"{edu.degree} ({edu.specialization}) at {edu.institution} "
                f"from {edu.start_date} to {edu.end_date}. {edu.equivalency_note}".strip()
            )
            add("education", text, "profile.education")

        for exp in model.experience:
            add(
                "experience",
                f"{exp.role} at {exp.organization} ({exp.start_date} to {exp.end_date})",
                "profile.experience",
            )
            for achievement in exp.achievements:
                add(
                    "achievement",
                    f"{exp.role} / {exp.organization}: {achievement}",
                    "profile.experience.achievements",
                )

        for pub in model.publications:
            add(
                "publication",
                f"{pub.year}: {pub.title} ({pub.venue})",
                "profile.publications",
            )

        for lang in model.languages:
            note = f" ({lang.note})" if lang.note else ""
            add("language", f"{lang.name}: {lang.level}{note}", "profile.languages")

        for category, values in model.skills.items():
            if not values:
                continue
            joined = ", ".join(values[:12])
            add("skill", f"{category}: {joined}", f"profile.skills.{category}")

        legal_status = profile.get("owner", {}).get("legal_status", {})
        visa_type = legal_status.get("visa_type")
        if visa_type:
            add(
                "legal",
                f"Visa type: {visa_type}; work permission Germany: {legal_status.get('work_permission_germany')}",
                "profile.owner.legal_status",
            )

        return items

    def _analyze_requirement_coverage(
        self, requirements: list[str], evidence_catalog: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        coverage_entries: list[dict[str, Any]] = []

        for requirement in requirements:
            req_tags = set(self._build_search_tags(requirement))
            scored: list[tuple[str, float]] = []
            for evidence in evidence_catalog:
                score = self._requirement_evidence_score(
                    requirement=requirement,
                    req_tags=req_tags,
                    evidence=evidence,
                )
                if score > 0:
                    scored.append((evidence["id"], score))

            scored.sort(key=lambda pair: pair[1], reverse=True)
            best = scored[:3]
            best_score = best[0][1] if best else 0.0
            if best_score >= 0.35:
                coverage = "full"
            elif best_score >= 0.18:
                coverage = "partial"
            else:
                coverage = "none"

            coverage_entries.append(
                {
                    "requirement": requirement,
                    "coverage": coverage,
                    "evidence_ids": [item_id for item_id, _ in best],
                    "best_score": round(best_score, 3),
                }
            )

        return coverage_entries

    def _requirement_evidence_score(
        self,
        requirement: str,
        req_tags: set[str],
        evidence: dict[str, Any],
    ) -> float:
        if not req_tags:
            return 0.0

        evidence_text = evidence.get("text", "")
        evidence_tags = set(evidence.get("tags", []))
        overlap = req_tags & evidence_tags
        if not overlap:
            return 0.0

        base = len(overlap) / len(req_tags)
        requirement_lower = requirement.lower()
        bonus = 0.0
        if requirement_lower in evidence_text.lower():
            bonus += 0.2

        domain_keywords = {
            "python",
            "airflow",
            "mlops",
            "fair",
            "workflow",
            "monitoring",
            "deployment",
            "orchestration",
        }
        if overlap & domain_keywords:
            bonus += 0.1

        return min(1.0, base + bonus)

    @staticmethod
    def _build_search_tags(text: str) -> list[str]:
        tokens = re.findall(r"[A-Za-z0-9\-\+\.]{3,}", text.lower())
        filtered = [token for token in tokens if token not in _TOKEN_STOPWORDS]
        return sorted(set(filtered))

    @staticmethod
    def _merge_unique(existing: list[str], new_items: list[str]) -> list[str]:
        merged = list(existing)
        for item in new_items:
            if not item:
                continue
            if item in merged:
                continue
            merged.append(item)
        return sorted(merged)

    @staticmethod
    def _fingerprint(category: str, text: str) -> str:
        normalized = re.sub(r"\s+", " ", text.strip().lower())
        payload = f"{category}|{normalized}".encode("utf-8")
        return hashlib.sha256(payload).hexdigest()

    def _render_letter_tex(self, markdown_text: str) -> str:
        blocks = self._extract_letter_blocks(markdown_text)
        body = self._render_letter_body_from_blocks(blocks)
        lines = [
            r"\documentclass[11pt,a4paper]{article}",
            r"\usepackage[utf8]{inputenc}",
            r"\usepackage[T1]{fontenc}",
            r"\usepackage[a4paper,margin=2.5cm]{geometry}",
            r"\usepackage{lmodern}",
            r"\usepackage{microtype}",
            r"\setlength{\parindent}{0pt}",
            r"\setlength{\parskip}{0.75em}",
            r"\linespread{1.04}",
            r"\begin{document}",
            r"\sloppy",
            body,
            r"\end{document}",
            "",
        ]
        return "\n".join(lines)

    def _extract_letter_blocks(self, markdown_text: str) -> dict[str, Any]:
        lines = [line.rstrip() for line in markdown_text.splitlines()]
        clean_lines = [line.strip() for line in lines]

        def first_non_empty(start: int = 0) -> tuple[int, str]:
            for index in range(start, len(clean_lines)):
                if clean_lines[index]:
                    return index, clean_lines[index]
            return -1, ""

        date_index, date_line = first_non_empty(0)
        subject_index = next(
            (
                index
                for index, line in enumerate(clean_lines)
                if line.lower().startswith("subject:")
            ),
            -1,
        )
        salutation_index = next(
            (
                index
                for index, line in enumerate(clean_lines)
                if line.lower().startswith("dear ")
            ),
            -1,
        )
        closing_index = next(
            (
                index
                for index, line in enumerate(clean_lines)
                if line.lower() in {"sincerely,", "best regards,"}
            ),
            -1,
        )

        recipient_lines: list[str] = []
        if subject_index > date_index >= 0:
            recipient_lines = [
                line for line in clean_lines[date_index + 1 : subject_index] if line
            ]

        subject_line = clean_lines[subject_index] if subject_index >= 0 else ""
        salutation_line = clean_lines[salutation_index] if salutation_index >= 0 else ""

        body_start = salutation_index + 1 if salutation_index >= 0 else 0
        body_end = closing_index if closing_index >= 0 else len(clean_lines)
        body_lines = clean_lines[body_start:body_end]
        body_paragraphs = self._split_paragraphs(body_lines)

        closing_line = clean_lines[closing_index] if closing_index >= 0 else ""
        signature_lines: list[str] = []
        if closing_index >= 0:
            signature_lines = [
                line for line in clean_lines[closing_index + 1 :] if line
            ]

        return {
            "date": date_line,
            "recipient": recipient_lines,
            "subject": subject_line,
            "salutation": salutation_line,
            "body": body_paragraphs,
            "closing": closing_line,
            "signature": signature_lines,
        }

    def _render_letter_body_from_blocks(self, blocks: dict[str, Any]) -> str:
        output: list[str] = []

        date_line = blocks.get("date", "")
        if date_line:
            output.append(r"\begin{flushright}")
            output.append(self._escape_latex(date_line))
            output.append(r"\end{flushright}")
            output.append(r"\vspace{1.1em}")

        recipient = blocks.get("recipient", [])
        if recipient:
            output.append(r"\begin{flushleft}")
            for line in recipient:
                output.append(self._escape_latex(line) + r"\\")
            output.append(r"\end{flushleft}")

        subject_line = blocks.get("subject", "")
        if subject_line:
            output.append(r"\vspace{0.8em}")
            output.append(r"\textbf{" + self._escape_latex(subject_line) + r"}")

        salutation_line = blocks.get("salutation", "")
        if salutation_line:
            output.append(r"\vspace{0.8em}")
            output.append(self._escape_latex(salutation_line))

        body = blocks.get("body", [])
        for paragraph in body:
            output.append(self._escape_latex(paragraph))

        closing_line = blocks.get("closing", "")
        if closing_line:
            output.append(r"\vspace{0.6em}")
            output.append(self._escape_latex(closing_line))

        signature = blocks.get("signature", [])
        if signature:
            output.append(r"\vspace{1.1em}")
            for line in signature:
                output.append(self._escape_latex(line) + r"\\")

        return "\n\n".join(output)

    @staticmethod
    def _escape_latex(text: str) -> str:
        escaped = text
        replacements = {
            "\\": r"\textbackslash{}",
            "&": r"\&",
            "%": r"\%",
            "$": r"\$",
            "#": r"\#",
            "_": r"\_",
            "{": r"\{",
            "}": r"\}",
            "~": r"\textasciitilde{}",
            "^": r"\textasciicircum{}",
        }
        for source, target in replacements.items():
            escaped = escaped.replace(source, target)
        return escaped

    @staticmethod
    def _clean_posting_title(title: str, reference_number: str) -> str:
        cleaned = title.strip()
        cleaned = re.sub(r"^[^A-Za-z0-9]+", "", cleaned)
        if reference_number:
            cleaned = re.sub(
                rf"^Job Posting\s+{re.escape(reference_number)}\s*:\s*",
                "",
                cleaned,
                flags=re.IGNORECASE,
            )
        cleaned = re.sub(r"^Job Posting\s+[A-Za-z0-9\-_/]+\s*:\s*", "", cleaned)
        return cleaned or title.strip()

    @staticmethod
    def _parse_generation_output(raw_response: str) -> dict[str, Any]:
        payload = MotivationLetterService._parse_json_loose(raw_response)
        required = ("subject", "salutation", "letter_markdown")
        missing = [field for field in required if field not in payload]
        if missing:
            raise ValueError(
                "Model output missing required fields: " + ", ".join(missing)
            )

        for field in required:
            if not isinstance(payload[field], str) or not payload[field].strip():
                raise ValueError(
                    f"Model output field must be non-empty string: {field}"
                )
        return payload

    @staticmethod
    def _parse_json_loose(text: str) -> dict[str, Any]:
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = json.loads(MotivationLetterService._extract_json_object(text))

        if not isinstance(payload, dict):
            raise ValueError("Model output must be a JSON object")
        return payload

    @staticmethod
    def _extract_json_object(text: str) -> str:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise ValueError("No JSON object found in model output")
        return text[start : end + 1]
