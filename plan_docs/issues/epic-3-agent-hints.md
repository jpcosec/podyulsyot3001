# Epic 3: Tuning del Agente de Rescate (Visión + Hints)

**Objective:** The LLM rescue agent must receive an annotated screenshot with Set-of-Mark hint labels already injected — not a raw screenshot. This eliminates CSS hallucinations and reduces token cost by ~20x per agent invocation.

**Priority:** HIGH — without this, the agent is unreliable in production. Resolve any conflict with sub-issues in favor of this epic's objective.

**Contains:**
- [ ] `set-of-mark-observe.md` — call `HintingTool.inject_hints()` inside `observe_node` before the agent screenshot is taken; store hints dict in `session_memory`
- [ ] `hint-failure-fallback.md` — when hint injection fails (CSP/Shadow DOM), fall back to raw DOM tree + coordinate-based clicks

**Execution order:** `set-of-mark-observe` must land first. `hint-failure-fallback` builds on top of it.

**Key constraint:** `HintingToolImpl` requires an `executor` at `__init__` time. In `observe_node`, the executor is available via `config["configurable"]["executor"]`. Instantiate `HintingToolImpl(executor)` inside the node function — do not inject it via config.

**Validation (real browser required):**

```bash
# Force the cascade to reach the agent by using a portal with no matching edges
# then observe whether the screenshot saved in state has [AA]/[AB] labels painted on it
python -m src.automation.main "easy_apply" --portal fitness_test \
  url="https://example.com" --motor crawl4ai
```

Inspect the screenshot stored in `session_memory` or saved to `data/ariadne/recordings/<thread_id>/`. It must show yellow hint labels overlaid on interactive elements.

**Acceptance criteria:**
1. Agent receives a screenshot with `[AA]`/`[AB]` labels visible on buttons and inputs.
2. Agent prompt contains the hints dict (e.g. `{"AA": "button 'Apply'", "AB": "input 'Email'"}`), not the full DOM tree.
3. When hint injection fails (simulate by disabling JS in the executor config), `session_memory["hints_available"]` is `False` and the agent switches to DOM-tree mode without crashing.
4. `python -m pytest tests/architecture/ tests/unit/automation/ -q` still passes green.
