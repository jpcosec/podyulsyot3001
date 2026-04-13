# fix-ariadne-io-refactor

## Explanation

The Ariadne I/O cleanup was completed as a follow-up to the Phase 0 fitness gauntlet. The hot loop now depends on a shared async-safe I/O layer, but the work was implemented before a dedicated issue file existed in the phase roadmap.

## Reference

- `src/automation/ariadne/io.py`
- `src/automation/ariadne/repository.py`
- `src/automation/ariadne/capabilities/recording.py`
- `src/automation/ariadne/promotion.py`
- `src/automation/ariadne/graph/orchestrator.py`
- `tests/architecture/test_sync_io_detector.py`

## What to fix

Make Ariadne file access consistent through shared helpers, keep blocking filesystem work out of the graph hot loop, and preserve the Phase 0 architecture guarantees under the real graph fitness tests.

## How to do it

1. Add a shared Ariadne I/O helper module for JSON and JSONL reads/writes.
2. Route recording, promotion, and repository access through that helper layer.
3. Ensure async hot-loop paths offload blocking filesystem and JSON parsing work.
4. Re-run the architecture fitness suite.

## Depends on

- Phase 0 architecture fitness tests
