"""Extract Bridge: Transform scraper output to match_skill input.

This bridge handles the I/O path crossing between:
- Scraper/Translator output: data/source/{source}/{job_id}/
- Match Skill input: output/match_skill/{source}/{job_id}/

It reads the extracted job posting data, maps requirements to RequirementInput
objects, and writes the transformed output to the match_skill artifact directory.
"""

from __future__ import annotations

import json
import logging
import shutil
from pathlib import Path
from typing import TYPE_CHECKING, Any

from src.ai.match_skill.contracts import RequirementInput
from src.shared.log_tags import LogTag

if TYPE_CHECKING:
    from src.core.io import WorkspaceManager

logger = logging.getLogger(__name__)


class ExtractBridgeError(Exception):
    """Raised when the extract bridge fails to transform data."""

    pass


# TODO(future): replace temporary data/source -> output/match_skill path crossing with the canonical workspace contract — see future_docs/issues/pipeline_unification_followups.md
def extract_bridge(
    source: str,
    job_id: str,
    data_root: str | Path = "data/source",
    output_root: str | Path = "output/match_skill",
    workspace: WorkspaceManager | None = None,
) -> list[RequirementInput]:
    """Transform job posting requirements to match_skill RequirementInput format.

    Reads extracted job posting data, maps requirements to RequirementInput
    objects with stable IDs, and writes artifacts to the match_skill directory.

    Args:
        source: Job source identifier (e.g., 'stepstone', 'xing').
        job_id: Unique job posting identifier.
        data_root: Root directory for scraped/translated data.
        output_root: Root directory for match_skill artifacts.
        workspace: Optional WorkspaceManager for I/O operations.

    Returns:
        List of RequirementInput objects derived from job posting requirements.

    Raises:
        ExtractBridgeError: On critical failure during transformation.
    """
    source_path = Path(data_root) / source / job_id
    extracted_en = source_path / "extracted_data_en.json"
    extracted_raw = source_path / "extracted_data.json"

    try:
        if extracted_en.exists():
            data_file = extracted_en
        elif extracted_raw.exists():
            data_file = extracted_raw
        else:
            raise FileNotFoundError(
                f"Neither extracted_data_en.json nor extracted_data.json found "
                f"in {source_path}"
            )

        logger.info(f"{LogTag.FAST} Reading job data from {data_file}")
        raw_data = json.loads(data_file.read_text(encoding="utf-8"))

    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.warning(f"{LogTag.WARN} Extract bridge failed to read data: {e}")
        return _create_error_requirement(str(e))

    try:
        requirements = raw_data.get("requirements", [])
        if not requirements:
            raise ValueError("No requirements field in JobPosting")

    except (ValueError, AttributeError) as e:
        logger.warning(
            f"{LogTag.WARN} Extract bridge failed to extract requirements: {e}"
        )
        return _create_error_requirement(str(e))

    requirement_inputs = [
        RequirementInput(
            id=f"REQ_{i:03d}",
            text=req,
            priority="must",
        )
        for i, req in enumerate(requirements, 1)
    ]

    if workspace is not None:
        _write_output_workspace(
            workspace=workspace,
            source=source,
            job_id=job_id,
            requirements=requirement_inputs,
            raw_data=raw_data,
        )
        _copy_content_workspace(
            workspace=workspace,
            source_path=source_path,
            source=source,
            job_id=job_id,
        )
    else:
        _write_output(
            source=source,
            job_id=job_id,
            requirements=requirement_inputs,
            raw_data=raw_data,
            output_root=output_root,
        )
        _copy_content_file(
            source_path=source_path,
            source=source,
            job_id=job_id,
            output_root=output_root,
        )

    logger.info(
        f"{LogTag.OK} Extracted bridge completed: {len(requirement_inputs)} requirements"
    )
    return requirement_inputs


def _create_error_requirement(error_message: str) -> list[RequirementInput]:
    """Create a dummy requirement so the graph continues to HITL reviewer."""
    return [
        RequirementInput(
            id="REQ_ERROR",
            text=f"[ERROR: {error_message}]",
            priority="must",
        )
    ]


def _write_output(
    source: str,
    job_id: str,
    requirements: list[RequirementInput],
    raw_data: dict[str, Any],
    output_root: str | Path,
) -> None:
    """Write transformed requirements to match_skill artifact directory."""
    output_path = (
        Path(output_root) / source / job_id / "nodes" / "extract_bridge" / "proposed"
    )
    output_path.mkdir(parents=True, exist_ok=True)

    state_payload = {
        "source": source,
        "job_id": job_id,
        "requirements": [req.model_dump() for req in requirements],
        "job_posting": raw_data,
    }

    state_file = output_path / "state.json"
    state_file.write_text(
        json.dumps(state_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.debug(f"{LogTag.FAST} Wrote state to {state_file}")


def _copy_content_file(
    source_path: Path,
    source: str,
    job_id: str,
    output_root: str | Path,
) -> None:
    """Copy content.md to match_skill artifact directory if it exists."""
    content_src = source_path / "content.md"
    if not content_src.exists():
        logger.debug(f"{LogTag.SKIP} No content.md to copy for {source}/{job_id}")
        return

    output_path = (
        Path(output_root) / source / job_id / "nodes" / "extract_bridge" / "proposed"
    )
    output_path.mkdir(parents=True, exist_ok=True)

    content_dst = output_path / "content.md"
    shutil.copy2(content_src, content_dst)
    logger.debug(f"{LogTag.FAST} Copied content.md to {content_dst}")


def _write_output_workspace(
    workspace: WorkspaceManager,
    source: str,
    job_id: str,
    requirements: list[RequirementInput],
    raw_data: dict[str, Any],
) -> None:
    """Write transformed requirements to match_skill artifact directory using workspace."""
    state_payload = {
        "source": source,
        "job_id": job_id,
        "requirements": [req.model_dump() for req in requirements],
        "job_posting": raw_data,
    }

    artifact_path = workspace.node_stage_artifact(
        source=source,
        job_id=job_id,
        node_name="extract_bridge",
        stage="proposed",
        filename="state.json",
    )
    workspace.ensure_parent(artifact_path)
    artifact_path.write_text(
        json.dumps(state_payload, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    logger.debug(f"{LogTag.FAST} Wrote state to {artifact_path}")


def _copy_content_workspace(
    workspace: WorkspaceManager,
    source_path: Path,
    source: str,
    job_id: str,
) -> None:
    """Copy content.md to match_skill artifact directory if it exists using workspace."""
    content_src = source_path / "content.md"
    if not content_src.exists():
        logger.debug(f"{LogTag.SKIP} No content.md to copy for {source}/{job_id}")
        return

    artifact_path = workspace.node_stage_artifact(
        source=source,
        job_id=job_id,
        node_name="extract_bridge",
        stage="proposed",
        filename="content.md",
    )
    workspace.ensure_parent(artifact_path)
    shutil.copy2(content_src, artifact_path)
    logger.debug(f"{LogTag.FAST} Copied content.md to {artifact_path}")
