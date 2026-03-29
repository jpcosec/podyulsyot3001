"""Pipeline profile loading node adapters for schema-v0."""

from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Mapping

from src.core.data_manager import DataManager
from src.core.profile import ProfileBaseData
from src.core.state import GraphState
from src.shared.log_tags import LogTag

logger = logging.getLogger(__name__)


class ProfileNotFoundError(Exception):
    """Raised when the master profile cannot be located on disk."""
    pass


def make_load_profile_node(data_manager: DataManager):
    """Create the profile loading node that resolves and normalizes user evidence."""

    async def load_profile_node(state: GraphState) -> dict:
        source = state["source"]
        job_id = state.get("job_id")
        if not job_id:
            logger.error(f"{LogTag.FAIL} Load profile node failed: job_id missing in state")
            return {
                "current_node": "load_profile",
                "status": "failed",
                "error_state": {
                    "node": "load_profile",
                    "message": "job_id missing in state",
                    "details": None,
                },
            }

        try:
            # 1. Resolve master profile source
            default_path = "data/reference_data/profile/base_profile/profile_base_data.json"
            master_path = Path(os.getenv("PROFILE_MASTER_PATH", default_path))
            
            if not master_path.exists():
                raise ProfileNotFoundError(f"Master profile not found at: {master_path}")

            logger.info(f"{LogTag.OK} Loading master profile: {master_path}")
            raw_master = json.loads(master_path.read_text(encoding="utf-8"))
            
            # 2. Schema Validation (Hardening)
            try:
                profile_data = ProfileBaseData.model_validate(raw_master)
            except Exception as e:
                logger.error(f"{LogTag.FAIL} Master profile schema validation failed: {e}")
                raise ValueError(f"Invalid master profile schema: {e}")

            # 3. Dynamic Transformation (Legacy 'dev' Logic Ported)
            evidence = _transform_profile_to_evidence(profile_data)
            
            # 4. Side-load Global Patches (Persisted Human Review results)
            patches_path = master_path.parent / "profile_patches.json"
            if patches_path.exists():
                logger.info(f"{LogTag.OK} Loading global profile patches: {patches_path}")
                try:
                    global_patches = json.loads(patches_path.read_text(encoding="utf-8"))
                    evidence = _merge_patches(evidence, global_patches)
                except Exception as e:
                    logger.warning(f"{LogTag.WARN} Failed to load profile patches: {e}")

            # 5. Compute Hash for Traceability
            profile_hash = hashlib.sha256(master_path.read_bytes()).hexdigest()
            metadata = {
                "source_profile_path": str(master_path),
                "source_profile_hash": f"sha256:{profile_hash}",
                "evidence_count": len(evidence)
            }

            # 6. Persist normalized artifact for the job
            ref_path = data_manager.write_json_artifact(
                source=source,
                job_id=job_id,
                node_name="pipeline_inputs",
                stage="proposed",
                filename="profile_evidence.json",
                data={
                    "metadata": metadata,
                    "evidence": evidence
                },
            )

            logger.info(
                f"{LogTag.OK} Persisted {len(evidence)} evidence items with hash {profile_hash[:8]}..."
            )
            return {
                "profile_evidence": evidence,
                "profile_evidence_ref": str(ref_path),
                "current_node": "load_profile",
                "status": "running",
            }

        except ProfileNotFoundError as exc:
            logger.error(f"{LogTag.FAIL} Profile Error: {exc}")
            return {
                "current_node": "load_profile",
                "status": "failed",
                "error_state": {
                    "node": "load_profile",
                    "message": str(exc),
                    "details": {"help": "Check PROFILE_MASTER_PATH env var"},
                },
            }
        except Exception as exc:
            logger.error(f"{LogTag.FAIL} Load profile node failed: {exc}")
            return {
                "current_node": "load_profile",
                "status": "failed",
                "error_state": {
                    "node": "load_profile",
                    "message": str(exc),
                    "details": None,
                },
            }

    return load_profile_node


def _transform_profile_to_evidence(profile: ProfileBaseData) -> List[Dict[str, str]]:
    """Convert a master profile into a flat list of evidence items for the LLM."""
    out: List[Dict[str, str]] = []

    def add(description: str, prefix: str) -> None:
        text = " ".join(description.split()).strip()
        if not text:
            return
        out.append({"id": f"{prefix}_{len(out) + 1:03d}", "description": text})

    # Summary and Tagline
    if profile.owner.professional_summary:
        add(profile.owner.professional_summary, "P_SUM")
    if profile.owner.tagline:
        add(profile.owner.tagline, "P_TAG")

    # Education
    for edu in profile.education:
        text = f"Degree: {edu.degree} ({edu.specialization or 'N/A'}) at {edu.institution}."
        if edu.equivalency_note:
            text += f" {edu.equivalency_note}"
        add(text, "P_EDU")

    # Experience
    for exp in profile.experience:
        header = f"Role: {exp.role} at {exp.organization} ({exp.start_date} to {exp.end_date or 'Present'})."
        if exp.achievements:
            for ach in exp.achievements:
                add(f"{header} Achievement: {ach}", "P_EXP")
        else:
            add(header, "P_EXP")

    # Projects
    for prj in profile.projects:
        stack = ", ".join(prj.stack) if prj.stack else "N/A"
        add(f"Project: {prj.name} ({prj.role or 'Contributor'}). Tech Stack: {stack}.", "P_PRJ")

    # Skills
    for category, values in profile.skills.items():
        if values:
            add(f"Skill Category ({category}): {', '.join(values)}.", "P_SKL")

    # Languages
    if profile.languages:
        langs = [f"{l.name} ({l.level})" for l in profile.languages]
        add(f"Languages: {', '.join(langs)}.", "P_LNG")

    return out


def _merge_patches(base: List[Dict[str, str]], patches: Any) -> List[Dict[str, str]]:
    """Safe merge of persistent human-provided patches into the evidence set."""
    if not isinstance(patches, list):
        return base
        
    merged = list(base)
    seen_ids = {item["id"] for item in base}
    
    for patch in patches:
        if not isinstance(patch, dict):
            continue
        pid = patch.get("id")
        desc = patch.get("description")
        if pid and desc and pid not in seen_ids:
            merged.append({"id": pid, "description": desc})
            seen_ids.add(pid)
            
    return merged
