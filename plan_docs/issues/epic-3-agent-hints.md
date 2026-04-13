# Epic 3: Tuning del Agente de Rescate (Visión + Hints)

**Umbrella:** depends on `ariadne-oop-skeleton.md`.

**Objective:** `Delphi` must receive an annotated screenshot with Set-of-Mark hint labels already injected by `Theseus`/`Sensor` — not a raw screenshot. This eliminates CSS hallucinations and reduces token cost by ~20x per rescue invocation.

**Priority:** HIGH — without this, the agent is unreliable in production. Resolve any conflict with sub-issues in favor of this epic's objective.

**Contains:**
- [ ] `som-hint-injection.md` — `Theseus` drives `HintingCapability` after `Sensor.perceive()`
- [ ] `som-agent-prompt-update.md` — `Delphi` consumes the hint dictionary from state
- [ ] `hint-failure-fallback.md` — degradation path when hint injection fails

### 📦 Required Context Pills
- [Law 1 - No Blocking I/O](../context/law-1-async.md)
- [Law 3 - DOM Hostility](../context/law-3-dom-hostility.md)
- [Law 4 - Finite Routing](../context/law-4-finite-routing.md)
- [Node Implementation Pattern](../context/node-pattern.md)
- [Set-of-Mark (SoM) Pattern](../context/som-pattern.md)

### 🚫 Non-Negotiable Constraints
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
- **Law 3 (DOM Hostility):** All JS injection must use an isolated overlay. Do not mutate existing DOM nodes or event listeners.
- **Law 4 (Finite Routing):** All loops must have finite circuit breakers. Escalation through counters (heuristic_retries >= 2, agent_failures >= 3) to HITL is mandatory.
