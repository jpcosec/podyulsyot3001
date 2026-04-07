"""Tests for automation storage helpers."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.automation.contracts import CandidateProfile
from src.automation.storage import AutomationStorage


def test_load_candidate_profile_returns_empty_model_by_default() -> None:
    storage = AutomationStorage.__new__(AutomationStorage)

    profile = storage.load_candidate_profile()

    assert profile == CandidateProfile()


def test_load_candidate_profile_validates_and_preserves_extra_fields() -> None:
    storage = AutomationStorage.__new__(AutomationStorage)

    profile = storage.load_candidate_profile(
        {
            "first_name": "Ada",
            "email": "ada@example.com",
            "work_authorization": "EU",
        }
    )

    assert profile.first_name == "Ada"
    assert profile.email == "ada@example.com"
    assert profile.model_dump()["work_authorization"] == "EU"


def test_load_candidate_profile_rejects_invalid_payloads() -> None:
    storage = AutomationStorage.__new__(AutomationStorage)

    with pytest.raises(ValidationError):
        storage.load_candidate_profile({"first_name": ["Ada"]})
