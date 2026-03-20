from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from src.core.io.artifact_writer import ArtifactWriter
from src.core.io.workspace_manager import WorkspaceManager
from src.core.scraping.fetch.http_fetcher import HttpFetcher
from src.core.scraping.fetch.playwright_fetcher import PlaywrightFetcher
from src.core.scraping.strategies.stepstone import extract_stepstone_detail
from src.core.tools.errors import ToolDependencyError, ToolFailureError

DEFAULT_TIMEOUT_SECONDS = 25.0


@dataclass(frozen=True)
class StepStoneAutoApplyRequest:
    job_id: str
    source_url: str
    dry_run: bool = True
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


@dataclass(frozen=True)
class StepStoneAutoApplyResult:
    status: str
    action: str
    summary: str
    warnings: list[str] = field(default_factory=list)
    artifact_refs: dict[str, str] = field(default_factory=dict)


def run_stepstone_autoapply(
    request: StepStoneAutoApplyRequest,
) -> StepStoneAutoApplyResult:
    source = "stepstone"
    writer = ArtifactWriter(WorkspaceManager())
    warnings: list[str] = []

    fetch_result = HttpFetcher().fetch(
        request.source_url,
        timeout_seconds=request.timeout_seconds,
    )
    payload = extract_stepstone_detail(fetch_result.content)
    gating = _detect_gating(fetch_result.content, payload)
    warnings.extend(gating["warnings"])

    artifact_refs = _write_autoapply_artifacts(
        writer=writer,
        source=source,
        job_id=request.job_id,
        request=request,
        payload=payload,
        fetch_mode="http",
        gating=gating,
        action="dry_run_scan",
        status="ready" if not gating["blocked"] else "blocked",
    )

    if request.dry_run:
        return StepStoneAutoApplyResult(
            status="ready" if not gating["blocked"] else "blocked",
            action="dry_run_scan",
            summary=_build_summary(payload, gating, dry_run=True),
            warnings=warnings,
            artifact_refs=artifact_refs,
        )

    if gating["blocked"]:
        return StepStoneAutoApplyResult(
            status="blocked",
            action="apply_blocked",
            summary=_build_summary(payload, gating, dry_run=False),
            warnings=warnings,
            artifact_refs=artifact_refs,
        )

    browser_html, browser_warnings = _fetch_with_playwright(
        url=request.source_url,
        timeout_seconds=request.timeout_seconds,
    )
    warnings.extend(browser_warnings)
    browser_payload = extract_stepstone_detail(browser_html)
    browser_gating = _detect_gating(browser_html, browser_payload)
    warnings.extend(browser_gating["warnings"])

    status = "applied_attempted"
    action = "apply_attempt"
    if browser_gating["blocked"]:
        status = "blocked"
        action = "apply_blocked"

    apply_refs = _write_autoapply_artifacts(
        writer=writer,
        source=source,
        job_id=request.job_id,
        request=request,
        payload=browser_payload,
        fetch_mode="playwright",
        gating=browser_gating,
        action=action,
        status=status,
    )
    artifact_refs.update({f"playwright_{k}": v for k, v in apply_refs.items()})

    return StepStoneAutoApplyResult(
        status=status,
        action=action,
        summary=_build_summary(browser_payload, browser_gating, dry_run=False),
        warnings=warnings,
        artifact_refs=artifact_refs,
    )


def _fetch_with_playwright(url: str, timeout_seconds: float) -> tuple[str, list[str]]:
    warnings: list[str] = []
    try:
        result = PlaywrightFetcher().fetch(url, timeout_seconds=timeout_seconds)
        warnings.extend(result.warnings)
        return result.content, warnings
    except ToolDependencyError:
        warnings.append("playwright_dependency_missing")
    except ToolFailureError:
        warnings.append("playwright_fetch_failed")
    return "", warnings


def _detect_gating(html: str, payload: dict[str, Any]) -> dict[str, Any]:
    lowered = html.lower()
    apply_text = str(payload.get("application", {}).get("apply_button_text") or "")
    warnings: list[str] = []
    blocked = False

    if any(token in lowered for token in ("captcha", "datadome", "cloudflare")):
        warnings.append("captcha_or_bot_protection_detected")
        blocked = True
    if any(token in lowered for token in ("anmelden", "einloggen", "sign in", "login")):
        warnings.append("login_ui_detected")
    if not apply_text.strip():
        warnings.append("apply_button_not_found")
        blocked = True

    return {
        "blocked": blocked,
        "warnings": warnings,
        "apply_button_text": apply_text,
    }


def _write_autoapply_artifacts(
    *,
    writer: ArtifactWriter,
    source: str,
    job_id: str,
    request: StepStoneAutoApplyRequest,
    payload: dict[str, Any],
    fetch_mode: str,
    gating: dict[str, Any],
    action: str,
    status: str,
) -> dict[str, str]:
    fetched = datetime.now(timezone.utc).isoformat()
    refs: dict[str, str] = {}
    refs["autoapply_scan"] = str(
        writer.write_node_stage_json(
            source=source,
            job_id=job_id,
            node_name="autoapply",
            stage="input",
            filename=f"scan_{fetch_mode}.json",
            payload={
                "source_url": request.source_url,
                "job_id": request.job_id,
                "dry_run": request.dry_run,
                "fetched_utc": fetched,
                "fetch_mode": fetch_mode,
                "gating": gating,
                "payload": payload,
            },
        )
    )
    refs["autoapply_attempt"] = str(
        writer.write_node_stage_json(
            source=source,
            job_id=job_id,
            node_name="autoapply",
            stage="proposed",
            filename=f"attempt_{fetch_mode}.json",
            payload={
                "status": status,
                "action": action,
                "source_url": request.source_url,
                "job_id": request.job_id,
                "gating": gating,
                "apply_button": payload.get("application", {}),
            },
        )
    )
    return refs


def _build_summary(
    payload: dict[str, Any], gating: dict[str, Any], *, dry_run: bool
) -> str:
    title = str(payload.get("title") or "unknown_title")
    company = str(payload.get("company") or "unknown_company")
    apply_text = str(gating.get("apply_button_text") or "n/a")
    mode = "dry_run" if dry_run else "apply_attempt"
    return (
        f"{mode}: title={title}; company={company}; "
        f"apply_button={apply_text}; blocked={bool(gating.get('blocked'))}"
    )
