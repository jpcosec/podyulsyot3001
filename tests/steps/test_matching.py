"""Tests for the matching step."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest

from src.models.pipeline_contract import ReviewedMapping, ReviewedClaim
from src.steps import StepResult
from src.steps.matching import (
    run,
    approve,
    _extract_keywords_from_proposal,
)
from src.utils.pipeline import MatchProposalPipeline
from src.utils.state import JobState


@pytest.fixture
def temp_pipeline_root(tmp_path):
    """Create a temporary pipeline root for testing."""
    pipeline_root = tmp_path / "data" / "pipelined_data"
    pipeline_root.mkdir(parents=True, exist_ok=True)
    return pipeline_root


@pytest.fixture
def mock_job_state(temp_pipeline_root, monkeypatch):
    """Create a JobState with mocked PIPELINE_ROOT."""
    monkeypatch.setattr(
        "src.utils.state.PIPELINE_ROOT",
        temp_pipeline_root,
    )
    job_id = "201084"
    source_dir = temp_pipeline_root / "tu_berlin"
    source_dir.mkdir(parents=True, exist_ok=True)
    return JobState(job_id, source="tu_berlin")


class TestMatchingRun:
    """Tests for the run() function."""

    def test_run_skipped_when_complete_and_not_force(self, mock_job_state):
        """Verify step returns 'skipped' when outputs exist and force=False."""
        # Create matching outputs
        for rel_path in mock_job_state.STEP_OUTPUTS["matching"]:
            mock_job_state.write_artifact(rel_path, "content")

        result = run(mock_job_state, force=False)

        assert result.status == "skipped"
        assert result.produced == []
        assert "already complete" in result.message

    def test_run_produces_proposal_and_keywords(self, mock_job_state, monkeypatch):
        """Verify run() produces match_proposal.md and keywords.json."""
        # Create job.md so matching can proceed
        job_md = """# Research Assistant III-51/26, Bioprocess Engineering
reference_number: 201084
- [ ] PhD or advanced degree in bioprocess engineering
- [ ] Experience with fermentation process control
- [ ] Python programming skills
"""
        mock_job_state.write_artifact("job.md", job_md)

        # Mock MatchProposalPipeline to return a proposal path with sample content
        proposal_content = """---
status: proposed
job_id: 201084
generated: 2026-03-02T14:30:00Z
---

# Match Proposal: Research Assistant III-51/26

## Requirements Mapping

### R1: PhD or advanced degree in bioprocess engineering [FULL]
Evidence: MSc Chemical Engineering (UPLA, 2022)
Claim: "MSc in Chemical Engineering with specialization in bioprocess systems"
Confidence: strong
Decision: [ ] approve  [ ] edit  [ ] reject
Edited Claim:
Notes:

### R2: Experience with fermentation process control [PARTIAL]
Evidence: Airflow pipeline work
Claim: "Experience designing process control pipelines"
Confidence: weak
Decision: [ ] approve  [ ] edit  [ ] reject
Edited Claim:
Notes:

### R3: Python programming skills [FULL]
Evidence: 4 years Python development
Claim: "4+ years Python development"
Confidence: strong
Decision: [ ] approve  [ ] edit  [ ] reject
Edited Claim:
Notes:

## Gaps (no evidence found)

- None found.

## Proposed Summary

Generated summary based on approved claims.
"""

        class StubPipeline:
            def execute_proposal(self, job_id, source="tu_berlin"):
                proposal_path = mock_job_state.artifact_path(
                    "planning/match_proposal.md"
                )
                proposal_path.parent.mkdir(parents=True, exist_ok=True)
                proposal_path.write_text(proposal_content, encoding="utf-8")
                return proposal_path

        monkeypatch.setattr("src.steps.matching.MatchProposalPipeline", StubPipeline)

        result = run(mock_job_state)

        assert result.status == "ok"
        assert "planning/match_proposal.md" in result.produced
        assert "planning/keywords.json" in result.produced

        # Verify keywords.json was written
        keywords = mock_job_state.read_json_artifact("planning/keywords.json")
        assert "keywords" in keywords
        assert "categories" in keywords
        assert "match_strength" in keywords

    def test_run_reads_comments_from_previous_output(self, mock_job_state, monkeypatch):
        """Verify run() reads comments from its own output and input files."""
        # Create job.md with a comment
        job_md = """# Research Assistant III-51/26
