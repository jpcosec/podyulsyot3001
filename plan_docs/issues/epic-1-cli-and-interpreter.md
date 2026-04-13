# Epic 1: CLI Semántico y Nodo Intérprete

**Objective:** Make Ariadne fully agnostic. `main.py` must stop knowing what a CV or Job ID is. The graph must start by understanding the user's intent.

**Priority:** HIGH — blocks all other epics. Resolve any conflict with sub-issues in favor of this epic's objective.

**Contains:**
- [ ] `interpreter-node.md` — create `parse_instruction_node`, add `instruction` to `AriadneState`, rewire orchestrator entry point
- [ ] `agent-context-aware.md` — replace hardcoded goal string with `state['instruction']` + `state['current_mission_id']`
- [ ] `cli-rewrite.md` — delete `apply`/`scrape`, replace with universal `instruction + --portal + kwargs`
- [ ] `test-cleanup.md` *(inline task)* — move `tests/unit/automation/fitness/` to `tests/architecture/` and `tests/integration/`; delete any test that mocks what it's supposed to test

**Execution order:** `interpreter-node` → `agent-context-aware` → `cli-rewrite` → test cleanup. The first three can be reviewed as one PR.

**Validation (real browser required):**
Run the following against a live portal after all sub-issues are merged:

```bash
# Exact mission ID — fast path, no LLM call on interpreter
python -m src.automation.main "easy_apply" --portal stepstone url="https://stepstone.de/..."

# Natural language — slow path, Gemini resolves mission
python -m src.automation.main "aplica a este trabajo con mi cv" --portal stepstone \
  url="https://stepstone.de/..." cv_path=./cv.pdf

# Discovery
python -m src.automation.main "busca 5 trabajos de Python" --portal stepstone limit=5
```

**Acceptance criteria:**
1. All three commands reach `observe_node` with correct `current_mission_id` in state.
2. No `--cv` or `--job-id` flags anywhere in the CLI.
3. `python -m pytest tests/unit/automation/ tests/architecture/ -q` passes green.
4. No fitness tests live under `tests/unit/`.
