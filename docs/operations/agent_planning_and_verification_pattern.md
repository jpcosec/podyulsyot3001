# Agent Planning and Verification Pattern

This document preserves the useful parts of the former local `.sisyphus/` workspace without keeping agent scratch files in the repository.

## What To Preserve

- Use an explicit planning document before large UI or workflow changes.
- Split work into dependency-aware waves instead of one long task list.
- Define verification per task, not only at the end.
- Keep final review gates separate from implementation tasks.
- Store durable project guidance in `docs/` or `plan/`, not in local agent scratch folders.

## Recommended Plan Shape

Use this structure for substantial implementation plans:

1. `TL;DR`
2. `Context`
3. `Work objectives`
4. `Must have / must not have`
5. `Verification strategy`
6. `Execution waves`
7. `Dependency matrix`
8. `Task checklist`
9. `Final verification wave`

## Execution Pattern

- Group independent work into parallel waves.
- Mark blockers explicitly.
- Keep each task narrow enough to verify in isolation.
- Add a final audit wave after implementation for compliance, code quality, and end-to-end QA.

## Verification Pattern

Each significant task should include:

- the scenario being verified
- the tool/command used
- exact steps
- expected result
- durable evidence location when the evidence belongs in the repo

Preferred verification order:

1. targeted unit or slice tests
2. build/type-check
3. browser or operator flow validation for UI/runtime behavior
4. final end-to-end sanity check

## Evidence Policy

- Keep durable docs, specs, and runbooks in `docs/` or `plan/`.
- Keep ephemeral screenshots, logs, drafts, and agent session state out of the repo.
- If a screenshot or log is worth preserving long-term, move it intentionally to a documented location and reference why it matters.

## Planning Guidance For UI/Sandbox Work

- Preserve behavioral contracts before restyling.
- Document interaction rules as acceptance criteria.
- Prefer realistic browser validation over synthetic assertions when UI behavior is the core risk.
- Record how to run and verify the slice in `changelog.md` or the relevant doc after completion.

## Repository Rule

Agent-local workspaces such as `.sisyphus/` should remain untracked. Any reusable planning or testing method must be promoted into normal repository documentation.
