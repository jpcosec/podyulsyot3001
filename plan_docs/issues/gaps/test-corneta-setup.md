# Setup: Test Corneta (E2E Validation)

**Explanation:** After massive refactors, need a quick dirty E2E test to validate LangGraph cascade works: Observe -> Determinista -> Heurísticas -> LLM Rescue -> Circuit Breaker -> HITL.

**Reference:** See detailed spec in the conversation

**What to fix:**
1. Create `src/automation/portals/example/maps/test_cascade.json` - trap map pointing to non-existent button
2. Create `scripts/test_corneta.py` - test script that runs full cascade on example.com
3. Run test and verify HITL breakpoint is reached

**How:** See user's 5-minute setup instructions

**Depends on:** none