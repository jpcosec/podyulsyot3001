---
type: pattern
domain: ariadne
source: plan_docs/design/ariadne-oop-architecture.md:96
---

# Pill: Actor Pattern

## Pattern
Ariadne graph behavior is split across injected callable actors with clear boundaries:
- `Theseus`: deterministic, low-cost execution
- `Delphi`: rescue/exploration when deterministic routing fails
- `Recorder`: assimilation of executed behavior back into memory

Each actor owns one job and collaborates through injected interfaces instead of hidden config wiring.

## Implementation
```python
teseo = Theseus(sensor=adapter, motor=adapter, labyrinth=labyrinth, thread=thread)
delfos = Delphi(sensor=adapter, motor=adapter, llm_client=llm)
recorder = Recorder(labyrinth=labyrinth, thread=thread)

workflow.add_node("teseo", teseo)
workflow.add_node("delfos", delfos)
workflow.add_node("recorder", recorder)
```

## When to use
Use when adding or refactoring graph-time execution logic, especially when deciding which responsibility belongs in deterministic execution, rescue reasoning, or learning/assimilation.

## Verify
Check that:
- `Theseus` does not own LLM rescue logic
- `Delphi` does not own topology or mission memory mutation rules
- `Recorder` does not decide the next action, only records and assimilates outcomes
