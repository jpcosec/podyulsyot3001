"""StepStone C4AI apply translator — consumes STEPSTONE_APPLY portal intent."""
from __future__ import annotations

from pathlib import Path

from src.automation.motors.crawl4ai.apply_engine import ApplyAdapter
from src.automation.motors.crawl4ai.models import FormSelectors
from src.automation.portals.stepstone.apply import STEPSTONE_APPLY


class StepStoneApplyAdapter(ApplyAdapter):
    """C4AI apply adapter for StepStone Easy Apply."""

    portal = STEPSTONE_APPLY

    @property
    def source_name(self) -> str:
        return self.portal.source_name

    def _get_portal_base_url(self) -> str:
        return self.portal.base_url

    def get_session_profile_dir(self) -> Path:
        return Path("data/profiles/stepstone_profile")

    def get_form_selectors(self) -> FormSelectors:
        return FormSelectors(
            apply_button="[data-at='apply-button']",
            cv_upload="input[type='file']",
            submit_button="[data-at='submit-button']",
            success_indicator="[data-at='application-success']",
            first_name="input[name='firstName']",
            last_name="input[name='lastName']",
            email="input[type='email']",
            phone="input[name='phone']",
            letter_upload=None,
            cv_select_existing=None,
        )

    def get_open_modal_script(self) -> str:
        return """
IF NOT `[data-at="apply-modal"]` THEN
  CLICK `[data-at="apply-button"]`
  WAIT `[data-at="apply-modal"]` 10
END
"""

    def get_fill_form_script(self, profile: dict) -> str:
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
        return """
CLICK `[data-at="submit-button"]`
WAIT `[data-at="application-success"]` 15
"""

    def get_success_text(self) -> str:
        return "Bewerbung"
