"""Default Mode implementation for Ariadne.

The DefaultMode provides a fallback behavior when no portal-specific mode
is available or identified. It relies on generalized heuristics and LLMs.
"""

from src.automation.ariadne.danger_contracts import ApplyDangerReport, ApplyDangerSignals
from src.automation.ariadne.models import AriadneStateDefinition
from src.automation.ariadne.modes.base import AriadneMode
from src.scraper.models import JobPosting


class DefaultMode(AriadneMode):
    """Fallback mode for generalized interpretation."""

    def normalize_job(self, payload: JobPosting) -> JobPosting:
        """Default normalization (no-op or generic cleanup)."""
        return payload

    def inspect_danger(self, snapshot: ApplyDangerSignals) -> ApplyDangerReport:
        """Default danger detection (empty report)."""
        return ApplyDangerReport(findings=[])

    def apply_local_heuristics(
        self, state: AriadneStateDefinition
    ) -> AriadneStateDefinition:
        """No-op heuristics for the default mode."""
        return state
