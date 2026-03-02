import pytest

try:
    from src.utils.nlp.text_analyzer import TextAnalyzer
except ImportError as e:
    pytestmark = pytest.mark.skip(reason=f"spacy not installed: {e}")

SAMPLE_CV = """
PROFESSIONAL SUMMARY
Machine Learning Engineer with experience in Python, Airflow, and MLOps.

WORK EXPERIENCE
AraraDS - Machine Learning Consultant   2025-07 - 2025-09
- Built and deployed Python-based data pipelines with Apache Airflow
- Applied MLOps practices including model versioning and monitoring

EDUCATION
Electrical Engineering (Computational Intelligence)
Universidad de Chile, Santiago, Chile   2011 - 2019

TECHNICAL SKILLS
Python, PyTorch, Airflow, Docker, Azure

Contact: juanpablo.ruiz.r@gmail.com | +49 15222144630
"""

SAMPLE_JD = "Python MLOps Airflow workflow orchestration machine learning"


def test_analyzer_initializes():
    analyzer = TextAnalyzer()
    assert analyzer.lang == "en"


def test_unsupported_language_raises():
    with pytest.raises(ValueError, match="Unsupported language"):
        TextAnalyzer(lang="zh")


def test_analyze_returns_required_keys():
    analyzer = TextAnalyzer()
    result = analyzer.analyze(SAMPLE_CV, SAMPLE_JD)
    for key in ("score", "score_breakdown", "skills_comparison", "recommendations", "identified_sections"):
        assert key in result, f"Missing key: {key}"


def test_score_in_range():
    analyzer = TextAnalyzer()
    result = analyzer.analyze(SAMPLE_CV, SAMPLE_JD)
    assert 0 <= result["score"] <= 100


def test_identifies_experience_section():
    analyzer = TextAnalyzer()
    result = analyzer.analyze(SAMPLE_CV)
    assert any("experience" in s.lower() for s in result["identified_sections"])


def test_keyword_match_finds_python():
    analyzer = TextAnalyzer()
    result = analyzer.analyze(SAMPLE_CV, SAMPLE_JD)
    matching = [k.lower() for k in result["skills_comparison"]["matching_keywords"]]
    assert "python" in matching
