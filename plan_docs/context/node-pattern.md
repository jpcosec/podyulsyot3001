---
type: pattern
domain: ariadne
source: plan_docs/design/ariadne-oop-architecture.md:96
---

# Pill: Node Implementation Pattern

## Pattern
LangGraph nodes should be callable actor objects with injected dependencies. Prefer `class Actor: async def __call__(self, state) -> dict` over free functions when the node needs `Sensor`, `Motor`, memory objects, or collaborators.

## Implementation
```python
class Theseus:
    def __init__(self, sensor, motor, labyrinth, thread):
        self.sensor = sensor
        self.motor = motor
        self.labyrinth = labyrinth
        self.thread = thread

    async def __call__(self, state: dict) -> dict:
        snapshot = await self.sensor.perceive()
        room_id = self.labyrinth.identify_room(snapshot)
        command = self.thread.get_next_step(room_id)
        return await self.motor.act(command)
```

## When to use
Use for new Ariadne actors such as `Theseus`, `Delphi`, and `Recorder`.

## Verify
Ensure the actor is injected into the graph as a callable instance and returns a partial state dict.
