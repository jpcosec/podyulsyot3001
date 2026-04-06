"""LinkedIn C4AI apply translator — consumes LINKEDIN_APPLY portal intent."""
from __future__ import annotations

from pathlib import Path

from src.automation.motors.crawl4ai.apply_engine import ApplyAdapter
from src.automation.motors.crawl4ai.models import FormSelectors
from src.automation.portals.linkedin.apply import LINKEDIN_APPLY


class LinkedInApplyAdapter(ApplyAdapter):
    """C4AI apply adapter for LinkedIn Easy Apply."""

    portal = LINKEDIN_APPLY

    @property
    def source_name(self) -> str:
        """Portal identifier for LinkedIn."""
        return self.portal.source_name

    def _get_portal_base_url(self) -> str:
        return self.portal.base_url

    def get_session_profile_dir(self) -> Path:
        """Return the browser session profile directory for LinkedIn authentication persistence."""
        return Path("data/profiles/linkedin_profile")

    def get_form_selectors(self) -> FormSelectors:
        """Return CSS selectors for the LinkedIn Easy Apply form. Includes cv_select_existing for the resume-picker flow."""
        return FormSelectors(
            apply_button="button.jobs-apply-button",
            cv_upload="input[type='file'][accept*='pdf']",
            submit_button="button.jp-apply-form-submit",
            success_indicator="[data-test-modal-id='post-apply-modal']",
            first_name="input[name='firstName']",
            last_name="input[name='lastName']",
            email="input[type='email']",
            phone="input[name='phoneNumber']",
            letter_upload=None,
            cv_select_existing="button.jobs-resume-picker__resume-list-item-select-btn",
        )

    def get_open_modal_script(self) -> str:
        """Return a C4A-Script snippet that opens the LinkedIn Easy Apply modal if not already open."""
        return """
IF NOT `[data-test-modal-id="apply-modal"]` THEN
  CLICK `button.jobs-apply-button`
  WAIT `[data-test-modal-id="apply-modal"]` 10
END
"""

    def get_fill_form_script(self, profile: dict) -> str:
        """Return a C4A-Script snippet that fills contact fields using {{template}} placeholders resolved at runtime."""
        del profile
        return """
IF `input[name="firstName"]` THEN
  SET `input[name="firstName"]` "{{first_name}}"
END
IF `input[name="lastName"]` THEN
  SET `input[name="lastName"]` "{{last_name}}"
END
IF `input[type="email"]` THEN
  SET `input[type="email"]` "{{email}}"
END
IF `input[name="phoneNumber"]` THEN
  SET `input[name="phoneNumber"]` "{{phone}}"
END
"""

    def get_submit_script(self) -> str:
        """Return a C4A-Script snippet that clicks submit and waits for the post-apply confirmation modal."""
        return """
CLICK `button.jp-apply-form-submit`
WAIT `[data-test-modal-id="post-apply-modal"]` 15
"""

    def get_success_text(self) -> str:
        """Return the English keyword that confirms a successful LinkedIn Easy Apply submission."""
        return "application"
