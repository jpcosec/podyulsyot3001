"""Tests for portal and default mode behavior."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from src.automation.ariadne.danger_contracts import (
    ApplyDangerReport,
    ApplyDangerSignals,
)
from src.automation.ariadne.contracts.base import AriadneTarget
from src.automation.ariadne.models import (
    AriadneObserve,
    AriadneStateDefinition,
    JobPosting,
)
from src.automation.ariadne.modes.default import DefaultMode
from src.automation.portals.modes.portals import JsonConfigMode


def _sample_job() -> JobPosting:
    return JobPosting(
        job_title="Engineer",
        company_name="Acme",
        location="Berlin",
        employment_type="Full-time",
        requirements=["Python"],
    )


def test_json_config_mode_detects_security_text():
    """Portal modes should restore keyword-based security detection."""
    JsonConfigMode._config_cache = {
        "danger_detection": {"text_rules": ["verify you are human", "security check"]}
    }
    JsonConfigMode._configs_loaded = True

    mode = JsonConfigMode("linkedin")
    report = mode.inspect_danger(
        ApplyDangerSignals(dom_text="Before continuing, verify you are human")
    )

    assert report.findings
    assert report.findings[0].code == "SECURITY_CHECK_DETECTED"
    assert report.findings[0].matched_text == "verify you are human"


def test_default_mode_normalize_job_uses_structured_llm():
    """DefaultMode should use structured LLM normalization when available."""
    payload = _sample_job()
    normalized_payload = payload.model_copy(update={"location": "Berlin, Germany"})

    structured_llm = MagicMock()
    structured_llm.invoke.return_value = normalized_payload

    llm = MagicMock()
    llm.with_structured_output.return_value = structured_llm

    mode = DefaultMode()
    with patch.object(mode, "_get_llm", return_value=llm):
        result = mode.normalize_job(payload)

    assert result.location == "Berlin, Germany"
    llm.with_structured_output.assert_called_once()


def test_default_mode_apply_local_heuristics_merges_llm_patches():
    """DefaultMode should merge structured LLM selector patches into the state."""
    state_definition = AriadneStateDefinition(
        id="apply",
        description="Application form",
        presence_predicate=AriadneObserve(required_elements=[]),
        components={},
    )

    response = MagicMock()
    response.components = {"submit": AriadneTarget(css="button[type='submit']")}

    structured_llm = MagicMock()
    structured_llm.invoke.return_value = response

    llm = MagicMock()
    llm.with_structured_output.return_value = structured_llm

    mode = DefaultMode()
    with patch.object(mode, "_get_llm", return_value=llm):
        patched = mode.apply_local_heuristics(
            state_definition,
            runtime_state={"errors": ["missing selector"], "dom_elements": []},
        )

    assert patched.components["submit"].css == "button[type='submit']"


def test_default_mode_inspect_danger_returns_llm_report():
    """DefaultMode should pass through structured LLM danger findings."""
    report = ApplyDangerReport(findings=[])
    structured_llm = MagicMock()
    structured_llm.invoke.return_value = report

    llm = MagicMock()
    llm.with_structured_output.return_value = structured_llm

    mode = DefaultMode()
    with patch.object(mode, "_get_llm", return_value=llm):
        result = mode.inspect_danger(
            ApplyDangerSignals(
                dom_text="security check", current_url="https://example.com"
            )
        )

    assert result is report
