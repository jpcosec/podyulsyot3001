from __future__ import annotations

import json

import pytest

from src.core.ai.generate_documents_v2.contracts.profile import (
    ProfileKG,
    SectionMappingItem,
)
from src.core.ai.generate_documents_v2.profile_loader import (
    load_profile_kg,
    load_section_mapping,
)

DEFAULT_PROFILE_PATH = "data/reference_data/profile/base_profile/profile_base_data.json"

SAMPLE_PROFILE = {
    "owner": {
        "full_name": "Juan Perez",
        "email": "juan@example.com",
        "phone": "+49 123 456",
    },
    "experience": [
        {
            "role": "Data Engineer",
            "organization": "ACME GmbH",
            "start_date": "2022-01",
            "end_date": "2024-12",
            "achievements": ["Built Kafka pipeline", "Reduced latency 40%"],
            "keywords": ["Kafka", "Python", "AWS"],
        }
    ],
    "skills": {
        "programming_languages": ["Python", "Rust"],
        "ml_ai": ["PyTorch"],
    },
    "cv_generation_context": {
        "tagline_seed": "Data engineering and Rust systems",
        "traits": ["railway-enthusiast", "curious"],
    },
}

SAMPLE_SECTION_MAPPING = [
    {
        "section_id": "summary",
        "target_document": "cv",
        "mandatory": True,
        "default_priority": 5,
    },
    {
        "section_id": "experience",
        "target_document": "cv",
        "mandatory": True,
        "default_priority": 4,
        "country_context": "global",
    },
]


def test_load_profile_kg_produces_entries(tmp_path):
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(SAMPLE_PROFILE), encoding="utf-8")
    kg = load_profile_kg(profile_path)
    assert isinstance(kg, ProfileKG)
    assert len(kg.entries) == 1
    assert kg.entries[0].id == "EXP001"
    assert kg.entries[0].role == "Data Engineer"
    assert kg.entries[0].organization == "ACME GmbH"


def test_load_profile_kg_flattens_skills(tmp_path):
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(SAMPLE_PROFILE), encoding="utf-8")
    kg = load_profile_kg(profile_path)
    assert "Python" in kg.skills
    assert "Rust" in kg.skills
    assert "PyTorch" in kg.skills


def test_load_profile_kg_extracts_traits(tmp_path):
    profile_path = tmp_path / "profile.json"
    profile_path.write_text(json.dumps(SAMPLE_PROFILE), encoding="utf-8")
    kg = load_profile_kg(profile_path)
    assert "railway-enthusiast" in kg.traits


def test_load_profile_kg_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_profile_kg(tmp_path / "nonexistent.json")


def test_load_profile_kg_checked_in_default_profile_exists():
    kg = load_profile_kg(DEFAULT_PROFILE_PATH)
    assert isinstance(kg, ProfileKG)
    assert len(kg.entries) >= 1
    assert "Python" in kg.skills


def test_load_section_mapping_returns_items(tmp_path):
    mapping_path = tmp_path / "section_mapping.json"
    mapping_path.write_text(json.dumps(SAMPLE_SECTION_MAPPING), encoding="utf-8")
    items = load_section_mapping(mapping_path)
    assert len(items) == 2
    assert isinstance(items[0], SectionMappingItem)
    assert items[0].section_id == "summary"


def test_load_section_mapping_missing_file_returns_empty(tmp_path):
    items = load_section_mapping(tmp_path / "missing.json")
    assert items == []
