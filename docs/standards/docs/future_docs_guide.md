# 🔭 future_docs — User Guide

`future_docs/` is a local folder at the repo root that holds deferred work: problems that are real but not being solved now, features that are wanted but not planned, and hardening that is postponed pending more pressing work.

It is **not** a graveyard. Items here should be findable, linkable, and promotable to active plans.

---

## What belongs here

| Belongs in `future_docs/` | Does NOT belong here |
|---|---|
| A known architectural problem with a clear description | A vague "we should improve X someday" note |
| A hardening or scalability item that is explicitly deferred | Work actively being executed (→ `plan_docs/`) |
| A feature idea with enough context to act on later | A resolved item (delete or move to changelog) |

---

## File naming

One file per topic, named descriptively in snake_case:

```
future_docs/
  match_skill_hardening_roadmap.md
  render_docx_engine.md
  scraper_rate_limit_backoff.md
```

A file may cover a theme (e.g. all hardening for one module) or a single well-scoped item.

---

## File structure

Each file must include a `Last reviewed` date. A file not touched in **6 months** is considered stale — either review and re-date it, promote it to `plan_docs/`, or delete it.

```markdown
# <Title>

**Why deferred:** One sentence. What is blocking or deprioritizing this now.
**Last reviewed:** YYYY-MM-DD

## Problem / Motivation
What is wrong or missing, and why it matters. Be specific.

## Proposed Direction
What the solution looks like at a high level. Not a full spec — enough to resume context later.

## Linked TODOs
- `src/core/ai/match_skill/graph.py` — `# TODO(future): thin state, move payloads to disk refs`
- `src/core/tools/render/coordinator.py` — `# TODO(future): add DOCX engine adapter`
```

**Stale threshold:** If `Last reviewed` is more than 6 months ago and there is no linked active work, the entry should be deleted or explicitly re-evaluated. A `future_docs/` file that no one has touched in 6 months is a graveyard entry.

---

## Inline TODO convention

When deferring work from inside the code, leave a `# TODO` comment at the exact location. Format:

```python
# TODO(future): <short description> — see future_docs/<filename>.md
```

The `(future)` tag distinguishes deferred items from short-term TODOs. The file link makes it navigable.

**Example:**
```python
# TODO(future): thin MatchSkillState — move payload fields to disk refs — see future_docs/match_skill_hardening_roadmap.md
```

---

## Lifecycle

```
idea / known problem
       ↓
  future_docs/<topic>.md  ←  linked from inline # TODO(future)
       ↓  (when prioritized)
  plan_docs/<plan>.md     ←  full execution plan written, future_docs entry deleted
       ↓  (when complete)
  plan_docs deleted, changelog.md updated, inline TODO removed
```

- Promote to `plan_docs/` when the item enters active execution.
- Delete the `future_docs/` entry at that point — do not keep both.
- Remove the inline `# TODO(future)` comment once the work is done.

---

## GitHub Issues (optional)

GitHub Issues can track the same items with assignees, labels, and discussion threads. If you use them, add the issue number to the inline TODO:

```python
# TODO(future): thin MatchSkillState — see future_docs/match_skill_hardening_roadmap.md (#42)
```

Issues are useful for visibility and prioritization across collaborators. The `future_docs/` file remains the source of technical context; the issue is the coordination handle.
