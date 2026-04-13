# Ariadne I/O Layer and Tests

### 1. Explanation
 Ariadne now has a shared I/O layer in `src/automation/ariadne/io.py`, but the roadmap still lacks a dedicated follow-up issue that treats the module plus its hot-loop guarantees as a first-class concern. We need an explicit issue that keeps future recording, promotion, repository, and graph changes aligned with the async I/O contract.

### 2. Reference
 `src/automation/ariadne/io.py`, `src/automation/ariadne/repository.py`, `src/automation/ariadne/capabilities/recording.py`, `src/automation/ariadne/promotion.py`, `src/automation/ariadne/graph/orchestrator.py`, `tests/architecture/test_sync_io_detector.py`

### 3. Real fix
 Treat the shared Ariadne I/O layer as the canonical path for JSON and JSONL persistence, and expand regression coverage so future edits cannot reintroduce blocking I/O or bypass the helper layer in graph-time code.

### 4. Steps

1. Audit Ariadne modules for direct JSON/JSONL reads and writes that should route through `src/automation/ariadne/io.py`.
2. Add or update unit tests around helper behavior, especially async path handling and missing-file semantics.
3. Keep the architecture fitness coverage green, especially `tests/architecture/test_sync_io_detector.py`.
4. Update any stale docs or context pills that describe recording/promotion persistence without the shared I/O layer.

**Depends on:** `recording-promoter-guard.md`, `law-1-async.md`, `recording-pattern.md`

### 📦 Required Context Pills
- [Ariadne Shared I/O Pattern](../context/ariadne-io-pattern.md)
- [Law 1 - No Blocking I/O](../context/law-1-async.md)
- [Promotion Pattern (Recording -> Map)](../context/promotion-pattern.md)
- [Graph Recording Pattern](../context/recording-pattern.md)

### 🚫 Non-Negotiable Constraints
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
