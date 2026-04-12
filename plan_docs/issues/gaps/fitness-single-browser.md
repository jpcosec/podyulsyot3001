# Fitness Function 2: Single Browser Lifecycle

**Explanation:** Protect session persistence - browser must open once and close once per graph session, not per step.

**Reference:** `tests/unit/automation/fitness/test_single_browser.py`

**Status:** Test design is wrong - needs redesign.

**Why it fails:** Test uses custom fake executor but graph ignores it. Real flow needed.

**Real fix:** Test should verify real browser lifecycle:
1. Use `fitness_test` portal with failing targets (forces multiple steps)
2. Real executor (Crawl4AI) tries and fails on missing elements
3. LLM fails (no API key or error)
4. Graph loops but browser should open ONCE, close ONCE
5. Track real `__aenter__`/`__aexit__` calls

**Don't:** Mock executor - defeats purpose of testing browser lifecycle.

**Steps:**
1. Use `fitness_test` portal with 3+ failing states
2. Pass real `Crawl4AIExecutor` to config
3. Instrument executor with counter (or check via mock at integration level)
4. Assert browser enters once, exits once
5. Even after 10+ failed steps

**API Key:** Requires GOOGLE_API_KEY or skip in CI without key