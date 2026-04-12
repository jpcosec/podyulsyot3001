# Fitness Function 2: Single Browser Lifecycle

**Explanation:** Protect session persistence - browser must open once and close once per graph session, not per step.

**Reference:** `tests/unit/automation/fitness/test_single_browser.py`

**Status:** Test exists but needs fixing.

**Why it fails:**
1. Graph exits early (goal_achieved) before executor called
2. Map matches immediately → no multi-step flow
3. Test's custom executor ignored by graph

**What to fix:**
1. Use `fitness_test` portal with failing targets
2. Mock LLM node to avoid API key (see fitness-graph-depth)
3. Verify graph runs multiple steps (not just observe → exit)

**Steps:**
1. Create map with 3+ states that all fail
2. Add LLM mock fixture
3. Track enter/exit calls with counter
4. Assert enter==1 and exit==1 after 3+ failed steps

**Test standard:** Must pass without GOOGLE_API_KEY