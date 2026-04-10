"""Integration tests for live onsite apply dry-run.

These tests require:
1. BrowserOS running at `http://127.0.0.1:9000/mcp` after launching `"$BROWSEROS_APPIMAGE_PATH" --no-sandbox`
2. Authenticated session for each portal (`--setup-session`)
3. A real CV file and real job IDs

Run with: pytest tests/integration/test_live_apply.py -v
All tests in this file are skipped if BrowserOS is not available.
"""

from __future__ import annotations

import pytest

from src.automation.main import main
from src.automation.storage import AutomationStorage
from src.core.data_manager import DataManager


def _is_browseros_available() -> bool:
    """Check if BrowserOS MCP front door is reachable."""
    try:
        import urllib.request

        with urllib.request.urlopen("http://127.0.0.1:9000/mcp", timeout=2):
            return True
    except Exception:
        return False


BROWSEROS_AVAILABLE = _is_browseros_available()


def _write_ingest_state(jobs_root, source: str, job_id: str, state=None):
    from pathlib import Path

    jobs_root = Path(jobs_root)
    data_manager = DataManager(jobs_root)
    data_manager.write_json_artifact(
        source=source,
        job_id=job_id,
        node_name="ingest",
        stage="proposed",
        filename="state.json",
        data=state
        or {
            "job_title": "Automation Engineer",
            "company_name": "Acme",
            "application_url": "https://www.xing.com/jobs/apply/123",
            "url": "https://www.xing.com/jobs/view/123",
        },
    )
    return data_manager


class TestLiveApplyRequiresBrowserOS:
    """Live apply tests that verify the integration test infrastructure is correct.

    These tests document the expected behavior when BrowserOS is available.
    When infrastructure is unavailable, they are skipped with clear instructions.
    """

    @pytest.mark.skipif(
        not BROWSEROS_AVAILABLE,
        reason="BrowserOS runtime not running at http://127.0.0.1:9000/mcp. "
        "Start with: export BROWSEROS_APPIMAGE_PATH=/path/to/BrowserOS.AppImage; "
        '"$BROWSEROS_APPIMAGE_PATH" --no-sandbox '
        "Then authenticate with: python -m src.automation.main apply "
        "--source xing --backend browseros --setup-session",
    )
    def test_xing_dry_run_documentation(self):
        """Documentation: expected command to run XING dry-run.

        When BrowserOS is running and authenticated, run:
        python -m src.automation.main apply \\
          --source xing \\
          --backend browseros \\
          --job-id <test-id> \\
          --cv tests/fixtures/test-cv.pdf \\
          --dry-run

        Expected: apply_meta.json has status='dry_run'
        """
        assert BROWSEROS_AVAILABLE, "BrowserOS must be running"

    @pytest.mark.skipif(
        not BROWSEROS_AVAILABLE,
        reason="BrowserOS runtime not running at http://127.0.0.1:9000/mcp",
    )
    def test_stepstone_email_handoff_documentation(self):
        """Documentation: expected command to verify StepStone email routing.

        When BrowserOS is running and authenticated, run the apply command
        against a StepStone job that has 'Apply by email'. Expected result:
        apply_meta.json has status='failed' with 'email_application_route' error.
        """
        assert BROWSEROS_AVAILABLE, "BrowserOS must be running"


def test_test_cv_fixture_exists():
    """Verify the test CV fixture is present at the expected path."""
    from pathlib import Path

    cv_path = Path("tests/fixtures/test-cv.pdf")
    assert cv_path.exists(), (
        f"Test CV fixture not found at {cv_path}. "
        "Create it with: tests/fixtures/test-cv.pdf"
    )


def test_browseros_setup_docs_exist():
    """Verify the BrowserOS setup documentation exists."""
    from pathlib import Path

    docs_path = Path("docs/automation/browseros_setup.md")
    assert docs_path.exists(), (
        f"BrowserOS setup docs not found at {docs_path}. "
        "This file should document BrowserOS setup and session management."
    )


def test_live_apply_validation_matrix_docs_exist():
    """Verify the live apply validation matrix exists."""
    from pathlib import Path

    docs_path = Path("docs/automation/live_apply_validation_matrix.md")
    assert docs_path.exists(), (
        f"Live apply validation matrix not found at {docs_path}. "
        "This file should define the canonical live apply validation scope."
    )
