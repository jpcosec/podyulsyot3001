# Fitness Function 1: Synchronous I/O Detector

**Explanation:** Protect the Event Loop from synchronous blocking calls (open(), requests.get) inside async LangGraph nodes.

**Reference:** `tests/unit/automation/fitness/test_sync_io_detector.py`

**Status:** Test design needs refinement.

**Why it fails:** Catches ALL sync I/O including boot-time (Crawl4AI init), not just hot loop.

**Real fix:** Test should detect only during node execution:
1. Instrument sync I/O detection at node entry/exit
2. Track calls between node_start → node_end markers
3. Fail only if sync I/O in hot path (during node execution)
4. Allow boot-time I/O (before first node)

**Don't:** Fail on any sync I/O anywhere - too strict.

**Steps:**
1. Add time/context markers to distinguish boot vs execution
2. Track only calls during active node execution
3. Use `fitness_test` portal to force multiple nodes
4. Assert no sync I/O during execution (boot OK)

**Note:** Current test technically works - it catches real sync I/O in Crawl4AI.
The question is: is this a bug or expected? 
- If sync I/O in Crawl4AI during crawl → report to motor team
- If only at boot → exclude with markers