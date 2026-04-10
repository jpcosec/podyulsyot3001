# Refactor CLI `main.py` to prevent "Big Ball of Mud"

**Explanation:** `src/cli/main.py` has grown to ~600 lines. It contains multiple sub-command parsers, orchestration logic, and direct implementation details (like `_sync_profile_if_needed`, `_run_pipeline`, etc.). This violates the "No file does two things" rule and makes it hard to maintain, test, and extend. It is effectively a "time-bomb" for future complexity.

**Reference:** `src/cli/main.py`

**What to fix:** A clean, modular CLI entry point. Implementation logic should be extracted to dedicated command handlers or a CLI coordinator class. The `main.py` should only handle parsing and routing.

**How to do it:**
1. Extract sub-command logic (`_run_pipeline`, `_run_batch`, etc.) into a `src/cli/commands/` package.
2. Each command should live in its own file (e.g., `src/cli/commands/pipeline.py`).
3. Convert the parser building and execution into a more modular structure where commands register themselves.
4. Ensure each command handler follows the pattern: `validate inputs -> call core/ai logic -> format output`.

**Depends on:** none
