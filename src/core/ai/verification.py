from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.core.ai.tracing import trace_section


@dataclass(frozen=True)
class VerificationCheck:
    name: str
    passed: bool
    detail: str
    weight: float = 1.0


def evaluate_prep_match_run(
    initial_state: Mapping[str, Any],
    output_state: Mapping[str, Any],
) -> dict[str, Any]:
    source = str(initial_state.get("source", "")).strip()
    job_id = str(initial_state.get("job_id", "")).strip()

    with trace_section(
        "quality_eval.prep_match",
        metadata={"source": source, "job_id": job_id},
    ):
        checks = _build_checks(output_state)

    total_weight = sum(item.weight for item in checks) or 1.0
    score = sum(item.weight for item in checks if item.passed) / total_weight
    payload = {
        "verifier": "prep_match_v1",
        "passed": all(item.passed for item in checks),
        "score": round(score, 4),
        "checks": [
            {
                "name": item.name,
                "passed": item.passed,
                "detail": item.detail,
                "weight": item.weight,
            }
            for item in checks
        ],
    }
    return payload


def verification_artifact_path(source: str, job_id: str) -> Path:
    return Path("data/jobs") / source / job_id / "graph" / "langsmith_verification.json"


def _build_checks(output_state: Mapping[str, Any]) -> list[VerificationCheck]:
    status = str(output_state.get("status", ""))
    current_node = str(output_state.get("current_node", ""))
    error_state = output_state.get("error_state")

    expected_node_by_status = {
        "pending_review": "review_match",
        "completed": "package",
    }
    expected_node = expected_node_by_status.get(status)
    routing_ok = expected_node is not None and current_node == expected_node

    checks = [
        VerificationCheck(
            name="status_allowed",
            passed=status in expected_node_by_status,
            detail=(
                "status is pending_review or completed"
                if status in expected_node_by_status
                else f"unexpected status: {status!r}"
            ),
            weight=1.0,
        ),
        VerificationCheck(
            name="routing_consistent",
            passed=routing_ok,
            detail=(
                f"current_node matches expected {expected_node!r}"
                if routing_ok
                else (
                    f"expected current_node {expected_node!r} for status {status!r}, "
                    f"got {current_node!r}"
                )
            ),
            weight=1.5,
        ),
        VerificationCheck(
            name="error_state_absent",
            passed=error_state is None,
            detail=(
                "error_state absent"
                if error_state is None
                else "error_state is present"
            ),
            weight=1.0,
        ),
    ]
    return checks
