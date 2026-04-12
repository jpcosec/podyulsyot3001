"""Tests for portal and default mode behavior."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

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


@pytest.mark.asyncio
async def test_json_config_mode_word_boundary_no_false_positive():
    """Word boundary matching should prevent false positives like 'human' inside other words."""
    JsonConfigMode._config_cache = {"danger_detection": {"text_rules": ["human"]}}
    JsonConfigMode._configs_loaded = True

    mode = JsonConfigMode("linkedin")

    # "human" appears inside "inhuman" - should NOT match (no word boundary)
    # This was the original false positive: "inhuman" triggered security block
    report = await mode.inspect_danger(
        ApplyDangerSignals(dom_text="This is an inhuman treatment")
    )

    assert report.findings == []


@pytest.mark.asyncio
async def test_json_config_mode_word_boundary_matches_standalone():
    """Word boundary matching should correctly match standalone 'human'."""
    JsonConfigMode._config_cache = {"danger_detection": {"text_rules": ["human"]}}
    JsonConfigMode._configs_loaded = True

    mode = JsonConfigMode("linkedin")

    # "human" as standalone word - should match
    report = await mode.inspect_danger(
        ApplyDangerSignals(dom_text="Please verify you are human to continue")
    )

    assert report.findings
    assert report.findings[0].matched_text == "human"


@pytest.mark.asyncio
async def test_json_config_mode_detects_security_text():
    """Portal modes should restore keyword-based security detection."""
    JsonConfigMode._config_cache = {
        "danger_detection": {"text_rules": ["verify you are human", "security check"]}
    }
    JsonConfigMode._configs_loaded = True

    mode = JsonConfigMode("linkedin")
    report = await mode.inspect_danger(
        ApplyDangerSignals(dom_text="Before continuing, verify you are human")
    )

    assert report.findings
    assert report.findings[0].code == "SECURITY_CHECK_DETECTED"
    assert report.findings[0].matched_text == "verify you are human"


@pytest.mark.asyncio
async def test_default_mode_normalize_job_uses_structured_llm():
    """DefaultMode should use structured LLM normalization when available."""
    payload = _sample_job()
    normalized_payload = payload.model_copy(update={"location": "Berlin, Germany"})

    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(return_value=normalized_payload)

    llm = MagicMock()
    llm.with_structured_output.return_value = structured_llm

    mode = DefaultMode()
    with patch.object(mode, "_get_llm", return_value=llm):
        result = await mode.normalize_job(payload)

    assert result.location == "Berlin, Germany"
    llm.with_structured_output.assert_called_once()


@pytest.mark.asyncio
async def test_default_mode_apply_local_heuristics_merges_llm_patches():
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
    structured_llm.ainvoke = AsyncMock(return_value=response)

    llm = MagicMock()
    llm.with_structured_output.return_value = structured_llm

    mode = DefaultMode()
    with patch.object(mode, "_get_llm", return_value=llm):
        patched = await mode.apply_local_heuristics(
            state_definition,
            runtime_state={"errors": ["missing selector"], "dom_elements": []},
        )

    assert patched.components["submit"].css == "button[type='submit']"


@pytest.mark.asyncio
async def test_default_mode_inspect_danger_skips_llm_on_safe_page():
    """DefaultMode should skip LLM when no dangerous keywords are present."""
    mode = DefaultMode()

    # Safe page with no suspicious keywords
    result = await mode.inspect_danger(
        ApplyDangerSignals(
            dom_text="Welcome to our careers page. Apply now!",
            current_url="https://example.com/careers",
        )
    )

    # Should return empty report without calling LLM
    assert result.findings == []
    assert mode._llm is None  # LLM was never instantiated


@pytest.mark.asyncio
async def test_default_mode_inspect_danger_triggers_on_keywords():
    """DefaultMode should call LLM when dangerous keywords are detected."""
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(return_value=ApplyDangerReport(findings=[]))

    llm = MagicMock()
    llm.with_structured_output.return_value = structured_llm

    mode = DefaultMode()
    with patch.object(mode, "_get_llm", return_value=llm):
        # Page containing "captcha" keyword
        result = await mode.inspect_danger(
            ApplyDangerSignals(
                dom_text="Please complete the captcha to verify you are human",
                current_url="https://example.com/verify",
            )
        )

    # LLM should have been invoked
    structured_llm.ainvoke.assert_called_once()


@pytest.mark.asyncio
async def test_default_mode_inspect_danger_returns_llm_report():
    """DefaultMode should pass through structured LLM danger findings."""
    report = ApplyDangerReport(findings=[])
    structured_llm = MagicMock()
    structured_llm.ainvoke = AsyncMock(return_value=report)

    llm = MagicMock()
    llm.with_structured_output.return_value = structured_llm

    mode = DefaultMode()
    with patch.object(mode, "_get_llm", return_value=llm):
        result = await mode.inspect_danger(
            ApplyDangerSignals(
                dom_text="security check", current_url="https://example.com"
            )
        )

    assert result is report
