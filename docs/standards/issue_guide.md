┄Issues Guide — Software Design Cycle

This document defines the pluggable design cycle used to manage and resolve project issues. It
has two stages: Mapping and Indexing.

═══════════════════════════════════════════════════════════════════════════════════════════════

┄┄Stage 1 — Mapping

Produce one .md file per concern under:

• plan_docs/issues/gaps/ — Things that exist but are wrong, inconsistent, or incomplete
  (duplicates, broken contracts, unresolved decisions, placeholders).
• plan_docs/issues/unimplemented/ — Things explicitly designed in contracts, house rules, or
  agent instructions but not yet built.

Each issue file follows this format:

────────────────────
# <Title>

**Explanation:** What is wrong or missing, and why it matters.

**Reference:** File(s) in src/, docs/, or agents/ where the issue lives.

**What to fix:** The concrete end state.

**How to do it:** Suggested implementation path.

**Depends on:** Other issue file path(s) this must wait for, or `none`.
────────────────────

═══════════════════════════════════════════════════════════════════════════════════════════════

┄┄Stage 2 — Initialization Procedure (Indexing)

Before executing any issue or assigning work to a subagent, you MUST perform this ritual. After mapping, run the indexing step before assigning any work. Five operations in order:

 1. Atomize: Break down work into the smallest possible units (see 2.2).
 2. See what's redundant > merge: Scan all issues for overlap (see 2.3).
 3. Legacy > delete: Review each issue for content that should be deleted (see 2.1).
 4. Contradictory > resolve: Produce compatible end states (see 2.3).
 5. Iterate: Repeat these steps until the plan is clean and straightforward.
 6. Update Index.md: Generate the dependency graph (see 2.4, 2.5).
 7. Execute: Execute the plan using the smallest possible/available subagent for each step. Provide the subagent with explicit context (e.g., architectural boundaries, limits, or relevant reference files) to prevent them from making wrong choices. Review their work.

┄┄┄2.1 — Legacy Audit

Review each issue for content that should simply be deleted rather than fixed. If an old
document has no place in the current architecture, record the decision as an ADR in wiki/adrs/
and delete the file. There is no archive folder — that violates Law 1.

┄┄┄2.2 — Atomization

If an issue's "How to do it" section has more than 3–4 distinct steps that could fail
independently, split it into child issues with explicit dependency links between them. The goal
is that each issue can be handed to a subagent as a single, completable unit of work.

┄┄┄2.3 — Contradiction Check

Before drawing dependencies, scan all issues for internal contradictions:

• Overlap: Two issues proposing different fixes to the same file or component. Merge or split
  the scope so ownership is unambiguous.
• Conflict: Two issues whose "What to fix" sections would produce incompatible end states.
  One must be revised or marked as blocked by a design decision.
• Circular dependency: A Depends on: chain that loops back to itself. Break the cycle by
  extracting the shared concern into a new root issue.

Flag any contradiction explicitly in the affected issue files before proceeding to the
dependency graph.

┄┄┄2.4 — Dependency Graph

Map every Depends on: link across all issue files into an explicit directed graph. Identify:

• Roots (no dependencies) — these are the starting phases
• Parallelizable groups — issues with no dependency on each other at the same depth can be
  solved concurrently by parallel subagents
• Blockers — issues that gate multiple downstream items

┄┄┄2.5 — Generate Index.md

Use the dependency graph to produce plan_docs/issues/Index.md from the seed template at wiki/
standards/issues_index_seed.md. This file is the entrypoint for subagents. It must be
regenerated whenever issues are added, split, or resolved.

═══════════════════════════════════════════════════════════════════════════════════════════════

┄┄Lifecycle (Execution Ritual)

Issue files are ephemeral (plan_docs/ lifespan rules apply). Once an issue is solved, the next step is always:

 1. Check whether any existing test is no longer valid and delete it if needed.
 2. Add new tests where necessary.
 3. Run the relevant tests.
 4. Verify compliance: Check that the implementation complies with all project standards and architectural boundaries.
 5. Update changelog.md.
 6. Delete the solved issue from both this index and the corresponding file in plan_docs/issues/.
 7. Make a commit that clearly states what was fixed, making sure all required files are staged.

### Validation-type issues

When resolving a validation-type issue (e.g. "is X working on live portal Y?"), the outcome may be positive or negative. Both cases require follow-up:

- **Positive outcome** — the validation passed. Close the issue normally.
- **Negative or mixed outcome** — the validation failed or exposed unexpected behavior. Do not close silently. Before deleting the validation issue, atomize every uncovered real problem into one or more new gap issues under `plan_docs/issues/gaps/`, then close the validation issue. Each new gap issue must include the observed behavior, evidence paths, likely owning area, and what needs to be fixed.

This ensures validation issues never mask underlying implementation problems.
