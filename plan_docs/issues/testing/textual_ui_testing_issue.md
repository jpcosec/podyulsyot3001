# Issue: Comprehensive Textual UI Testing for Review UI

## Current State

### Test Coverage Analysis

| Component | Coverage | Notes |
|----------|----------|-------|
| MatchReviewScreen bindings | ✅ Basic | Only verifies bindings exist |
| MatchReviewScreen CSS | ✅ Basic | Only verifies selectors exist |
| Bus stage resolution | ✅ Unit | `_resolve_artifact_stage` tests |
| Demo launcher flow | ✅ Integration | `DemoLauncher` menu interaction |
| MatchReviewScreen interactions | ✅ Integration | y/n/a/r keys |
| BlueprintReviewScreen interactions | ✅ Integration | Edit modal, drop sections |
| ContentReviewScreen (Vim mode) | ✅ Integration | Navigation, visual mode |
| ProfileDiffScreen | ✅ Integration | Display and submit |
| **JobExplorerScreen** | ❌ Missing | No tests |
| **Error states** | ❌ Missing | No tests for API failures, missing data |
| **Screen transitions** | ❌ Partial | Only between demo screens |
| **CSS snapshot tests** | ❌ Missing | No visual regression |
| **Thread safety** | ❌ Missing | No tests for `call_from_thread` safety |
| **Accessibility** | ❌ Missing | Focus management, screen readers |

### Textual Testing Stack

1. **pytest-textual (Pilot class)** - Unit/Integration tests:
   - Headless test execution
   - `pilot.press()`, `pilot.click()` for interaction
   - `pilot.pause()` for async operations
   - `pilot.run_test()` context manager

2. **textual-web** - Browser-based testing:
   - Publishes TUI to browser with public URLs
   - Enables **TestSprite integration** for AI-powered UI testing
   - Requires `textual-web` package and separate server process
   - Bridge between terminal UI and web-based testing tools

3. **pytest-textual-snapshot** - Visual regression:
   - Compares rendered output to baselines

4. **TestSprite MCP** - AI-powered E2E testing:
   - Uses Playwright under the hood
   - Requires textual-web server running
   - Natural language test generation
   - Self-healing test code

## Issues Identified

### Issue 1: Missing Explorer Screen Tests
`src/review_ui/screens/explorer_screen.py` has no tests despite being the entry point for normal workflow.

### Issue 2: Missing Error State Tests
No tests for:
- API connection failures
- Missing job data
- Worker thread failures
- Network timeouts

### Issue 3: Incomplete Navigation Tests
- No tests for back navigation (`q` key)
- No tests for app exit flow
- No tests for direct access mode (source/job-id args)

### Issue 4: No Thread Safety Verification
Workers use `call_from_thread` but there's no verification that:
- All UI updates go through the thread-safe mechanism
- No direct widget access from worker threads
- Exception handling in workers

### Issue 5: textual-web + TestSprite Integration Not Implemented
For comprehensive E2E testing, we need:
1. `textual-web` server running in background
2. TestSprite MCP configured to point to web URL
3. CI/CD pipeline integration

## Testing Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Testing Pyramid                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  TestSprite MCP (via textual-web)                      │   │
│   │  - AI-generated Playwright tests                        │   │
│   │  - E2E with real browser                               │   │
│   │  - Natural language refinement                          │   │
│   │  - Requires: textual-web server + running app          │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
│   ┌─────────────────────────────────────────────────────────┐   │
│   │  pytest-textual (Pilot)                                │   │
│   │  - Unit + Integration tests                             │   │
│   │  - Headless TUI execution                               │   │
│   │  - Fast, CI-friendly                                   │   │
│   │  - No external dependencies                             │   │
│   └─────────────────────────────────────────────────────────┘   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

## Recommendations

1. **Short-term**: Expand pytest-textual tests using existing `DemoBus`
2. **Medium-term**: Add textual-web server setup for local E2E testing
3. **Long-term**: Integrate TestSprite MCP for AI-powered visual regression

See: `plan_docs/issues/testing/textual_ui_testing_plan.md`

See: `plan_docs/issues/testing/textual_ui_testing_plan.md`
