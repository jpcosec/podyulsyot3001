"""StepStone-specific apply routing resolution."""

from __future__ import annotations

from typing import Any

from src.automation.portals.contracts import PortalRoutingResult
from src.automation.portals.routing import build_default_portal_route


def route_job_application(ingest_data: dict[str, Any]) -> PortalRoutingResult:
    """Resolve whether a StepStone job stays onsite or redirects outward."""
    return build_default_portal_route(
        portal_name="stepstone",
        portal_host="stepstone.de",
        ingest_data=ingest_data,
    )
