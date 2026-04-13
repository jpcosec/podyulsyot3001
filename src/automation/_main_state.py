"""CLI state building helpers."""

import os
import uuid
from typing import Optional

from src.automation.contracts import CandidateProfile
from src.automation.ariadne.models import AriadneMap, AriadneState


def get_entry_state(ariadne_map: AriadneMap, preferred: str) -> str:
    """Resolve the entry state from map states."""
    return (
        preferred if preferred in ariadne_map.states else next(iter(ariadne_map.states))
    )


def base_state(
    portal_name: str,
    mission_id: str,
    entry_state: str,
    portal_mode: str,
    profile_data: dict,
    job_data: dict,
    session_memory: dict,
) -> dict:
    """Build base state structure shared by apply and scrape."""
    return {
        "portal_name": portal_name,
        "current_mission_id": mission_id,
        "current_state_id": entry_state,
        "profile_data": profile_data,
        "job_data": job_data,
        "path_id": str(uuid.uuid4()),
        "dom_elements": [],
        "current_url": "",
        "screenshot_b64": None,
        "session_memory": session_memory,
        "errors": [],
        "history": [],
        "portal_mode": portal_mode,
        "patched_components": {},
    }


def apply_job_data(job_id: str, cv_path: str, dry_run: bool) -> dict:
    """Build job data for apply flow."""
    return {
        "job_id": job_id,
        "cv_path": os.path.abspath(cv_path),
        "dry_run": dry_run,
    }


def scrape_job_data(limit: int) -> dict:
    """Build job data for scrape flow."""
    return {"limit": limit}


def scrape_session_memory(limit: int) -> dict:
    """Build session memory for scrape flow."""
    return {"limit": limit}


def build_apply_state(
    source: str,
    job_id: str,
    cv_path: str,
    profile: CandidateProfile,
    ariadne_map: AriadneMap,
    dry_run: bool,
    portal_mode: str,
    mission_id: Optional[str],
) -> AriadneState:
    """Construct the initial state for an apply run."""
    entry_state = get_entry_state(ariadne_map, "job_details")
    state = base_state(
        portal_name=source,
        mission_id=mission_id or portal_mode,
        entry_state=entry_state,
        portal_mode=portal_mode,
        profile_data=profile.model_dump(),
        job_data=apply_job_data(job_id, cv_path, dry_run),
        session_memory={},
    )
    state["job_id"] = job_id
    return state


def build_scrape_state(
    source: str,
    limit: int,
    ariadne_map: AriadneMap,
    portal_mode: str,
    mission_id: str,
) -> AriadneState:
    """Construct the initial state for a scrape run."""
    entry_state = get_entry_state(ariadne_map, "search_results")
    state = base_state(
        portal_name=source,
        mission_id=mission_id,
        entry_state=entry_state,
        portal_mode=portal_mode,
        profile_data={},
        job_data=scrape_job_data(limit),
        session_memory=scrape_session_memory(limit),
    )
    state["job_id"] = f"discovery-{source}-{uuid.uuid4().hex[:8]}"
    return state
