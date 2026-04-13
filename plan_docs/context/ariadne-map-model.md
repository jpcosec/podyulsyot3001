---
type: model
domain: ariadne
source: src/automation/ariadne/models.py:1
---

# Pill: Ariadne Map Model (Full Schema)

## Structure
The `AriadneMap` is a static directed graph of states (`AriadneObserve`) and transitions (`AriadneEdge`).

### Components
- `AriadneObserve`: Predicate to identify a JIT state (URL + DOM elements).
- `AriadneEdge`: Condition to move between states (`intent`, `target`, `value`).
- `AriadneTarget`: Exact selector/text to find an element.

## Usage
Used by `MapRepository` to load JSON maps and by the deterministic node to find the next action.

```python
# MapRepository.get_map(portal) returns an AriadneMap instance
ariadne_map = await repo.get_map_async("linkedin")
for edge in ariadne_map.edges:
    if edge.from_state == current_state:
        # Match found!
```

## Verify
Validate with `pydantic.ValidationError` on any JSON map under `src/automation/portals/`.
