from __future__ import annotations

import json

from src.cli.run_stepstone_autoapply import main
from src.core.application.stepstone_autoapply import StepStoneAutoApplyResult


def test_cli_run_stepstone_autoapply_outputs_json(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "src.cli.run_stepstone_autoapply.run_stepstone_autoapply",
        lambda request: StepStoneAutoApplyResult(
            status="ready",
            action="dry_run_scan",
            summary=f"url={request.source_url}",
            warnings=[],
            artifact_refs={"autoapply_scan": "/tmp/a.json"},
        ),
    )
    monkeypatch.setattr(
        "sys.argv",
        [
            "run_stepstone_autoapply",
            "--job-id",
            "13722751",
            "--source-url",
            "https://www.stepstone.de/stellenangebote--x--13722751-inline.html",
        ],
    )

    assert main() == 0
    output = capsys.readouterr().out
    payload = json.loads(output)
    assert payload["status"] == "ready"
    assert payload["artifact_refs"]["autoapply_scan"] == "/tmp/a.json"
