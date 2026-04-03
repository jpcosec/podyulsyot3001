"""StepStone Easy Apply adapter.

Design reference: `src/apply/README.md` and `plan_docs/applying/applying_feature_design.md`

Selector discovery: inspect tests/fixtures/apply/stepstone_apply_modal.html
  - Prefer data-at attributes — StepStone commonly uses these for test targeting
  - The selectors below are placeholders — update them after DOM inspection

C4A-Script docs: https://docs.crawl4ai.com/core/c4a-script/
"""

from __future__ import annotations

from pathlib import Path

from src.apply.models import FormSelectors
from src.apply.smart_adapter import ApplyAdapter


class StepStoneApplyAdapter(ApplyAdapter):
    """Adapter for StepStone Easy Apply inline application flow."""

    @property
    def source_name(self) -> str:
        """Return the canonical provider key for StepStone apply."""
        return "stepstone"

    def _get_portal_base_url(self) -> str:
        return "https://www.stepstone.de"

    def get_session_profile_dir(self) -> Path:
        """Return the persistent browser profile directory for StepStone."""
        return Path("data/profiles/stepstone_profile")

    def get_form_selectors(self) -> FormSelectors:
        """CSS selectors for the StepStone Easy Apply modal.

        Discovered by inspecting tests/fixtures/apply/stepstone_apply_modal.html.
        Update these selectors if StepStone updates their DOM (tests will fail first).

        Prefer data-at selectors over class names.
        """
        return FormSelectors(
            # Mandatory — update with real selectors from fixture
            apply_button="[data-at='apply-button']",
            cv_upload="input[type='file']",
            submit_button="[data-at='submit-button']",
            success_indicator="[data-at='application-success']",
            # Optional — set to None if not present in StepStone Easy Apply flow
            first_name="input[name='firstName']",
            last_name="input[name='lastName']",
            email="input[type='email']",
            phone="input[name='phone']",
            letter_upload=None,  # StepStone may or may not request a cover letter
            cv_select_existing=None,
        )

    def get_open_modal_script(self) -> str:
        """Open the Easy Apply modal. Idempotent: checks if modal already open."""
        return """
IF NOT `[data-at="apply-modal"]` THEN
  CLICK `[data-at="apply-button"]`
  WAIT `[data-at="apply-modal"]` 10
END
"""

    def get_fill_form_script(self, profile: dict) -> str:
        """C4A-Script to fill the StepStone Easy Apply form text fields.

        Uses {{placeholder}} syntax — _render_script() injects values via json.dumps().
        Update field selectors to match real StepStone form structure.
        """
        return """
SET `input[name="firstName"]` "{{first_name}}"
SET `input[name="lastName"]` "{{last_name}}"
SET `input[type="email"]` "{{email}}"
IF `input[name="phone"]` THEN
  SET `input[name="phone"]` "{{phone}}"
END
"""

    def get_submit_script(self) -> str:
        """C4A-Script to click submit. Separated from fill for dry-run support."""
        return """
CLICK `[data-at="submit-button"]`
WAIT `[data-at="application-success"]` 15
"""

    def get_success_text(self) -> str:
        """Expected text fragment in the confirmation page after submission.

        Update with actual StepStone confirmation copy once discovered.
        Common German patterns: 'Bewerbung gesendet', 'Erfolgreich beworben', etc.
        """
        return "Bewerbung"
