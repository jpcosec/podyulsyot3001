import json
import pytest
from pathlib import Path
from src.utils.model import CVModel

FIXTURE = Path("tests/cv_generator/fixtures/sample_profile.json")


@pytest.fixture
def profile():
    return json.loads(FIXTURE.read_text())


def test_from_profile_full_name(profile):
    model = CVModel.from_profile(profile)
    assert model.full_name == "Juan Pablo Andres Ruiz Rodriguez"


def test_from_profile_tagline(profile):
    model = CVModel.from_profile(profile)
    assert model.tagline != ""


def test_from_profile_contact_email(profile):
    model = CVModel.from_profile(profile)
    assert "@" in model.contact.email


def test_from_profile_education_not_empty(profile):
    model = CVModel.from_profile(profile)
    assert len(model.education) > 0


def test_from_profile_experience_not_empty(profile):
    model = CVModel.from_profile(profile)
    assert len(model.experience) > 0


def test_from_profile_skills_dict(profile):
    model = CVModel.from_profile(profile)
    assert isinstance(model.skills, dict)
    assert len(model.skills) > 0