reference_number: 201084
- [ ] PhD or advanced degree <!-- Check if this matches candidate -->
"""
        mock_job_state.write_artifact("job.md", job_md)

        # Create previous proposal with a comment
        proposal_with_comment = """---
status: proposed
job_id: 201084
---

# Match Proposal

## Requirements Mapping

<!-- This requirement was missing in the job description -->
### R1: Test [FULL]
Claim: Test claim
Decision: [ ] approve

## Gaps

## Proposed Summary
"""
        mock_job_state.write_artifact(
            "planning/match_proposal.md", proposal_with_comment
        )

        class StubPipeline:
            def execute_proposal(self, job_id, source="tu_berlin"):
                proposal_path = mock_job_state.artifact_path(
                    "planning/match_proposal.md"
                )
                return proposal_path

        monkeypatch.setattr("src.steps.matching.MatchProposalPipeline", StubPipeline)

        result = run(mock_job_state, force=True)

        # Should have found at least one comment (from either job.md or proposal)
        assert result.status == "ok"
        assert result.comments_found >= 1

    def test_run_removes_stale_reviewed_mapping_on_regeneration(
        self,
        mock_job_state,
        monkeypatch,
    ):
        """Verify run() removes reviewed_mapping.json when proposal regenerates."""
        mock_job_state.write_artifact("job.md", "# Job\n- [ ] Requirement")
        mock_job_state.write_json_artifact(
            "planning/reviewed_mapping.json",
            {"job_id": "201084", "status": "reviewed", "claims": []},
        )

        proposal_content = """---
status: proposed
job_id: 201084
---

# Match Proposal

## Requirements Mapping

### R1: Requirement [FULL]
Evidence IDs: E1
Evidence: Evidence text
Claim: Claim text
Confidence: strong
Decision: [ ] approve  [ ] edit  [ ] reject
Edited Claim:
Notes:

## Gaps (no evidence found)

## Proposed Summary
"""

        class StubPipeline:
            def execute_proposal(self, job_id, source="tu_berlin"):
                proposal_path = mock_job_state.artifact_path(
                    "planning/match_proposal.md"
                )
                proposal_path.parent.mkdir(parents=True, exist_ok=True)
                proposal_path.write_text(proposal_content, encoding="utf-8")
                return proposal_path

        monkeypatch.setattr("src.steps.matching.MatchProposalPipeline", StubPipeline)

        result = run(mock_job_state, force=True)

        assert result.status == "ok"
        assert not mock_job_state.artifact_path(
            "planning/reviewed_mapping.json"
        ).exists()

    def test_run_error_when_pipeline_fails(self, mock_job_state, monkeypatch):
        """Verify run() returns error when pipeline fails."""

        class FailingPipeline:
            def execute_proposal(self, job_id, source="tu_berlin"):
                raise Exception("Pipeline error")

        monkeypatch.setattr("src.steps.matching.MatchProposalPipeline", FailingPipeline)

        result = run(mock_job_state)

        assert result.status == "error"
        assert "Failed" in result.message


class TestMatchingApprove:
    """Tests for the approve() function."""

    def test_approve_produces_reviewed_mapping(self, mock_job_state):
        """Verify approve() reads proposal and produces reviewed_mapping.json."""
        # Create a valid proposal
        proposal_content = """---
status: proposed
job_id: 201084
generated: 2026-03-02T14:30:00Z
---

# Match Proposal: Research Assistant

## Requirements Mapping

### R1: Test requirement [FULL]
Evidence IDs: E1
Claim: Test claim text
Confidence: strong
Decision: [x] approve
Edited Claim:
Notes:

### R2: Second requirement [PARTIAL]
Evidence IDs: E2
Claim: Second claim
Confidence: weak
Decision: [x] edit
Edited Claim: Edited version of second claim
Notes: Some notes

## Gaps (no evidence found)

- Gap 1: Missing skill

## Proposed Summary

Summary text here.
"""
        mock_job_state.write_artifact("planning/match_proposal.md", proposal_content)

        result = approve(mock_job_state)

        assert result.status == "ok"
        assert "planning/reviewed_mapping.json" in result.produced

        # Verify the mapping was written and parsed correctly
        mapping_data = mock_job_state.read_json_artifact(
            "planning/reviewed_mapping.json"
        )
        assert mapping_data["job_id"] == "201084"
        assert mapping_data["status"] == "reviewed"
        assert len(mapping_data["claims"]) == 2
        assert mapping_data["claims"][0]["decision"] == "approved"
        assert mapping_data["claims"][1]["decision"] == "edited"
        assert (
            mapping_data["claims"][1]["claim_text"] == "Edited version of second claim"
        )

    def test_approve_extracts_gaps_and_summary(self, mock_job_state):
        """Verify approve() correctly extracts gaps and summary."""
        proposal_content = """---
