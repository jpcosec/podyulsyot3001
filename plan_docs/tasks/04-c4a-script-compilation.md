# Task: Thread → C4AScript compilation (Level 0 execution)

## Explanation
A mature, verified `AriadneThread` can be compiled to a native Crawl4AI `c4ascript` — a standalone script that executes without LangGraph or Python overhead. This is the production artifact of a fully learned mission: Thread → compile → C4AScript → deploy. If the script fails (portal changed, new modal), execution degrades to Level 1 (Theseus/LangGraph).

This is the highest-speed execution mode. Not implementing it means every run pays the LangGraph overhead even for well-known missions.

## Reference
- `docs/reference/external_libs/crawl4ai/c4a_script_reference.md` — C4AScript format reference
- `src/automation/ariadne/thread/thread.py` — `AriadneThread`, source of truth for the transition sequence
- `src/automation/ariadne/thread/action.py` — `TransitionAction`, `PassiveAction`, `ExtractionAction`

## What to fix
Implement a `compile(thread: AriadneThread) -> str` function (or class) that:
1. Walks the `AriadneThread` transition sequence for a given mission
2. Translates each `TransitionAction`/`PassiveAction` to the corresponding C4AScript instruction
3. Returns a valid `.c4a` script string (or writes to file)

Also implement a degradation mechanism: if the compiled script fails at runtime, fall back to Level 1 (LangGraph / `build_graph()`).

## How to do it
- Add `src/automation/ariadne/thread/compiler.py` — single function `compile(thread) -> str`, under 10 lines, delegates to action-specific translators
- Add `src/automation/ariadne/thread/translators.py` — one function per action type mapping to C4AScript syntax
- The degradation wrapper belongs in the entrypoint (CLI or builder), not in the compiler itself

## Depends on
- `AriadneThread` must be in a "sealed" / complete state (all transitions verified)
- C4AScript reference must be read first — see `docs/reference/external_libs/crawl4ai/c4a_script_reference.md`
