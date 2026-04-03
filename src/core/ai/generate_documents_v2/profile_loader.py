"""Load P1 (ProfileKG) and P2 (SectionMapping) from disk."""

from __future__ import annotations

import json
from pathlib import Path

from src.core.data_manager import DataManager
from src.core.ai.generate_documents_v2.contracts.profile import (
    ProfileEntry,
    ProfileKG,
    SectionMappingItem,
)

# TODO(future): module-level singleton locks path at import time — see future_docs/issues/core/ai/generate_documents_v2/profile_loader_singleton.md
_DATA_MANAGER = DataManager()


def load_profile_kg(profile_path: str | Path) -> ProfileKG:
    """Build a ProfileKG from a ProfileBaseData JSON file."""

    path = Path(profile_path)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {path}")

    raw = _DATA_MANAGER.read_json_path(path)
    return build_profile_kg(raw, path.parent / "profile_patches.json")


def build_profile_kg(
    raw_data: dict[str, Any], patch_path: Path | None = None
) -> ProfileKG:
    """Build a ProfileKG from raw ProfileBaseData dictionary."""
    entries = _build_entries(raw_data.get("experience", []))
    entries.extend(_build_education_entries(raw_data.get("education", [])))

    skills = _flatten_skills(raw_data.get("skills", {}))
    traits = _extract_traits(raw_data.get("cv_generation_context", {}))
    profile = ProfileKG(entries=entries, skills=skills, traits=traits)

    if patch_path and patch_path.exists():
        return _apply_profile_patches(profile, patch_path)
    return profile


def load_section_mapping(mapping_path: str | Path) -> list[SectionMappingItem]:
    """Load section mapping rules from JSON or return an empty list."""

    path = Path(mapping_path)
    if not path.exists():
        return []

    raw: list[dict] = _DATA_MANAGER.read_json_path(path)
    items = [SectionMappingItem.model_validate(item) for item in raw]
    return _apply_section_mapping_patches(
        items, path.parent / "section_mapping_patches.json"
    )


def _build_entries(experience: list[dict]) -> list[ProfileEntry]:
    entries: list[ProfileEntry] = []
    for index, item in enumerate(experience, start=1):
        entries.append(
            ProfileEntry(
                id=item.get("id") or f"EXP{index:03d}",
                role=item.get("role", ""),
                organization=item.get("organization", ""),
                achievements=item.get("achievements", []),
                keywords=item.get("keywords", []),
                start_date=item.get("start_date"),
                end_date=item.get("end_date"),
            )
        )
    return entries


def _build_education_entries(education: list[dict]) -> list[ProfileEntry]:
    entries: list[ProfileEntry] = []
    for index, item in enumerate(education, start=1):
        role = item.get("degree", "")
        spec = item.get("specialization")
        if spec:
            role = f"{role} ({spec})"

        achievements = []
        if item.get("equivalency_note"):
            achievements.append(item["equivalency_note"])
        if item.get("grade"):
            achievements.append(f"Grade: {item['grade']}")

        entries.append(
            ProfileEntry(
                id=item.get("id") or f"EDU{index:03d}",
                role=role,
                organization=item.get("institution", ""),
                achievements=achievements,
                keywords=[],
                start_date=item.get("start_date"),
                end_date=item.get("end_date"),
            )
        )
    return entries


def _flatten_skills(skills_dict: dict) -> list[str]:
    flat: list[str] = []
    for skill_list in skills_dict.values():
        if isinstance(skill_list, list):
            flat.extend(str(skill) for skill in skill_list if skill)
    return flat


def _extract_traits(context: dict) -> list[str]:
    traits = context.get("traits", [])
    if isinstance(traits, list):
        return [str(trait) for trait in traits if trait]
    return []


def _apply_profile_patches(profile: ProfileKG, patch_path: Path) -> ProfileKG:
    if not patch_path.exists():
        return profile
    patches = _DATA_MANAGER.read_json_path(patch_path)
    skills = list(profile.skills)
    traits = list(profile.traits)
    entries = list(profile.entries)
    for patch in patches:
        target_type = patch.get("target_type")
        value = patch.get("new_value")
        if target_type == "skill" and isinstance(value, str) and value not in skills:
            skills.append(value)
        elif target_type == "trait" and isinstance(value, str) and value not in traits:
            traits.append(value)
        elif target_type == "entry" and isinstance(value, dict):
            entries.append(ProfileEntry.model_validate(value))
    return ProfileKG(
        entries=entries,
        skills=skills,
        traits=traits,
        evidence_edges=profile.evidence_edges,
    )


def _apply_section_mapping_patches(
    items: list[SectionMappingItem],
    patch_path: Path,
) -> list[SectionMappingItem]:
    if not patch_path.exists():
        return items
    patches = _DATA_MANAGER.read_json_path(patch_path)
    by_id = {item.section_id: item for item in items}
    for patch in patches:
        target_id = patch.get("target_id")
        value = patch.get("new_value")
        action = patch.get("action")
        if target_id not in by_id:
            continue
        current = by_id[target_id].model_dump()
        if action == "move_to_doc" and isinstance(value, str):
            current["target_document"] = value
        elif isinstance(value, dict):
            current.update(value)
        by_id[target_id] = SectionMappingItem.model_validate(current)
    return list(by_id.values())
