from __future__ import annotations

import pytest

from src.core.application.stepstone_autoapply import (
    StepStoneAutoApplyRequest,
    run_stepstone_autoapply,
)
from src.core.scraping.fetch.base import FetchResult


def test_autoapply_dry_run_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    html = """
    <html><body>
      <h1 data-at='header-job-title'>Data Scientist</h1>
      <a data-at='header-company-name'>Acme</a>
      <div data-at='jobad-content'>Great role</div>
      <button data-at='apply-button'>Jetzt bewerben</button>
    </body></html>
    """

    monkeypatch.setattr(
        "src.core.application.stepstone_autoapply.HttpFetcher.fetch",
        lambda _self, _url, timeout_seconds: FetchResult(
            url="u",
            resolved_url="u",
            status_code=200,
            content=html,
            mode="http",
            warnings=[],
        ),
    )
    monkeypatch.setattr(
        "src.core.application.stepstone_autoapply.ArtifactWriter.write_node_stage_json",
        lambda _self, source, job_id, node_name, stage, filename, payload: (
            __import__("pathlib").Path(
                f"/tmp/{source}/{job_id}/{node_name}/{stage}/{filename}"
            )
        ),
    )

    result = run_stepstone_autoapply(
        StepStoneAutoApplyRequest(
            job_id="13722751",
            source_url="https://www.stepstone.de/stellenangebote--x--13722751-inline.html",
            dry_run=True,
        )
    )

    assert result.status == "ready"
    assert result.action == "dry_run_scan"
    assert "autoapply_scan" in result.artifact_refs


def test_autoapply_apply_mode_blocks_on_captcha(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    html = """
    <html><body>
      <h1 data-at='header-job-title'>Data Scientist</h1>
      <div data-at='jobad-content'>Role content</div>
      <button data-at='apply-button'>Jetzt bewerben</button>
      <div>captcha challenge</div>
    </body></html>
    """

    monkeypatch.setattr(
        "src.core.application.stepstone_autoapply.HttpFetcher.fetch",
        lambda _self, _url, timeout_seconds: FetchResult(
            url="u",
            resolved_url="u",
            status_code=200,
            content=html,
            mode="http",
            warnings=[],
        ),
    )
    monkeypatch.setattr(
        "src.core.application.stepstone_autoapply.ArtifactWriter.write_node_stage_json",
        lambda _self, source, job_id, node_name, stage, filename, payload: (
            __import__("pathlib").Path(
                f"/tmp/{source}/{job_id}/{node_name}/{stage}/{filename}"
            )
        ),
    )

    result = run_stepstone_autoapply(
        StepStoneAutoApplyRequest(
            job_id="13722751",
            source_url="https://www.stepstone.de/stellenangebote--x--13722751-inline.html",
            dry_run=False,
        )
    )

    assert result.status == "blocked"
    assert result.action == "apply_blocked"
    assert "captcha_or_bot_protection_detected" in result.warnings
