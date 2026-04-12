"""Default Mode implementation for Ariadne.

The DefaultMode provides a fallback behavior when no portal-specific mode
is available or identified. It relies on generalized heuristics and LLMs.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field

from src.automation.ariadne.danger_contracts import (
    ApplyDangerReport,
    ApplyDangerSignals,
)
from src.automation.ariadne.models import (
    AriadneStateDefinition,
    JobPosting,
    AriadneTarget,
)
from src.automation.ariadne.modes.base import AriadneMode


class DefaultMode(AriadneMode):
    """Fallback mode for generalized interpretation using LLMs."""

    _danger_keywords = (
        "captcha",
        "security",
        "verify",
        "robot",
        "human",
        "permission denied",
        "access denied",
    )

    def __init__(self):
        self._llm: ChatGoogleGenerativeAI | None = None

    def _get_llm(self) -> ChatGoogleGenerativeAI:
        """Create the shared LLM client lazily to avoid eager runtime setup."""
        if self._llm is None:
            self._llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")
        return self._llm

    async def normalize_job(self, payload: JobPosting) -> JobPosting:
        """Clean up and normalize job posting data using LLM cleanup."""
        try:
            structured_llm = self._get_llm().with_structured_output(JobPosting)
            prompt = (
                "You are an expert at normalizing job posting data. Your goal is to clean up, "
                "fix typos, and standardize the following job data into the provided structure. "
                "Do not invent information; if a field is missing, leave it as is or null.\n\n"
                f"Input Data: {payload.model_dump_json()}"
            )
            normalized = await structured_llm.ainvoke(prompt)
            if isinstance(normalized, JobPosting):
                return normalized
            return payload
        except Exception as e:
            # Log error and return original payload as fallback
            print(f"--- DEFAULT MODE: normalize_job failed: {e} ---")
            return payload

    def _requires_llm_danger_check(self, snapshot: ApplyDangerSignals) -> bool:
        """Run a cheap keyword pass before escalating danger detection to the LLM."""
        evidence = " ".join(
            part.lower()
            for part in [
                snapshot.dom_text,
                snapshot.screenshot_text,
                snapshot.current_url,
            ]
            if part
        )
        if not evidence:
            return False

        return any(
            re.search(rf"\b{re.escape(keyword)}\b", evidence)
            for keyword in self._danger_keywords
        )

    async def inspect_danger(self, snapshot: ApplyDangerSignals) -> ApplyDangerReport:
        """Evaluate security blocks, CAPTCHAs, or login walls via gated LLM analysis."""
        if not self._requires_llm_danger_check(snapshot):
            return ApplyDangerReport(findings=[])

        try:
            structured_llm = self._get_llm().with_structured_output(ApplyDangerReport)
            prompt = (
                "You are a security-focused automation guardian. Analyze the provided DOM and "
                "OCR text from a web page to determine if there is a security block (CAPTCHA), "
                "a login wall, or a 'permission denied' message that prevents the automation "
                "from continuing. Provide a list of findings including machine-readable codes "
                "(e.g. 'captcha_detected', 'login_wall', 'access_denied') and recommended actions.\n\n"
            )
            if snapshot.dom_text:
                prompt += f"DOM Text (truncated):\n{snapshot.dom_text[:10000]}\n\n"
            if snapshot.screenshot_text:
                prompt += f"OCR Text:\n{snapshot.screenshot_text}\n\n"
            if snapshot.current_url:
                prompt += f"Current URL: {snapshot.current_url}\n"

            report = await structured_llm.ainvoke(prompt)
            if isinstance(report, ApplyDangerReport):
                return report
            return ApplyDangerReport(findings=[])
        except Exception as e:
            print(f"--- DEFAULT MODE: inspect_danger failed: {e} ---")
            return ApplyDangerReport(findings=[])

    async def apply_local_heuristics(
        self,
        state_definition: AriadneStateDefinition,
        runtime_state: Optional[Dict[str, Any]] = None,
    ) -> AriadneStateDefinition:
        """Propose selector patches if an error is present in the runtime state."""
        if not runtime_state or not runtime_state.get("errors"):
            return state_definition

        try:
            # Define a local response model for patching components
            class PatchResponse(BaseModel):
                components: Dict[str, AriadneTarget] = Field(
                    description="Map of component names to their corrected selectors."
                )

            structured_llm = self._get_llm().with_structured_output(PatchResponse)

            errors = runtime_state.get("errors", [])
            dom_summary = ""
            if "dom_elements" in runtime_state:
                # Serialize and truncate dom_elements to avoid context window blowup
                dom_summary = str(runtime_state["dom_elements"])[:15000]

            prompt = (
                "You are a web automation expert. The current navigation state failed to execute "
                "because some elements were not found or not interactable. Given the state description, "
                "existing components, and the current DOM content, identify the correct CSS selectors "
                "or text matches for the components. Return ONLY the updated components.\n\n"
                f"State ID: {state_definition.id}\n"
                f"Description: {state_definition.description}\n"
                f"Existing Components: {state_definition.components}\n"
                f"Errors encountered: {errors}\n\n"
                f"Current Page DOM (truncated):\n{dom_summary}"
            )

            response = await structured_llm.ainvoke(prompt)
            components = getattr(response, "components", None)
            if components:
                print(f"--- DEFAULT MODE: LLM proposed {len(components)} patches ---")
                state_definition.components.update(components)

            return state_definition
        except Exception as e:
            print(f"--- DEFAULT MODE: apply_local_heuristics failed: {e} ---")
            return state_definition
