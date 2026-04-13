---
type: pattern
domain: scraping
source: src/automation/ariadne/promotion.py:1
---

# Pill: Promotion Pattern (Recording -> Map)

## Pattern
Promote a session history into a static, reusable `AriadneMap`. This is the "factory" process.

## Steps
1. **Clean**: Remove redundant or back-and-forth navigations.
2. **Generalize**: Replace specific IDs with stable CSS selectors or text matches.
3. **Template**: Replace specific data values with `{{placeholders}}` from the `profile_data`.
4. **Validate**: Run the newly promoted map and verify it completes the mission.

## Implementation
```python
class MapPromoter:
    def promote(self, history: list) -> AriadneMap:
        # Resolve recording to states and edges
        # ...
        return new_map
```

## When to use
Use in Phase 4 "Promotion + canonical map validation".

## Verify
Verify that the `new_map` is a valid JSON that can be loaded by `MapRepository`.
