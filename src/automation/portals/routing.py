"""Portal routing loader and shared heuristics.

The routing layer keeps portal-specific apply branching in `src/automation/portals`
instead of Ariadne or motor adapters. Each portal package exposes a
`route_job_application()` function that returns a `PortalRoutingResult`.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any
from urllib.parse import urlparse

from src.automation.portals.contracts import PortalRoutingResult


def resolve_portal_routing(
    portal_name: str,
    ingest_data: dict[str, Any],
) -> PortalRoutingResult:
    """Load the portal routing module and resolve the apply route."""
    module = import_module(f"src.automation.portals.{portal_name}.routing")
    route_job_application = getattr(module, "route_job_application")
    return route_job_application(ingest_data)


def build_default_portal_route(
    *,
    portal_name: str,
    portal_host: str,
    ingest_data: dict[str, Any],
    default_path_id: str = "standard_easy_apply",
) -> PortalRoutingResult:
    """Resolve an enriched job into an onsite, external, or email route."""
    method = _normalize_method(ingest_data.get("application_method"))
    application_url = _normalize_url(ingest_data.get("application_url"))
    detail_url = _normalize_url(ingest_data.get("url"))
    target_url = application_url or detail_url
    application_email = _normalize_email(ingest_data.get("application_email"))

    diagnostics = {
        "portal_name": portal_name,
        "application_method": method,
        "portal_host": portal_host,
        "detail_url": detail_url,
        "application_url": application_url,
        "application_email": application_email,
    }

    if method == "email" or (application_email and not application_url):
        return PortalRoutingResult(
            outcome="email",
            application_email=application_email,
            application_url=target_url,
            reason="Enriched ingest state requires an email application handoff.",
            diagnostics=diagnostics,
        )

    if target_url and _url_matches_host(target_url, portal_host):
        return PortalRoutingResult(
            outcome="onsite",
            path_id=default_path_id,
            application_url=target_url,
            reason="Apply flow stays on the portal and can use the Ariadne map.",
            diagnostics=diagnostics,
        )

    if target_url:
        return PortalRoutingResult(
            outcome="external_url",
            application_url=target_url,
            reason="Apply flow redirects to an external ATS or third-party form.",
            diagnostics=diagnostics,
        )

    return PortalRoutingResult(
        outcome="unsupported",
        reason="Enriched ingest state does not provide a usable onsite, external, or email route.",
        diagnostics=diagnostics,
    )


def _normalize_method(value: Any) -> str | None:
    if not value:
        return None
    lowered = str(value).strip().lower()
    if not lowered:
        return None
    if lowered in {"onsite", "direct_url", "email"}:
        return lowered
    if "email" in lowered or "e-mail" in lowered or "mail" in lowered:
        return "email"
    if "onsite" in lowered or "easy apply" in lowered or "easyapply" in lowered:
        return "onsite"
    if "direct" in lowered or "external" in lowered or "redirect" in lowered:
        return "direct_url"
    return lowered


def _normalize_url(value: Any) -> str | None:
    if not value:
        return None
    candidate = str(value).strip()
    if not candidate or candidate.lower().startswith("mailto:"):
        return None
    parsed = urlparse(candidate)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return None
    return candidate


def _normalize_email(value: Any) -> str | None:
    if not value:
        return None
    candidate = str(value).strip()
    if candidate.lower().startswith("mailto:"):
        candidate = candidate[7:]
    candidate = candidate.split("?", 1)[0].strip()
    if "@" not in candidate:
        return None
    return candidate


def _url_matches_host(url: str, portal_host: str) -> bool:
    host = urlparse(url).netloc.lower()
    normalized_portal_host = portal_host.lower().lstrip(".")
    return host == normalized_portal_host or host.endswith(f".{normalized_portal_host}")
