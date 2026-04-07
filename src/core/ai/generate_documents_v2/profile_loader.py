"""Load P1 (ProfileKG) and P2 (SectionMapping) from disk."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.core.ai.generate_documents_v2.contracts.profile import (
    ProfileEntry,
    ProfileKG,
    SectionMappingItem,
)

if TYPE_CHECKING:
    from src.core.ai.generate_documents_v2.strategies import DocumentStrategy


def load_profile_kg(profile_path: str | Path) -> ProfileKG:
    """Build a ProfileKG from a ProfileBaseData JSON file.

    Stable path-based entry point.  When a ``profile_patches.json`` file is
    present beside the profile, patches are applied automatically.

    Prefer injecting ``profile_evidence`` into the graph state directly
    (bypassing this function) when the raw profile dict is already in memory.
    """
    path = Path(profile_path)
    if not path.exists():
        raise FileNotFoundError(f"Profile not found: {path}")

    raw = json.loads(path.read_text(encoding="utf-8"))
    return build_profile_kg(raw, path.parent / "profile_patches.json")


def build_profile_kg(
    raw_data: dict[str, Any], patch_path: Path | None = None
) -> ProfileKG:
    """Build a ProfileKG from a raw ProfileBaseData dictionary.

    Stable injection entry point.  Called by ``load_profile_kg`` and also
    directly by the ``load_profile_mapping`` graph node when ``profile_evidence``
    is injected into initial state.  Extend this function when the profile JSON
    schema gains new top-level keys that should populate ``ProfileKG``.
    """
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

    raw: list[dict] = json.loads(path.read_text(encoding="utf-8"))
    items = [SectionMappingItem.model_validate(item) for item in raw]
    return _apply_section_mapping_patches(
        items, path.parent / "section_mapping_patches.json"
    )


def filter_sections_by_strategy(
    items: list[SectionMappingItem],
    strategy: "DocumentStrategy",
) -> list[SectionMappingItem]:
    """Filter and reorder section mapping items by the chosen strategy.

    Keeps only items whose ``country_context`` is ``"global"`` (universal) or
    matches the strategy name.  Items that appear in ``strategy.section_order``
    are placed first in that order; any remaining items follow in their
    original relative order.

    Args:
        items: Full list of section mapping items loaded from disk.
        strategy: Resolved document strategy.

    Returns:
        Filtered and reordered list of section mapping items.
    """
    relevant = [
        item for item in items
        if item.country_context in ("global", strategy.name)
    ]
    order_index = {name: idx for idx, name in enumerate(strategy.section_order)}
    not_ordered = [i for i in relevant if i.section_id not in order_index]
    ordered = sorted(
        (i for i in relevant if i.section_id in order_index),
        key=lambda i: order_index[i.section_id],
    )
    return ordered + not_ordered


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
    patches = json.loads(patch_path.read_text(encoding="utf-8"))
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
    patches = json.loads(patch_path.read_text(encoding="utf-8"))
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
