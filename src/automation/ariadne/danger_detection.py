"""Shared apply-time danger detection for Ariadne and execution motors.

The detector converts routing hints, prior submission state, DOM text, and
optional screenshot text into normalized danger codes so callers can respond
consistently across motors.
"""

from __future__ import annotations

from urllib.parse import urlparse

from src.automation.ariadne.danger_contracts import (
    ApplyDangerFinding,
    ApplyDangerReport,
    ApplyDangerSignals,
)


class ApplyDangerDetector:
    """Evaluate apply-time evidence and return normalized danger findings."""

    _TEXT_RULES: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
        (
            "captcha_challenge",
            (
                "captcha",
                "recaptcha",
                "hcaptcha",
                "verify you are human",
                "i'm not a robot",
                "security check",
            ),
            "pause",
            "The page is asking for a CAPTCHA or human verification challenge.",
        ),
        (
            "anti_bot_challenge",
            (
                "unusual traffic",
                "automated access",
                "access denied",
                "bot detection",
                "request looks automated",
                "temporarily blocked",
            ),
            "pause",
            "The page appears to have triggered an anti-bot or access-control wall.",
        ),
        (
            "duplicate_submission",
            (
                "already applied",
                "already submitted",
                "application already received",
                "you have already applied",
                "duplicate application",
            ),
            "abort",
            "The page indicates this job was already submitted.",
        ),
        (
            "login_required",
            (
                "sign in to continue",
                "log in to continue",
                "please sign in",
                "please log in",
                "login required",
            ),
            "pause",
            "The flow is blocked behind an authentication gate.",
        ),
    )

    def detect(self, signals: ApplyDangerSignals) -> ApplyDangerReport:
        """Return normalized danger findings for the supplied evidence bundle."""
        findings: list[ApplyDangerFinding] = []
        seen_codes: set[tuple[str, str]] = set()

        self._append_submission_finding(signals, findings, seen_codes)
        self._append_routing_finding(signals, findings, seen_codes)
        self._append_text_findings(
            signals.dom_text,
            source="dom_text",
            findings=findings,
            seen_codes=seen_codes,
        )
        self._append_text_findings(
            signals.screenshot_text,
            source="screenshot",
            findings=findings,
            seen_codes=seen_codes,
        )
        return ApplyDangerReport(findings=findings)

    def _append_submission_finding(
        self,
        signals: ApplyDangerSignals,
        findings: list[ApplyDangerFinding],
        seen_codes: set[tuple[str, str]],
    ) -> None:
        if not signals.already_submitted:
            return
        self._append_unique(
            findings,
            seen_codes,
            ApplyDangerFinding(
                code="duplicate_submission",
                source="submission_state",
                recommended_action="abort",
                message="Storage already marks this job as submitted.",
            ),
        )

    def _append_routing_finding(
        self,
        signals: ApplyDangerSignals,
        findings: list[ApplyDangerFinding],
        seen_codes: set[tuple[str, str]],
    ) -> None:
        if signals.route_outcome == "external_url":
            self._append_unique(
                findings,
                seen_codes,
                ApplyDangerFinding(
                    code="external_application_route",
                    source="routing",
                    recommended_action="abort",
                    message=signals.route_reason
                    or "The apply flow redirects to an external application route.",
                    matched_text=signals.application_url,
                ),
            )
            return
        if signals.route_outcome == "email":
            self._append_unique(
                findings,
                seen_codes,
                ApplyDangerFinding(
                    code="email_application_route",
                    source="routing",
                    recommended_action="abort",
                    message=signals.route_reason
                    or "The apply flow requires an email handoff instead of onsite replay.",
                    matched_text=signals.application_url,
                ),
            )
            return
        if signals.route_outcome == "unsupported":
            self._append_unique(
                findings,
                seen_codes,
                ApplyDangerFinding(
                    code="unsupported_application_route",
                    source="routing",
                    recommended_action="abort",
                    message=signals.route_reason
                    or "The apply flow could not be resolved into a supported route.",
                ),
            )
            return
        if self._is_offsite_redirect(
            current_url=signals.current_url,
            application_url=signals.application_url,
        ):
            self._append_unique(
                findings,
                seen_codes,
                ApplyDangerFinding(
                    code="external_application_route",
                    source="routing",
                    recommended_action="abort",
                    message="The live page navigated away from the expected onsite application host.",
                    matched_text=signals.current_url,
                ),
            )

    def _append_text_findings(
        self,
        text: str | None,
        *,
        source: str,
        findings: list[ApplyDangerFinding],
        seen_codes: set[tuple[str, str]],
    ) -> None:
        normalized = self._normalize_text(text)
        if not normalized:
            return
        for code, phrases, action, message in self._TEXT_RULES:
            for phrase in phrases:
                if phrase in normalized:
                    self._append_unique(
                        findings,
                        seen_codes,
                        ApplyDangerFinding(
                            code=code,
                            source=source,
                            recommended_action=action,
                            message=message,
                            matched_text=phrase,
                        ),
                    )
                    break

    def _append_unique(
        self,
        findings: list[ApplyDangerFinding],
        seen_codes: set[tuple[str, str]],
        finding: ApplyDangerFinding,
    ) -> None:
        key = (finding.code, finding.source)
        if key in seen_codes:
            return
        seen_codes.add(key)
        findings.append(finding)

    def _is_offsite_redirect(
        self,
        *,
        current_url: str | None,
        application_url: str | None,
    ) -> bool:
        current_host = self._host(current_url)
        expected_host = self._host(application_url)
        if not current_host or not expected_host:
            return False
        return current_host != expected_host and not current_host.endswith(
            f".{expected_host}"
        )

    def _host(self, value: str | None) -> str | None:
        if not value:
            return None
        parsed = urlparse(value)
        host = parsed.netloc.lower().strip()
        return host or None

    def _normalize_text(self, value: str | None) -> str:
        if not value:
            return ""
        return " ".join(value.lower().split())
