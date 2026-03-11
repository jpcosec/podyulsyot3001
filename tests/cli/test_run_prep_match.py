"""Tests for prep-match CLI helper."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.cli.run_prep_match import _load_profile_evidence


def test_load_profile_evidence_requires_path() -> None:
    with pytest.raises(ValueError, match="profile-evidence"):
        _load_profile_evidence(None)


def test_load_profile_evidence_reads_list_of_dicts(tmp_path: Path) -> None:
    p = tmp_path / "profile.json"
    p.write_text(
        json.dumps([{"id": "P1", "description": "Python"}, "skip", {"id": "P2"}]),
        encoding="utf-8",
    )
    out = _load_profile_evidence(str(p))
    assert out == [{"id": "P1", "description": "Python"}, {"id": "P2"}]


def test_load_profile_evidence_reads_profile_base_shape(tmp_path: Path) -> None:
    p = tmp_path / "profile_base_data.json"
    p.write_text(
        json.dumps(
            {
                "cv_generation_context": {
                    "professional_summary_seed": "Applied AI engineer",
                    "tagline_seed": "AI profile",
                },
                "education": [
                    {
                        "degree": "Electrical Engineering",
                        "specialization": "Computational Intelligence",
                        "institution": "UChile",
                    }
                ],
                "experience": [
                    {
                        "role": "ML Engineer",
                        "organization": "Kwali",
                        "achievements": ["Built CV pipelines"],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    out = _load_profile_evidence(str(p))

    assert len(out) >= 2
    assert all("id" in item and "description" in item for item in out)
    assert all(not item["id"].startswith("P_SUM") for item in out)
