# Context Pill Audit Guide

Two-phase gate for the issue preparation ritual. **Run Phase A before atomizing issues, Phase B after merging.** Both phases work only from live repo state — never from memory or prior knowledge.

Pills have a `type` field in their frontmatter (`guardrail | decision | pattern | model`). Type governs how pills are routed to issues and what makes them stale. See `plan_docs/context/README.md` for the full format spec.

---

## Phase A — Pre-Atomization: Pill Health Audit

Run before Step 1 (Atomize) of Stage 2 in STANDARDS.md.

### A1 · Inventory

List every file under `plan_docs/context/` (excluding `README.md`). Write them down — every one will be checked.

### A2 · Freshness check (one pill at a time)

Read each pill's frontmatter `type` and `source`, then apply the staleness rule for that type:

| Type | Stale when |
|---|---|
| `guardrail` | `source` file is renamed or deleted; threshold constants in the pill differ from the constants in `source`; the fitness test in `## Verify` no longer exists |
| `decision` | The dependency or API the pill describes is no longer present in `src/`; an ADR in `docs/adrs/` explicitly reverses the decision |
| `pattern` | The function signature, config key, or import path the pill shows has changed in `source` |
| `model` | Any field listed in `## Structure` has been added, renamed, or removed from the `source` file |

For each pill that is stale: **delete it**. Do not patch stale pills in place. Recreate from live source if the concept still applies.

### A3 · Contradiction check

Read all pills in sequence. For any two pills that reference the same rule, threshold, or API:
- Do they agree on the value? (e.g. `agent_failures >= 3` in both)
- Do they agree on the import path?
- If they contradict → keep the one that matches the current `source` file, delete the other.

### A4 · Mandatory coverage check

These pills must always exist. If any is missing, create it from the live source before proceeding. All new pills must follow the format in `plan_docs/context/README.md`.

| File | Type | Source of truth |
|---|---|---|
| `law-1-async.md` | guardrail | `src/automation/ariadne/graph/orchestrator.py` + `tests/architecture/test_sync_io_detector.py` |
| `law-2-single-browser.md` | guardrail | `src/automation/main.py:319` |
| `law-3-dom-hostility.md` | guardrail | `src/automation/ariadne/capabilities/hinting.js:40` |
| `law-4-finite-routing.md` | guardrail | `src/automation/ariadne/graph/orchestrator.py:38` |
| `dip-enforcement.md` | guardrail | `tests/architecture/test_domain_isolation.py` |
| `ariadne-models.md` | model | `src/automation/ariadne/models.py:121` |

---

## Phase B — Post-Atomization: Issue Coverage Audit

Run after Step 3 (Redundant > Merge) of Stage 2 in STANDARDS.md, before Step 6 (Update Index.md).

### B1 · Pill routing by type

Route pills to issues based on what the issue touches. Apply all rows that match.

**Guardrails** — route when the issue could physically violate the constraint:

| Issue touches… | Required pill |
|---|---|
| Any node, heuristic, capability, or graph code | `law-1-async.md` |
| Browser open/close, executor lifecycle, `async with executor` | `law-2-single-browser.md` |
| JS injection, DOM mutation, screenshot capture | `law-3-dom-hostility.md` |
| Routing functions, loops, retries, escalation, circuit breakers | `law-4-finite-routing.md` |
| Any import that crosses the `ariadne/` ↔ `motors/` boundary | `dip-enforcement.md` |

**Models** — route when the issue reads or writes the described structure:

| Issue touches… | Required pill |
|---|---|
| Returning from a node, reading `AriadneState`, writing to `session_memory` | `ariadne-models.md` |

**Decisions / Patterns** — route when the issue works in the architectural layer the pill covers. (No decision or pattern pills exist yet; add them here as they are created.)

Add a `### 📦 Required Context Pills` section to any issue that lacks one. Link only pills that exist on disk.

### B2 · Dangling link check

For every `plan_docs/context/` link in every issue file, verify the target file exists. If it does not:
- Create the missing pill from current source (following the format in `README.md`), or
- Remove the dead link from the issue.

No issue may be dispatched to a subagent with a broken pill link.

### B3 · Zero-context sufficiency check

Ask for each issue: *"Could a fresh agent implement this correctly using only this file and its linked pills?"*

A sufficient issue must contain all of the following. Add any that are absent:

1. **What is wrong** — concrete symptom or missing behaviour, not "it doesn't work."
2. **Reference** — at least one `file_path:line_range` pointing to where the problem lives today.
3. **Real fix** — end state described precisely enough that there is only one correct interpretation.
4. **Steps** — ordered implementation steps, not vague suggestions.
5. **Test command** — exact command to verify the fix, not "write a test."
6. **Constraints section** (`### 🚫 Non-Negotiable Constraints`) — lists only the laws relevant to this issue, inline (not just a link). If a guardrail pill is linked but its rule is not called out explicitly, add it.

### B4 · Constraint vs. code consistency

For each constraint value in an issue, verify against the live `source` file of its pill:
- Threshold numbers (`agent_failures >= 3`, `MAX_HEURISTIC_RETRIES = 2`) must match `orchestrator.py`.
- Import paths and config keys must match `src/`.
- If the issue disagrees with the code → fix the issue's constraint, or open a new gap issue to fix the code.

---

## Audit Report Format

After both phases, produce this report before proceeding to Step 6:

```
PHASE A — Pill Health
  Pills audited:       N
  Pills deleted:       N  [names]
  Pills created:       N  [names]
  Contradictions:      N  [resolutions]

PHASE B — Issue Coverage
  Issues audited:      N
  Pills routed:        N  [issue → pill]
  Broken links fixed:  N
  Sufficiency gaps:    N  [issues patched]
  Constraint fixes:    N  [issue + what changed]

READY FOR EXECUTION: YES / NO
```

If `READY FOR EXECUTION: NO`, list the blockers. Do not proceed to Step 6 of Stage 2 until it is YES.
