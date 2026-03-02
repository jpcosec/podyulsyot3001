import pytest

try:
    import spacy
    HAS_SPACY = True
except ImportError:
    HAS_SPACY = False

from src.utils.ats import run_ats_analysis

CV_TEXT = """
PROFESSIONAL SUMMARY
Machine Learning Engineer with Python, Airflow, and MLOps experience.

WORK EXPERIENCE
AraraDS - ML Consultant  2025-07 - 2025-09
- Built Airflow DAGs for production orchestration
- Applied MLOps: versioning, deployment, monitoring

EDUCATION
Electrical Engineering - Universidad de Chile  2011-2019

TECHNICAL SKILLS
Python, PyTorch, Airflow, Docker

Contact: test@example.com | +49 123 456
"""

JD_TEXT = "Python MLOps Airflow workflow orchestration machine learning research"


def test_run_ats_analysis_returns_valid_schema():
    result = run_ats_analysis(cv_text=CV_TEXT, job_description=JD_TEXT)
    for key in ("id", "success", "score", "engines", "weights"):
        assert key in result, f"Missing key: {key}"


@pytest.mark.skipif(not HAS_SPACY, reason="spacy not installed")
def test_code_engine_not_fallback():
    result = run_ats_analysis(cv_text=CV_TEXT, job_description=JD_TEXT)
    code = result["engines"]["code"]
    assert code["available"] is True
    assert code.get("used_fallback") is False, f"spaCy engine should not fall back, got: {code}"


def test_score_in_range():
    result = run_ats_analysis(cv_text=CV_TEXT, job_description=JD_TEXT)
    assert 0 <= result["score"] <= 100
