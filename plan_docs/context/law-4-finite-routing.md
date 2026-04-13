---
type: guardrail
law: 4
domain: ariadne
source: src/automation/ariadne/graph/orchestrator.py:38
---

# Pill: Law 4 — Finite Routing

## Rule
All cyclic paths must have bounded counters that escalate through the cascade and terminate at HITL. Never loop without a counter.

## Escalation path (thresholds from `orchestrator.py:38`)
```
Observe → ExecuteDeterministic
  └─ fails → ApplyLocalHeuristics
       └─ heuristic_retries >= 2  → LLMRescueAgent
            └─ agent_failures >= 3 → HumanInTheLoop  ← terminal
```

## ❌ Forbidden
```python
def route(state):
    if state["errors"]:
        return "heuristics"  # no counter → infinite loop
```

## ✅ Correct
```python
# mirrors orchestrator.py:580-596
def route_after_heuristics(state):
    retries = state.get("session_memory", {}).get("heuristic_retries", 0)
    if state.get("errors") or retries >= 2:
        return "llm_rescue_agent"
    return "observe"

def route_after_agent(state):
    mem = state.get("session_memory", {})
    if state.get("errors") or mem.get("give_up") or mem.get("agent_failures", 0) >= 3:
        return "human_in_the_loop"
    return "observe"
```

## Verify
```bash
python -m pytest tests/architecture/test_graph_depth.py -q
```
