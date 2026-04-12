"""Portal-specific Ariadne Mode implementations."""

from src.automation.ariadne.danger_contracts import ApplyDangerReport, ApplyDangerSignals
from src.automation.ariadne.models import AriadneStateDefinition
from src.automation.ariadne.modes.base import AriadneMode
from src.scraper.models import JobPosting


class LinkedInMode(AriadneMode):
    """Placeholder for LinkedIn-specific heuristics and cleanup."""

    def normalize_job(self, payload: JobPosting) -> JobPosting:
        return payload

    def inspect_danger(self, snapshot: ApplyDangerSignals) -> ApplyDangerReport:
        return ApplyDangerReport(findings=[])

    def apply_local_heuristics(
        self, state: AriadneStateDefinition
    ) -> AriadneStateDefinition:
        return state


class StepStoneMode(AriadneMode):
    """Placeholder for StepStone-specific heuristics and cleanup."""

    def normalize_job(self, payload: JobPosting) -> JobPosting:
        return payload

    def inspect_danger(self, snapshot: ApplyDangerSignals) -> ApplyDangerReport:
        return ApplyDangerReport(findings=[])

    def apply_local_heuristics(
        self, state: AriadneStateDefinition
    ) -> AriadneStateDefinition:
        return state


class XingMode(AriadneMode):
    """Placeholder for Xing-specific heuristics and cleanup."""

    def normalize_job(self, payload: JobPosting) -> JobPosting:
        return payload

    def inspect_danger(self, snapshot: ApplyDangerSignals) -> ApplyDangerReport:
        return ApplyDangerReport(findings=[])

    def apply_local_heuristics(
        self, state: AriadneStateDefinition
    ) -> AriadneStateDefinition:
        return state
