"""Public portal package surface for routing and portal definitions."""

from src.automation.portals.contracts import PortalRoutingResult
from src.automation.portals.routing import resolve_portal_routing

__all__ = ["PortalRoutingResult", "resolve_portal_routing"]
