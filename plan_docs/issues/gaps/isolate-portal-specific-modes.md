# Isolate: Portal-Specific Modes from Ariadne Core

**Explanation:** Currently, `LinkedInMode`, `StepStoneMode`, and their respective JSON configurations live inside `src/automation/ariadne/modes/`. This violates the Isolation Boundary: the Ariadne core (the semantic engine) should not contain implementation details for specific websites.

**Reference:** 
- `src/automation/ariadne/modes/portals.py`
- `src/automation/ariadne/modes/configs/`

**What to fix:** Move all portal-specific class implementations and configuration files out of the `ariadne` package to restore its role as a pure, portal-agnostic orchestrator.

**How to do it:**
1.  Move `portals.py` and the `configs/` directory to `src/automation/portals/` or a dedicated `portal_infrastructure` area.
2.  Update the `ModeRegistry` to perform dynamic discovery/loading of these modes from the external location.
3.  Ensure `src/automation/ariadne/modes/` only contains the `AriadneMode` interface and the `DefaultMode` fallback.

**Depends on:** none
