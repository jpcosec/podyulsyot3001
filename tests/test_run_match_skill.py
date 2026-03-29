from __future__ import annotations

import json

from langgraph.checkpoint.memory import InMemorySaver

from src.core.ai.match_skill.main import main
from src.core.ai.match_skill.contracts import MatchEnvelope
from src.core.ai.match_skill.graph import build_match_skill_graph
from src.core.ai.match_skill.storage import MatchArtifactStore


class FakeMatchChain:
    def __init__(self, responses: list[MatchEnvelope]):
        self.responses = list(responses)

    def invoke(self, payload):
        if not self.responses:
            raise AssertionError("no fake responses left")
        return self.responses.pop(0)


def test_run_match_skill_cli_run_and_resume(tmp_path, capsys) -> None:
    requirements_path = tmp_path / "requirements.json"
    evidence_path = tmp_path / "profile.json"
    review_payload_path = tmp_path / "review.json"
    output_dir = tmp_path / "out"

    fake_app = build_match_skill_graph(
        match_chain=FakeMatchChain(
            [
                MatchEnvelope(
                    matches=[
                        {
                            "requirement_id": "R1",
                            "status": "matched",
                            "score": 0.9,
                            "evidence_ids": ["P1"],
                            "evidence_quotes": ["Built Python pipelines"],
                            "reasoning": "Directly supported",
                        }
                    ],
                    total_score=0.9,
                    decision_recommendation="proceed",
                    summary_notes="Strong fit",
                )
            ]
        ),
        artifact_store=MatchArtifactStore(output_dir),
        checkpointer=InMemorySaver(),
    )

    import src.core.ai.match_skill.main as cli_module

    def fake_build_match_skill_graph(*, checkpointer=None, artifact_store=None):
        return fake_app

    cli_module.build_match_skill_graph = fake_build_match_skill_graph

    requirements_path.write_text(
        json.dumps([{"id": "R1", "text": "Python", "priority": "must"}]),
        encoding="utf-8",
    )
    evidence_path.write_text(
        json.dumps([{"id": "P1", "description": "Built Python pipelines"}]),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--source",
            "demo",
            "--job-id",
            "job-1",
            "--requirements",
            str(requirements_path),
            "--profile-evidence",
            str(evidence_path),
            "--output-dir",
            str(output_dir),
        ]
    )
    assert exit_code == 0
    run_output = json.loads(capsys.readouterr().out)
    assert run_output["status"] == "pending_review"
    assert run_output["review_surface_path"]

    approved_path = output_dir / "demo/job-1/nodes/match_skill/approved/state.json"
    review_payload_path.write_text(
        json.dumps(
            {
                "source_state_hash": MatchArtifactStore.sha256_file(approved_path),
                "items": [{"requirement_id": "R1", "decision": "approve"}],
            }
        ),
        encoding="utf-8",
    )

    exit_code = main(
        [
            "--source",
            "demo",
            "--job-id",
            "job-1",
            "--output-dir",
            str(output_dir),
            "--resume",
            "--review-payload",
            str(review_payload_path),
        ]
    )
    assert exit_code == 0
    resume_output = json.loads(capsys.readouterr().out)
    assert resume_output["status"] == "completed"
    assert resume_output["review_decision"] == "approve"
