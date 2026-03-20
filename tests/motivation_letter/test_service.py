import json
from pathlib import Path
from unittest.mock import patch

from src.utils.config import CVConfig
from src.steps.motivation_service import MotivationLetterService


class FakeGemini:
    def __init__(self, payload: dict):
        self._payload = payload

    def generate(self, _: str) -> str:
        return json.dumps(self._payload)


def _build_minimal_profile() -> dict:
    return {
        "owner": {
            "full_name": "Jane Doe",
            "tagline": "Research Assistant Candidate",
            "professional_summary": "Applied ML and data engineering background.",
            "contact": {
                "email": "jane@example.com",
                "phone": "+49 123 456",
                "addresses": [{"label": "current", "value": "Berlin, Germany"}],
            },
            "links": {
                "linkedin": "https://linkedin.example/jane",
                "github": "https://github.com/jane",
            },
            "legal_status": {
                "visa_type": "Chancenkarte",
                "work_permission_germany": True,
            },
        },
        "education": [
            {
                "degree": "Electrical Engineering",
                "specialization": "Computational Intelligence",
                "institution": "Universidad de Chile",
                "location": "Santiago, Chile",
                "start_date": "2011-03",
                "end_date": "2019-06",
                "equivalency_note": "Validated by Anabin/ZAB as equivalent to a German Master's/Diplom.",
            }
        ],
        "experience": [
            {
                "role": "Machine Learning Consultant",
                "organization": "AraraDS",
                "location": "Santiago, Chile",
                "start_date": "2025-07",
                "end_date": "2025-09",
                "achievements": [
                    "Built Airflow-based production orchestration pipelines.",
                    "Applied model versioning and monitoring practices.",
                ],
            }
        ],
        "publications": [{"year": 2025, "title": "Paper", "venue": "NeurIPS Workshop"}],
        "languages": [{"name": "English", "level": "CEFR C1"}],
        "skills": {"programming_languages": ["Python"], "ml_ai": ["PyTorch"]},
    }


