# CLI Rewrite: Universal Agnostic Engine

**Explanation:** Implement the new universal CLI entrypoint logic (`instruction + --portal + kwargs`) in `main.py` without deleting the old code yet. This allows for a safe, incremental migration of the transport layer.

**Reference:** `src/automation/main.py`

**Status:** Not started.

### 📦 Required Context Pills
- [Universal CLI Pattern](../context/cli-universal-pattern.md)
- [Law 2 — One Browser Per Mission](../context/law-2-single-browser.md)
- [Law 1 — No Blocking I/O](../context/law-1-async.md)
- [Registry Pattern (DIP-Compliant)](../context/registry-pattern.md)
- [Ariadne State & Models](../context/ariadne-models.md)

### 🚫 Non-Negotiable Constraints (Laws of Physics)

1. **Law 1 (No Blocking I/O):** The new CLI entrypoint must be `async`. Use `asyncio.run(run_ariadne(args))`.
2. **Law 2 (One Browser Per Mission):** The `run_ariadne` function MUST wrap the entire graph execution in a single `async with executor` block.
3. **DIP Enforcement:** `main.py` is an infrastructure component. It may import from `ariadne/` and `motors/` to wire them together.

**Real fix:**
1. Implement `parse_kwargs(kwarg_list) -> dict`.
2. Implement `_build_parser()` with the new universal schema: `instruction` (positional), `--portal`, `--motor`, `kwargs` (nargs=*).
3. Implement `run_ariadne(args)` with the universal initial state and `async with executor` wrapper.
4. Update `main()` to use the new `run_ariadne(args)` loop.

**Steps:**
1. Write `parse_kwargs()`.
2. Write new `_build_parser()`.
3. Write `run_ariadne()` with universal initial state and `async with executor` wrapper.
4. Verify the new CLI can start a "discovery" mission on a mapped portal.

**Test command:**
`python -m src.automation.main "easy_apply" --portal linkedin url=https://example.com`
