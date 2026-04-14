# instructions/

Role instructions for agents operating in this workspace.

| File | Role |
|---|---|
| [`supervisor-instructions.md`](supervisor-instructions.md) | Supervisor — orchestration, gatekeeping, phase sign-off |
| [`executor-instructions.md`](executor-instructions.md) | Executor — issue implementation and handoff |
| [`context_compiler-instructions.md`](context_compiler-instructions.md) | Context Compiler — clarifying issue context before execution |
| [`context-pill-audit.md`](context-pill-audit.md) | Pill audit process — pre/post-atomization gate |

---

## Rule: No repo-specific content in this folder

Every file here describes **how a role works**, not **what this repo contains**.

File paths, module names, class names, threshold values, test commands, and architecture details **must not appear here**. They belong in:

- `STANDARDS.md` — coding rules and laws
- `AGENTS.md` — repo architecture, open work, test command
- `docs/` — design and reference documentation

The only exception is references to structural paths that are part of the workflow itself (`plan_docs/tasks/Index.md`, `plan_docs/context/`, `instructions/`). Those are workflow infrastructure, not repo specifics.

If you find a repo-specific detail in one of these files, move it to the appropriate doc and replace it with a pointer.