def _write_job_markdown(job_path: Path) -> None:
    job_path.write_text(
        "\n".join(
            [
                "---",
                "reference_number: III-51/26",
                "university: TU Berlin",
                "deadline: 20.03.2026",
                "contact_email: test@tu-berlin.de",
                "url: https://example.test/job",
                "---",
                "",
                "# Job Posting III-51/26: Research Assistant",
                "",
                "## Their Requirements (Profile)",
                "- [ ] Strong Python programming skills",
                "- [ ] Experience with workflow orchestration (e.g., Airflow)",
                "",
                "## Area of Responsibility (Tasks)",
                "- [ ] Build FAIR-compliant pipelines",
                "",
                "## How I Match (Auto-detected)",
                "- I have practical Airflow production experience.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _build_service(tmp_path: Path, generator=None) -> MotivationLetterService:
    project_root = tmp_path
    profile_root = project_root / "data" / "reference_data" / "profile" / "base_profile"
    pipeline_root = project_root / "data" / "pipelined_data"

    profile_root.mkdir(parents=True, exist_ok=True)
    pipeline_root.mkdir(parents=True, exist_ok=True)

    profile_path = profile_root / "profile_base_data.json"
    profile_path.write_text(
        json.dumps(_build_minimal_profile(), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    job_dir = pipeline_root / "tu_berlin" / "999999"
    job_dir.mkdir(parents=True, exist_ok=True)
    _write_job_markdown(job_dir / "job.md")

    planning_dir = job_dir / "planning"
    planning_dir.mkdir(parents=True, exist_ok=True)
    (planning_dir / "motivation_letter copy.md").write_text(
        "\n".join(
            [
                "[Berlin, Date]",
                "",
                "Dr. Example",
                "Faculty/Dean's Office",
                "TU Berlin",
                "",
                "Subject: Application for Job Posting III-51/26 - Research Assistant",
                "",
                "Dear Dr. Example,",
                "",
                "I am applying for the role and align with FAIR and workflow goals.",
                "",
                "My degree is Anabin/ZAB equivalent and I comply with the mobility rule.",
                "",
                "I built Python and Airflow pipelines and applied MLOps in production.",
                "",
                "I am motivated by interdisciplinary research and doctoral trajectory.",
                "",
                "Thank you for your consideration. Supporting documents are attached.",
                "",
                "Sincerely,",
                "Jane Doe",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    config = CVConfig(
        project_root=project_root,
        profile_root=profile_root,
        pipeline_root=pipeline_root,
    )
    return MotivationLetterService(
        config=config,
        generator=generator,
    )


def test_build_context_extracts_job_requirements(tmp_path):
    service = _build_service(tmp_path)
    context = service.build_context(job_id="999999", source="tu_berlin")

    assert context["job"]["reference_number"] == "III-51/26"
    assert len(context["job"]["requirements"]) == 2
    assert "Strong Python programming skills" in context["job"]["requirements"][0]
    assert context["candidate"]["name"] == "Jane Doe"
    assert len(context["candidate"]["evidence_catalog"]) > 0
    assert len(context["analysis"]["requirement_coverage"]) == 2
    assert "format_insights" in context["analysis"]
    assert "strengths" in context["analysis"]["format_insights"]



def test_generate_for_job_writes_letter_and_analysis(tmp_path):
    def fake_generator(_: str) -> str:
        return json.dumps(
            {
                "subject": "Application for III-51/26",
                "salutation": "Dear Hiring Committee,",
                "fit_signals": [],
                "risk_notes": [],
                "letter_markdown": "[Berlin, Date]\n\nDear Hiring Committee,\n\nI am applying for the role.\n\nSincerely,\nJane Doe",
            }
        )

    service = _build_service(tmp_path, generator=fake_generator)
    result = service.generate_for_job(job_id="999999", source="tu_berlin")

    assert result.letter_path.exists()
    assert result.analysis_path.exists()
    assert "I am applying for the role." in result.letter_path.read_text(
        encoding="utf-8"
    )

    analysis = json.loads(result.analysis_path.read_text(encoding="utf-8"))
    assert analysis["subject"] == "Application for III-51/26"
    assert analysis["salutation"] == "Dear Hiring Committee,"


def test_generate_email_draft_writes_email_file(tmp_path):
    service = _build_service(tmp_path)
    service.gemini = FakeGemini(
        {
            "to": "test@tu-berlin.de",
            "subject": "Application for Job Posting III-51/26",
            "salutation": "Dear Hiring Committee,",
            "body": "I am applying for the role and have attached my motivation letter and CV.",
            "closing": "Best regards,",
            "sender_name": "Jane Doe",
            "sender_email": "jane@example.com",
            "sender_phone": "+49 123 456",
        }
    )
    result = service.generate_email_draft(job_id="999999", source="tu_berlin")

    assert result.email_path.exists()
    content = result.email_path.read_text(encoding="utf-8")
    assert content.startswith("To:")
    assert "Subject: Application for Job Posting III-51/26" in content
    assert "Dear Hiring Committee," in content


def test_build_pdf_for_job_writes_output_pdf(tmp_path):
    service = _build_service(tmp_path)
    planning_dir = service.config.pipeline_root / "tu_berlin" / "999999" / "planning"
    letter_path = planning_dir / "motivation_letter.md"
    letter_path.write_text(
        "[Berlin, Date]\n\nDear Hiring Committee,\n\nTest letter.\n\nSincerely,\nJane Doe\n",
        encoding="utf-8",
    )

    def fake_run(*_, **kwargs):
        cwd = Path(kwargs["cwd"])
        (cwd / "motivation_letter.pdf").write_bytes(b"%PDF-1.4\n%fake\n")

        class Result:
            returncode = 0
            stdout = ""
            stderr = ""

        return Result()

    with patch("src.steps.motivation_service.which", return_value="/usr/bin/pdflatex"):
        with patch(
            "src.steps.motivation_service.subprocess.run", side_effect=fake_run
        ):
            pdf_result = service.build_pdf_for_job(job_id="999999", source="tu_berlin")

    assert pdf_result.pdf_path.exists()
    assert pdf_result.pdf_path.suffix == ".pdf"
