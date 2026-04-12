"""Base interface for Ariadne Modes (Nyxt Pattern).

Modes provide portal-specific logic, heuristics, and normalization rules
without polluting the core navigation graph.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.automation.ariadne.danger_contracts import (
    ApplyDangerReport,
    ApplyDangerSignals,
)
from src.automation.ariadne.models import AriadneStateDefinition, JobPosting


class AriadneMode(ABC):
    """Abstract Base Class for all portal modes.

    Required async methods:
    - normalize_job
    - inspect_danger
    - apply_local_heuristics
    """

    @abstractmethod
    async def normalize_job(self, payload: JobPosting) -> JobPosting:
        """Apply portal-specific cleanup to scraped job data."""
        raise NotImplementedError

    @abstractmethod
    async def inspect_danger(self, snapshot: ApplyDangerSignals) -> ApplyDangerReport:
        """Perform custom detection for portal-specific security blocks or risks."""
        raise NotImplementedError

    @abstractmethod
    async def apply_local_heuristics(
        self,
        state_definition: AriadneStateDefinition,
        runtime_state: Optional[Dict[str, Any]] = None,
    ) -> AriadneStateDefinition:
        """Inject or patch selectors in the state definition based on local rules."""
        raise NotImplementedError
