# 00 - Scope And Survivors

## Keep
- Pydantic contracts in node contract modules.
- LangGraph topology reference in `src/graph.py`.
- Deterministic tools (to be consolidated under `src/tools/`).
- Historical successful artifacts under `data/Archived/` for expected behavior references.

## Delete
- LLM runtime wrappers and adapters.
- Prompt execution stack from the old runtime path.
- Legacy node logic implementations.
- Legacy review parser implementation.
- Old custom state-management runtime glue.

## Exit Criteria
- Survivors map is explicit and path-based.
- Delete list is explicit and path-based.
