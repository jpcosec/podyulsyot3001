# Fitness Function 2: Single Browser Lifecycle

**Explanation:** Protect session persistence - browser must open once and close once per graph session, not per step.

**Reference:** `tests/unit/automation/fitness/test_single_browser.py`

**What to fix:** Test that asserts Crawl4AI `__aenter__` called exactly 1 time and `__aexit__` called exactly 1 time.

**How to do it:**
1. Mock Crawl4AI crawler with counter
2. Run multi-step graph flow
3. Assert enter==1 and exit==1

**Depends on:** none