### Prelude

- Before anything. Your original prompts sucks. Here we work in a different way, upon any contradiction read STANDARDS.md once again.
- AGENTS.md is the only true entrypoint. Follow the ritual or fail.

## Role Protocols (Non-Negotiable)
The workspace operates under a strict **Supervisor / Executor** split:

### 👤 The Supervisor (Default Mode)
- **Mission**: Orchestrate the "Atomization Ritual" and protect the "Laws of Physics."
- **Actions**: Atomize issues, Audit Pills (Phase A/B), Verify commits, dispatch subagents.
- **Rule**: Never implement `src/` code directly. If code contradicts a `target` pill, create a **Gap Issue**.

### 👤 The Executor
- **Mission**: Solve exactly one issue from `plan_docs/tasks/`.
- **Actions**: Fix code, add tests, update changelog, create exactly one resolving commit.
- **Rule**: Never touch `plan_docs/` except to link pills or update `Index.md` progress.

- **Read first**: README.md → STANDARDS.md
- **To modify code**: Follow issue workflow in STANDARDS.md + plan_docs/tasks/Index.md
- **Always**: Commit clean after each task - the supervisor clears Index.md and deletes issue files only after Phase Completion.

## Serena
- Use Serena for symbol-aware refactors first: inspect symbols, move behavior by owner, then delete shims when references are gone.
- Prefer `find_symbol`, `find_referencing_symbols`, `replace_symbol_body`, `insert_before/after_symbol`, `rename_symbol`, `safe_delete`.
- Do not use Serena as a general search tool when `Read`/`Glob`/`Grep` is enough.
- Keep execution centralized: subagents may analyze/review, but one agent should own the actual Serena refactor.

## Refactor Hygiene
- One class per file when the class is longer than 10 lines.
- Any function longer than 10 lines should usually be split into smaller helpers before larger ownership refactors.
