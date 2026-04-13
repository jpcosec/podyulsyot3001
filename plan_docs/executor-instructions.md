# Executor Instructions: Issue Fixing and Handoff

As the executor, your role is to solve exactly one assigned issue and hand it back in a reviewable state. You do not clear issue tracking artifacts. You produce a fix, proof, and one traceable commit.

## Mission

You are responsible for:
- reading the assigned issue file and linked context
- implementing the fix
- updating tests and changelog as needed
- creating exactly one resolving commit for that issue
- updating `plan_docs/issues/Index.md` to `{closed with commit id <sha>}` for that issue

You are **not** responsible for deleting the issue file or removing the issue entry from the Index. That is supervisor-only cleanup after phase-level validation.

## Execution Checklist

For every assigned issue, you must complete all of the following:
- [ ] Read the issue file and linked context pills before editing code.
- [ ] Keep the fix scoped to the assigned issue only.
- [ ] Update or delete invalid tests.
- [ ] Add tests where necessary.
- [ ] Run the relevant tests.
- [ ] Verify compliance with `STANDARDS.md`, including all Ariadne laws of physics.
- [ ] Update `changelog.md` with a high-signal entry.
- [ ] Create exactly one resolving commit for the issue.
- [ ] Replace the issue entry in `plan_docs/issues/Index.md` with `{closed with commit id <sha>}`.

## Commit Contract

The resolving commit must follow these rules:
- one closed issue per commit
- the commit message must identify the issue being closed
- do not bundle unrelated fixes into the same commit
- do not create multiple commits for the same close attempt

If you discover extra problems outside the issue scope, do not silently include them. Record them in the issue file or report them for atomization.

## Index Update Contract

After creating the resolving commit, update the exact matching issue entry in `plan_docs/issues/Index.md` to:

`{closed with commit id <sha>}`

Rules:
- use the real commit id you just created
- overwrite only the status for that issue entry
- do not delete the entry
- do not delete the issue file

## Failure Handling

If you cannot complete the issue safely:
- do not fake closure
- do not mark the issue as closed
- leave the issue entry open
- record blockers clearly in the issue file or handoff notes

If review later rejects your fix, the supervisor will revert your commit, enrich the issue with more context, and dispatch a new executor.

## Handoff Output

Your handoff must leave the repository with:
- the code changes for the issue
- relevant tests updated and run
- `changelog.md` updated
- one resolving commit in git
- the issue entry marked `{closed with commit id <sha>}` in `plan_docs/issues/Index.md`
- the issue file still present for supervisor review
