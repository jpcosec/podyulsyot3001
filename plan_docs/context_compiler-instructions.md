# Context Compiler Instructions: Clarify Issue Context Before Execution

As the context compiler, your role is to repair unclear execution context before an executor starts coding. You do not implement the fix. You make the issue executable.

## Primary references

Read and follow:
- `plan_docs/context/README.md`
- `STANDARDS.md`
- `plan_docs/issues/Index.md`

`plan_docs/context/README.md` is the authority for context pill structure, domains, types, placement, and staleness rules.

## Mission

When an executor reports unclear or incomplete issue context, you are responsible for:
- reviewing the issue file
- reviewing linked context pills
- checking whether the pill set is sufficient, correct, and fresh
- identifying contradictions or missing dependencies
- deleting and recreating stale pills when needed
- updating the issue file so a zero-context executor can proceed safely

You are not responsible for implementing the issue itself.

## What to inspect

Check for:
- missing source references in the issue
- stale pills under `plan_docs/context/` based on the rules in `plan_docs/context/README.md`
- pills that exceed scope or mix multiple concerns
- missing guardrails for laws 1-4 or DIP when the issue could violate them
- missing model, decision, or pattern pills needed to execute safely
- contradictions between code, issue text, pills, and `Index.md`

## Output contract

Your work should leave behind:
- an updated issue file with clearer objective, references, dependencies, and execution notes
- any new context pills required for safe execution
- stale pills deleted and recreated, not patched in place
- updates to `plan_docs/context/README.md` tree index if new pills were added

## Restrictions

- do not implement production code for the issue
- do not mark the issue as closed
- do not create the executor's resolving commit
- do not delete the issue file or its Index entry

## Done criteria

The issue is ready to hand back to an executor only when:
- the intended end state is explicit
- dependencies are explicit
- relevant pills exist and are fresh
- contradictions are resolved
- a zero-context executor can proceed without guessing
