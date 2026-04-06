"""XING C4AI apply translator — consumes XING_APPLY portal intent."""
from __future__ import annotations

from pathlib import Path

from src.automation.motors.crawl4ai.apply_engine import ApplyAdapter
from src.automation.motors.crawl4ai.models import FormSelectors
from src.automation.portals.xing.apply import XING_APPLY


class XingApplyAdapter(ApplyAdapter):
    """C4AI apply adapter for XING Easy Apply."""

    portal = XING_APPLY

    @property
    def source_name(self) -> str:
        """Portal identifier for XING."""
        return self.portal.source_name

    def _get_portal_base_url(self) -> str:
        return self.portal.base_url

    def get_session_profile_dir(self) -> Path:
        """Return the browser session profile directory for XING authentication persistence."""
        return Path("data/profiles/xing_profile")

    def get_form_selectors(self) -> FormSelectors:
        """Return CSS selectors for the XING Easy Apply form elements."""
        return FormSelectors(
            apply_button="[data-testid='apply-button']",
            cv_upload="input[type='file'][accept*='pdf']",
            submit_button="[data-testid='submit-button']",
            success_indicator="[data-testid='application-success']",
            first_name="input[name='firstName']",
            last_name="input[name='lastName']",
            email="input[type='email']",
            phone="input[name='phone']",
            letter_upload=None,
            cv_select_existing=None,
        )

    def get_open_modal_script(self) -> str:
        """Return a C4A-Script snippet that opens the XING apply modal if not already open."""
        return """
IF NOT `[data-testid="apply-modal"]` THEN
  CLICK `[data-testid="apply-button"]`
  WAIT `[data-testid="apply-modal"]` 10
END
"""

    def get_fill_form_script(self, profile: dict) -> str:
        """Return a C4A-Script snippet that fills contact fields using {{template}} placeholders resolved at runtime."""
        del profile
        return """
SET `input[name="firstName"]` "{{first_name}}"
SET `input[name="lastName"]` "{{last_name}}"
SET `input[type="email"]` "{{email}}"
IF `input[name="phone"]` THEN
  SET `input[name="phone"]` "{{phone}}"
END
"""

    def get_submit_script(self) -> str:
        """Return a C4A-Script snippet that clicks submit and waits for the success indicator."""
        return """
CLICK `[data-testid="submit-button"]`
WAIT `[data-testid="application-success"]` 15
"""

    def get_success_text(self) -> str:
        """Return the German keyword that confirms a successful XING application."""
        return "Bewerbung"
