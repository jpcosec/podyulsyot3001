# Ariadne 2.0: Fitness Functions & Error Taxonomy

## 1. Architectural Fitness Functions (Guardrails)
To prevent architectural drift, Ariadne 2.0 uses automated "Fitness Functions" that break the build if design principles are violated.

### Category A: Static Architecture (Linter)
- **Dependency Wall**: Prohibits Ariadne (Domain) from importing Motors (Infrastructure) via `pytest-archon`.
- **Dumb Executors**: Ensures Executors do not import domain models like `AriadneMap`.
- **Strict Typing**: Mypy/Pyright enforce that Executors only receive primitive commands.

### Category B: I/O Isolation
- **Clean Room**: Uses `pyfakefs` to ensure Ariadne nodes cannot read the disk directly. They must use the `MapRepository`.

### Category C: Business Logic (Mode Blindness)
- **Blindness by Default**: Tests that confirm the core normalization logic returns empty results if no `PortalMode` configuration is injected. No magic strings in Python.

### Category D: Graph Topology (Routing)
- **Fallback Escalation**: Validates that conditional edges correctly route from Deterministic Failure → Heuristics → LLM Agent → HITL.
- **Circuit Breaker**: Ensures the graph aborts to HITL after N consecutive Agent failures.

## 2. Error Taxonomy
Higher layers only catch Ariadne-neutral errors. Motors must wrap their internal errors.

| Error | Cause |
|---|---|
| `TranslationError` | Intent could not be compiled to JIT command. |
| `ObservationFailed` | Current UI state could not be identified. (Triggers LLM Rescue). |
| `TargetNotFound` | Executor could not find the resolved target on page. |
| `EdgeActivationFailed` | Condition for a graph transition was not met. |
| `ReplayAborted` | Intentional stop (Human abort or dry-run). |

## 3. Motor Error Wrapping
All motor-specific exceptions (e.g. `PlaywrightError`, `Crawl4AIError`) must be caught at the executor boundary and re-raised as the appropriate Ariadne error with full context (state_id, edge, target).