status: proposed
job_id: 201084
---

# Match Proposal

## Requirements Mapping

### R1: Requirement [FULL]
Evidence IDs: E1
Claim: Claim
Confidence: strong
Decision: [x] approve
Edited Claim:
Notes:

## Gaps (no evidence found)

- Gap 1: Missing skill A
- Gap 2: Missing skill B

## Proposed Summary

This is my proposal summary.
"""
        mock_job_state.write_artifact("planning/match_proposal.md", proposal_content)

        result = approve(mock_job_state)

        assert result.status == "ok"

        mapping_data = mock_job_state.read_json_artifact(
            "planning/reviewed_mapping.json"
        )
        assert len(mapping_data["gaps"]) == 2
        assert "Gap 1: Missing skill A" in mapping_data["gaps"]
        assert "This is my proposal summary." in mapping_data["summary"]

    def test_approve_error_when_proposal_missing(self, mock_job_state):
        """Verify approve() returns error when proposal.md doesn't exist."""
        result = approve(mock_job_state)

        assert result.status == "error"
        assert "not found" in result.message

    def test_approve_marks_status_as_reviewed(self, mock_job_state):
        """Verify approve() marks the mapping status as 'reviewed'."""
        proposal_content = """---
status: proposed
job_id: 201084
---

# Match Proposal

## Requirements Mapping

### R1: Test [FULL]
Evidence IDs:
Claim: Claim
Confidence: strong
Decision: [x] approve
Edited Claim:
Notes:

## Gaps (no evidence found)

## Proposed Summary
"""
        mock_job_state.write_artifact("planning/match_proposal.md", proposal_content)

        result = approve(mock_job_state)

        assert result.status == "ok"

        mapping_data = mock_job_state.read_json_artifact(
            "planning/reviewed_mapping.json"
        )
        assert mapping_data["status"] == "reviewed"

    def test_approve_accepts_flexible_checkbox_formats(self, mock_job_state):
        """Verify approve() parses decisions with loose checkbox formatting."""
        proposal_content = """---
status: proposed
job_id: 201084
---

# Match Proposal

## Requirements Mapping

### R1: Requirement one [FULL]
Evidence IDs: E1
Claim: Claim one
Confidence: strong
Decision: [ x] approve  [ ] edit  [ ] reject
Edited Claim:
Notes:

### R2: Requirement two [PARTIAL]
Evidence IDs: E2
Claim: Claim two
Confidence: moderate
Decision: [ ] approve  [x ] edit  [ ] reject
Edited Claim: Claim two edited
Notes:

### R3: Requirement three [NONE]
Evidence IDs: None
Claim: Claim three
Confidence: weak
Decision: [ ] approve  [ ] edit  x[ ] reject
Edited Claim:
Notes:

## Gaps (no evidence found)

## Proposed Summary
"""
        mock_job_state.write_artifact("planning/match_proposal.md", proposal_content)

        result = approve(mock_job_state)

        assert result.status == "ok"
        mapping_data = mock_job_state.read_json_artifact(
            "planning/reviewed_mapping.json"
        )
        assert len(mapping_data["claims"]) == 3
        assert mapping_data["claims"][0]["decision"] == "approved"
        assert mapping_data["claims"][1]["decision"] == "edited"
        assert mapping_data["claims"][1]["claim_text"] == "Claim two edited"
        assert mapping_data["claims"][2]["decision"] == "rejected"

    def test_approve_logs_comments_from_proposal(self, mock_job_state):
        """Verify approve() always logs extracted proposal comments."""
        proposal_content = """---
status: proposed
job_id: 201084
---

# Match Proposal

## Requirements Mapping

### R1: Requirement [FULL]
Evidence IDs: E1
Claim: Claim
Confidence: strong
Decision: [x] approve
Edited Claim:
Notes: <!-- tighten wording -->

## Gaps (no evidence found)

## Proposed Summary
"""
        mock_job_state.write_artifact("planning/match_proposal.md", proposal_content)

        result = approve(mock_job_state)

        assert result.status == "ok"
        assert result.comments_found == 1

        log_path = mock_job_state.artifact_path(".metadata/comments.jsonl")
        log_data = json.loads(log_path.read_text(encoding="utf-8"))
        assert any(entry["step"] == "match_approve" for entry in log_data)


