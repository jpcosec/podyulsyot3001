"""Promotion entrypoint for deterministic BrowserOS MCP recordings."""

from __future__ import annotations

from src.automation.motors.browseros.agent.promoter import BrowserOSLevel2Promoter
from src.automation.motors.browseros.cli.normalizer import BrowserOSMcpTraceNormalizer
from src.automation.motors.browseros.cli.recording import BrowserOSMcpRecording
from src.automation.motors.browseros.promotion_pipeline import (
    BrowserOSCandidateGrouper,
    BrowserOSPathAssessment,
    BrowserOSPathValidator,
)


class BrowserOSMcpPromoter:
    """Promote deterministic MCP recordings into draft replay paths."""

    def __init__(self) -> None:
        self.normalizer = BrowserOSMcpTraceNormalizer()
        self.grouper = BrowserOSCandidateGrouper()
        self.validator = BrowserOSPathValidator()
        self.promoter = BrowserOSLevel2Promoter()

    def promote(self, *, portal: str, recording: BrowserOSMcpRecording):
        candidates = self.normalizer.normalize(recording)
        grouped = self.grouper.group(candidates)
        assessment = self.validator.assess(grouped)
        path = None
        if assessment.outcome == "promotable":
            path = self.promoter.promote(portal=portal, candidates=grouped)
        return grouped, assessment, path
