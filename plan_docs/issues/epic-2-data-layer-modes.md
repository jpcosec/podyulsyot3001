# EPIC 2: Data Layer & Portal Modes (The Stupid Brain)

**Explanation:** Move from linear path arrays to directed state graphs and externalize heuristic rules into URL-contextual "Modes."

**Tasks:**
1.  **Refactor Models**: Update `models.py` to replace `AriadnePath` (list) with `AriadneMap` (directed graph of nodes and edges).
2.  **Mode Registry**: Implement the `ModeRegistry` to inject URL-based configurations (e.g., `LinkedInMode`, `StepStoneMode`).
3.  **Heuristic Extraction**: Move all "magic strings" (e.g., "vollzeit", "gmbh") from `job_normalization.py` and `danger_detection.py` into external YAML/JSON mode files.
4.  **Blackboard Memory**: Define the `AriadneState` TypedDict to serve as the single source of truth for working memory.

**Success Criteria:**
- No hardcoded portal-specific strings exist in the core Ariadne code.
- Portal behavior is configurable via static files without code changes.

**Depends on:** `epic-1-fitness-functions.md`
