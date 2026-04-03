"""XING Easy Apply adapter.

Design reference: `src/apply/README.md`

Selector discovery: inspect tests/fixtures/apply/xing_apply_modal.html
  - Prefer data-testid attributes over generated class names (more stable)
  - The selectors below are placeholders — update them after DOM inspection

C4A-Script docs: https://docs.crawl4ai.com/core/c4a-script/
"""

from __future__ import annotations

from pathlib import Path

from src.apply.models import FormSelectors
from src.apply.smart_adapter import ApplyAdapter


class XingApplyAdapter(ApplyAdapter):
    """Adapter for XING Easy Apply inline application flow."""

    @property
    def source_name(self) -> str:
        """Return the canonical provider key for XING apply."""
        return "xing"

    def _get_portal_base_url(self) -> str:
        return "https://www.xing.com"

    def get_session_profile_dir(self) -> Path:
        """Return the persistent browser profile directory for XING."""
        return Path("data/profiles/xing_profile")

    def get_form_selectors(self) -> FormSelectors:
        """CSS selectors for the XING Easy Apply modal.

        Discovered by inspecting tests/fixtures/apply/xing_apply_modal.html.
        Update these selectors if XING updates their DOM (tests will fail first).

        Prefer data-testid selectors — they are more stable than generated class names.
        """
        return FormSelectors(
            # Mandatory — update with real selectors from fixture
            apply_button="[data-testid='apply-button']",
            cv_upload="input[type='file'][accept*='pdf']",
            submit_button="[data-testid='submit-button']",
            success_indicator="[data-testid='application-success']",
            # Optional — set to None if not present in the XING Easy Apply flow
            first_name="input[name='firstName']",
            last_name="input[name='lastName']",
            email="input[type='email']",
            phone="input[name='phone']",
            letter_upload=None,  # XING Easy Apply may not request a cover letter
            cv_select_existing=None,  # Set if XING offers "select saved CV" option
        )

    def get_open_modal_script(self) -> str:
        """Open the Easy Apply modal. Idempotent: checks if modal already open."""
        return """
IF NOT `[data-testid="apply-modal"]` THEN
  CLICK `[data-testid="apply-button"]`
  WAIT `[data-testid="apply-modal"]` 10
END
"""

    def get_fill_form_script(self, profile: dict) -> str:
        """C4A-Script to fill the XING Easy Apply form text fields.

        Uses {{placeholder}} syntax — _render_script() injects values via json.dumps().
        File upload is NOT here — handled by the before_retrieve_html hook.

        Update the SET selectors to match the real XING form field selectors.
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
CLICK `[data-testid="submit-button"]`
WAIT `[data-testid="application-success"]` 15
"""

    def get_success_text(self) -> str:
        """Expected text fragment in the confirmation page after submission.

        Update with actual XING confirmation copy once discovered.
        Common patterns: 'Bewerbung wurde gesendet', 'Application submitted', etc.
        """
        return "Bewerbung"
