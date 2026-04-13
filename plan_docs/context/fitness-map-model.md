---
type: model
domain: ariadne
source: src/automation/portals/fitness_test/maps/easy_apply.json
---

# Pill: Fitness Test Portal Map (Schema)

## Structure
A minimal, valid JSON map for testing failure cascades and circuit breakers. Place at `src/automation/portals/fitness_test/maps/easy_apply.json`.

## Implementation
```json
{
  "meta": { "source": "fitness_test", "flow": "easy_apply", "version": "1.0" },
  "states": {
    "start": { "url_contains": "example.com", "required_elements": [] }
  },
  "edges": [
    {
      "from_state": "start",
      "to_state": "terminal",
      "mission_id": "easy_apply",
      "intent": { "action": "click", "goal": "Apply" },
      "target": { "css": "#element-that-does-not-exist" }
    }
  ],
  "success_states": ["terminal"]
}
```

## When to use
Use in Phase 0 and Phase 2 fitness/smoke tests to ensure the map loads correctly and the executor fails deterministically.

## Verify
Verify that `MapRepository().get_map_async("fitness_test")` loads this JSON without error.