class TestKeywordsExtraction:
    """Tests for _extract_keywords_from_proposal()."""

    def test_keywords_extraction_basic(self):
        """Verify keyword extraction from sample proposal."""
        proposal_content = """---
status: proposed
job_id: 201084
---

# Match Proposal

## Requirements Mapping

### R1: Python programming skills [FULL]
Claim: Python development experience

### R2: Process control experience [PARTIAL]
Claim: Control systems knowledge

### R3: Missing requirement [NONE]
Claim: No coverage

## Gaps

## Proposed Summary
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            proposal_path = Path(tmpdir) / "match_proposal.md"
            proposal_path.write_text(proposal_content)

            keywords = _extract_keywords_from_proposal(proposal_path)

            assert "python" in keywords["keywords"]
            assert "process" in keywords["keywords"]
            assert keywords["match_strength"] == 0.5  # 1 full + 0.5*1 partial / 3 total

    def test_keywords_extraction_categories(self):
        """Verify category inference from proposal text."""
        proposal_content = """---
status: proposed
job_id: 201084
---

# Match Proposal

## Requirements Mapping

### R1: MSc degree in engineering [FULL]
Claim: Education requirement

### R2: Python programming [FULL]
Claim: Programming skill

### R3: 5 years experience [PARTIAL]
Claim: Experience requirement

## Gaps

## Proposed Summary
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            proposal_path = Path(tmpdir) / "match_proposal.md"
            proposal_path.write_text(proposal_content)

            keywords = _extract_keywords_from_proposal(proposal_path)

            assert "Education" in keywords["categories"]
            assert "Programming" in keywords["categories"]
            assert "Experience" in keywords["categories"]

    def test_keywords_extraction_empty_proposal(self):
        """Verify graceful handling of empty/missing proposal."""
        with tempfile.TemporaryDirectory() as tmpdir:
            proposal_path = Path(tmpdir) / "missing.md"

            keywords = _extract_keywords_from_proposal(proposal_path)

            assert keywords["keywords"] == []
            assert keywords["categories"] == []
            assert keywords["match_strength"] == 0.0

    def test_keywords_extraction_match_strength_calculation(self):
        """Verify match strength calculation (full=1, partial=0.5, none=0)."""
        proposal_content = """---
status: proposed
job_id: 201084
---

# Match Proposal

## Requirements Mapping

### R1: Req1 [FULL]
Claim: Full coverage

### R2: Req2 [FULL]
Claim: Full coverage

### R3: Req3 [PARTIAL]
Claim: Partial coverage

### R4: Req4 [NONE]
Claim: No coverage

## Gaps

## Proposed Summary
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            proposal_path = Path(tmpdir) / "match_proposal.md"
            proposal_path.write_text(proposal_content)

            keywords = _extract_keywords_from_proposal(proposal_path)

            # (2 full + 0.5 partial) / 4 total = 2.5 / 4 = 0.625
            assert keywords["match_strength"] == 0.62  # rounded to 2 decimals

    def test_keywords_handles_req_and_r_formats(self):
        """Verify extraction works with both req_N and RN heading formats."""
        proposal_content = """---
status: proposed
job_id: 201084
---

# Match Proposal

## Requirements Mapping

### req_1: First requirement [FULL]
Claim: First claim

### R2: Second requirement [FULL]
Claim: Second claim

## Gaps

## Proposed Summary
"""
        with tempfile.TemporaryDirectory() as tmpdir:
            proposal_path = Path(tmpdir) / "match_proposal.md"
            proposal_path.write_text(proposal_content)

            keywords = _extract_keywords_from_proposal(proposal_path)

            # Should extract from both req_1 and R2
            assert "requirement" in keywords["keywords"]
            assert keywords["match_strength"] == 1.0


class TestProposalRoundArchiving:
    """Tests for match proposal round history handling."""

    def test_archive_existing_proposal_to_next_round(self, tmp_path):
        planning_dir = tmp_path
        round1 = planning_dir / "match_proposal.round1.md"
        proposal = planning_dir / "match_proposal.md"
        round1.write_text("round1", encoding="utf-8")
        proposal.write_text("current", encoding="utf-8")

        MatchProposalPipeline._archive_existing_proposal(proposal)

        round2 = planning_dir / "match_proposal.round2.md"
        assert round1.read_text(encoding="utf-8") == "round1"
        assert round2.read_text(encoding="utf-8") == "current"
        assert not proposal.exists()
