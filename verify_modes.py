from src.automation.ariadne.modes.registry import ModeRegistry
from src.automation.portals.modes.portals import LinkedInMode

def test_registry_resolution():
    url = "https://www.linkedin.com/jobs/view/12345"
    mode = ModeRegistry.get_mode_for_url(url)
    print(f"Resolved mode for {url}: {type(mode).__name__}")
    assert isinstance(mode, LinkedInMode)

    url = "https://www.stepstone.de/jobs/6789"
    mode = ModeRegistry.get_mode_for_url(url)
    print(f"Resolved mode for {url}: {type(mode).__name__}")
    from src.automation.portals.modes.portals import StepStoneMode
    assert isinstance(mode, StepStoneMode)

    url = "https://example.com"
    mode = ModeRegistry.get_mode_for_url(url)
    print(f"Resolved mode for {url}: {type(mode).__name__}")
    from src.automation.ariadne.modes.default import DefaultMode
    assert isinstance(mode, DefaultMode)

if __name__ == "__main__":
    try:
        test_registry_resolution()
        print("Verification SUCCESS")
    except Exception as e:
        print(f"Verification FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
