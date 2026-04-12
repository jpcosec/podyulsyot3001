# Ariadne 2.0: Portals & Modes (Nyxt Pattern)

## 1. The Mode Pattern
Ariadne 2.0 adopts the **Nyxt Mode Pattern** to handle portal-specific logic without polluting the domain core. A "Mode" is a set of contextual rules and heuristics injected into the graph based on the current URL.

### AriadneMode Interface
Every mode implements these capabilities:
- `normalize_job(payload)`: Portal-specific cleanup (replaces old God functions).
- `inspect_danger(snapshot)`: Custom detection for portal-specific security blocks.
- `apply_local_heuristics(state)`: Rules for patching broken selectors (e.g. "Apply" vs "Quick Apply").

### Implementations
- **`DefaultMode`**: Uses LLMs for all interpretations. Low speed, high cost, high intelligence.
- **`PortalMode` (e.g. `StepStoneMode`)**: Uses local regex and rule files. High speed, zero cost, deterministic.

## 2. Portal Definitions
Portals are packages of domain knowledge.

```python
class PortalDefinition(BaseModel):
    source_name: str
    base_url: str
    capabilities: PortalCapabilities
    routing: PortalRoutingConfig # Logic to choose between flows
```

### Routing Logic
Given a job URL, the portal definition determines the appropriate starting state and mode:
- ** outcome: `apply`**: Use an onsite deterministic graph.
- ** outcome: `external_ats`**: Reroute to the Agent for free exploration.

## 3. Heuristic Externalization
Hardcoded strings (e.g., `vollzeit`, `gmbh`) are strictly forbidden in Python code. They must live in YAML/JSON rule files scoped to each Mode. The `ApplyLocalHeuristics` node loads these rules JIT.
