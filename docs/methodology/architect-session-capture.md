# Methodology: Capturing an Architect Session

This document describes the workflow used to extract knowledge from a freeform architecture conversation and turn it into durable, actionable project artifacts. The goal is that after the session, no valuable decision, design, or implementation detail lives only in a chat log.

---

## When to use this

After any architecture or design conversation — with a human, a senior agent, or an external LLM — where:
- Design decisions were made
- Code patterns or reference implementations were discussed
- Invariants or rules were established
- Work was prioritized or sequenced

---

## Step 1 — Topic Extraction

Read the full conversation and identify every distinct topic discussed. For each topic produce a structured entry in this format:

```
#topic {what was discussed}
        {where is the friction point with the current architecture}
        {what needs to be changed}
        [{artifact: start_line | end_line}]
```

At this stage, do not touch any files. Just identify and list. Topics typically fall into one of:
- Architecture decisions (how the system should work)
- Implementation gaps (what's missing or wrong in code)
- Test problems (false positives, wrong scope, missing tests)
- Documentation gaps (things that exist in the chat but nowhere else)

---

## Step 2 — Artifact Classification

For each topic, decide where it belongs:

| Type | Destination |
|---|---|
| Invariant / universal rule | `STANDARDS.md` — permanent, agents always read this |
| Architecture diagram or flow | `docs/ariadne/*.md` — update existing file, don't create new ones unless the topic is truly new |
| Reference implementation (code) | Embed directly in the issue file that describes the work |
| Actionable work item | `plan_docs/issues/<name>.md` |
| Grouped work with validation | `plan_docs/issues/epic-<n>-<name>.md` |

**Key principle:** If a topic produces an artifact (code snippet, diagram, Mermaid chart), that artifact must be embedded where it will be found by the next agent working on the problem — not left only in the chat.

---

## Step 3 — Write Issues

For each implementation gap or test problem, create a file in `plan_docs/issues/`.

A good issue file contains:
- **Explanation** — one paragraph on what is wrong and why it matters
- **Reference** — exact file path and line numbers
- **Status** — not started / partial / false positive / file does not exist
- **Why it's wrong** — the specific failure mode, with code evidence
- **Real fix** — the correct approach (not "do better", but "change line X to Y")
- **Don't** — what approach to avoid and why
- **Steps** — numbered, specific, runnable
- **Reference implementation** — paste the actual code from the conversation if one was provided

Sub-issues (small, atomic) live as standalone files. They get grouped under an epic.

---

## Step 4 — Check for Unclear Implementation Details

After writing the issues, re-read each one and ask: *could a subagent implement this without asking any questions?* If no, the issue is unclear. Common causes:

- References a file or class that doesn't exist yet — say so explicitly and note it must be created first
- References a method by the wrong name — verify against the actual source
- Assumes a pattern that isn't established — add a code example
- Has a dependency that isn't stated — add a "Depends on" line

Fix all unclear issues before moving on.

---

## Step 5 — Capture Diagrams and Conceptual Content into Docs

Diagrams, flows, and explanatory prose from the conversation belong in the `docs/` tree, not in issues. Issues get deleted when work is done; docs persist.

Rules:
- **Update existing files** — check whether a relevant doc already exists before creating a new one
- **Don't duplicate** — if a doc already covers a topic in text, add the diagram to that section rather than creating a parallel file
- **Keep docs honest** — if a doc has an outdated code snippet (e.g. `AriadneState` without the new `instruction` field), update it

---

## Step 6 — Write Universal Laws into STANDARDS.md

If the conversation established invariants — rules that apply to every piece of code, every agent, every future PR — they belong in `STANDARDS.md` as a dedicated section, not in an issue that will be deleted.

A well-written invariant has:
- A one-line rule in a blockquote (`>`)
- **Why** — the exact failure mode if violated
- **Enforced by** — the fitness test or linter that catches violations
- Any allowed exceptions

---

## Step 7 — Group Issues Under Epics

Every issue must have a parent epic. Orphaned issues get missed.

An epic file contains:
- **Objective** — one sentence on what "done" looks like for the group
- **Priority** — epics override sub-issues in conflict resolution
- **Contains** — checklist of sub-issue files
- **Execution order** — what's sequential vs parallel
- **Validation** — a real-browser or real-data test that must pass before the epic closes. CI-only validation is not sufficient if the system touches live portals or LLMs.

Epic naming: `epic-<n>-<slug>.md`, numbered by execution phase.

---

## Step 8 — Verify Full Coverage

Before committing, check that every issue file appears in at least one epic's **Contains** list and in `Index.md`. Run:

```
grep -r "\.md" plan_docs/issues/Index.md | wc -l
ls plan_docs/issues/*.md | grep -v epic | grep -v Index | wc -l
```

The counts should match (accounting for issues nested in epics). Any file not in the index is invisible to subagents.

---

## Step 9 — Update Index.md

The Index is the entrypoint for all subagents. After all issues and epics are written, update it to reflect:

- **Priority convention** — state explicitly that epic issues override sub-issues in conflicts
- **Phases** — group epics by execution phase with dependency notes
- **Parallelization map** — which issues can run concurrently within each phase

---

## Step 10 — Commit

Separate the commit into two if there are both doc/issue changes and test tree changes — they have different scopes and different reviewers care about them.

```
docs: capture <session name> — epics, invariants, and issue backlog
chore: clean test tree — remove obsolete tests, add new tests
```

Stage explicitly by file. Never `git add -A` blindly — check for secrets, generated files, or unintended artifacts.

---

## Common mistakes to avoid

| Mistake | Consequence |
|---|---|
| Leaving reference implementations only in prose | The next agent rewrites from scratch and gets it wrong |
| Creating new doc files for topics already covered | Drift — two sources of truth contradict each other |
| Writing issues without checking current code | Wrong line numbers, wrong method names, wrong assumptions |
| Grouping work in epics without a validation step | "Done" is never defined; epics never close |
| Putting invariants in issues instead of STANDARDS.md | They get deleted when the issue closes |
| Orphaning issues outside any epic | Issues become invisible in the Index |
| Using vague steps like "fix this" | Subagents need specific, runnable instructions |
