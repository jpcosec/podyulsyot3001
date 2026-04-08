# BrowserOS Level 2 Promotion Hardening

**Explanation:** Level 2 BrowserOS traces can already be promoted into draft replay paths, but only for the simplest deterministic cases. The current logic is too shallow to trust for broader portal drift recovery or first-time flow discovery.

**Reference:** `src/automation/motors/browseros/agent/openbrowser.py`, `src/automation/motors/browseros/agent/normalizer.py`, `src/automation/motors/browseros/agent/promoter.py`, `tests/unit/automation/motors/browseros/agent/`

**What to fix:** Make Level 2 promotion robust enough to support stable draft Ariadne paths across realistic BrowserOS-discovered flows.

**How to do it:** 1. Support multi-action step grouping and better filtering of non-replayable BrowserOS tools. 2. Improve target/value inference for fill, select, upload, submit, and keyboard-driven flows. 3. Add promotion confidence rules so only deterministic-enough paths are promoted automatically. 4. Add regression tests covering partial, blocked, and promotable Level 2 traces.

**Depends on:** `plan_docs/issues/unimplemented/browseros-shared-promotion-intermediate.md`
