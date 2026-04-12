# Refactor: Isolate Translators from Ariadne Core

**Explanation:** Currently, the `BrowserOSTranslator` and `Crawl4AITranslator` implementations reside within `src/automation/ariadne/translators/`. This violates the strict isolation principle, as the Ariadne core package contains code that knows about the specific command formats of external motors.

**Reference:** 
- `src/automation/ariadne/translators/`
- `plan_docs/ariadne/execution_interfaces.md`

**What to fix:** Move the motor-specific translator implementations out of the `ariadne` package to restore its role as a pure, infrastructure-agnostic domain.

**How to do it:**
1.  Create a new package, e.g., `src/automation/adapters/translators/`.
2.  Move the `browseros.py` and `crawl4ai.py` translator implementations to the new package.
3.  `src/automation/ariadne/translators/` should now only contain the abstract `base.py`.
4.  Update the `TranslatorRegistry` to dynamically discover and load these external translators, similar to how the `ModeRegistry` works.

**Depends on:** none
