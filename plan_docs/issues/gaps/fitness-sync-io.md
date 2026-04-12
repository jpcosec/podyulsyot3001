# Fitness Function 1: Synchronous I/O Detector

**Explanation:** Protect the Event Loop from synchronous blocking calls (open(), requests.get) inside async LangGraph nodes.

**Reference:** `tests/unit/automation/fitness/test_sync_io_detector.py`

**Status:** Test exists but broken.

**Why it fails:**
1. Detector catches Crawl4AI boot-time I/O (not hot loop)
2. Too sensitive - fails on any sync I/O anywhere
3. LLM node needs API key

**What to fix:**
1. Filter sync calls to only detect during node execution (not setup)
2. Mock LLM node (patches `llm_rescue_agent_node`)
3. Only fail if sync I/O in hot path nodes (observe/execute/heurlistics)

**Steps:**
1. Add markers to distinguish boot vs hot loop
2. Mock LLM node (see fitness-graph-depth)
3. Assert sync calls only in setup phase, not node execution

**Test standard:** Must pass without GOOGLE_API_KEY