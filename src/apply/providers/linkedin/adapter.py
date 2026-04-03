"""LinkedIn Easy Apply adapter.

Selector discovery: inspect tests/fixtures/apply/linkedin_apply_modal.html
  - Prefer data-test-* attributes over generated class names (more stable)
  - Revalidate selectors against current portal fixtures when LinkedIn changes its UI

C4A-Script docs: https://docs.crawl4ai.com/core/c4a-script/
"""

from __future__ import annotations

from pathlib import Path

from src.apply.models import FormSelectors
from src.apply.smart_adapter import ApplyAdapter


class LinkedInApplyAdapter(ApplyAdapter):
    """Adapter for LinkedIn Easy Apply inline application flow."""

    @property
    def source_name(self) -> str:
        """Return the canonical provider key for LinkedIn apply."""
        return "linkedin"

    def _get_portal_base_url(self) -> str:
        return "https://www.linkedin.com"

    def get_session_profile_dir(self) -> Path:
        """Return the persistent browser profile directory for LinkedIn."""
        return Path("data/profiles/linkedin_profile")

    def get_form_selectors(self) -> FormSelectors:
        """Return the selectors used for the LinkedIn Easy Apply modal."""
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
        """Return the C4A-Script that opens the LinkedIn apply modal."""
        return """
IF NOT `[data-test-modal-id="apply-modal"]` THEN
  CLICK `button.jobs-apply-button`
  WAIT `[data-test-modal-id="apply-modal"]` 10
END
"""

    def get_fill_form_script(self, profile: dict) -> str:
        """Return the C4A-Script that fills LinkedIn contact fields.

        Args:
            profile: Placeholder mapping used by the shared adapter renderer.

        Returns:
            A script template containing profile placeholders.
        """
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
        """Return the C4A-Script that submits the LinkedIn application."""
        return """
CLICK `button.jp-apply-form-submit`
WAIT `[data-test-modal-id="post-apply-modal"]` 15
"""

    def get_success_text(self) -> str:
        """Return text expected on the post-submit confirmation surface."""
        return "Application"
