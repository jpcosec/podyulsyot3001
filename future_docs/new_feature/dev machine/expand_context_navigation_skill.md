# Navigation Skill: expand_context

**Why deferred:** Depends on all module READMEs being conformant with the Architecture and Data Contract section standards. Build after README conformance is verified across the codebase.
**Last reviewed:** 2026-03-29

---

## Problem / Motivation

The documentation system is designed as a **navigable graph** — the same model Wikipedia uses. Each module README is the "article" for that module: it orients you, links to key files, and points to the data contracts. You follow links to go deeper, reading only what the task requires. You never need to read the whole encyclopedia to understand one topic.

This matters especially for LLM agents: an agent that reads files by following an explicit link graph has a deterministic, minimal context. An agent that scans the tree or reads files speculatively loads noise and risks stopping at the wrong depth.

The problem: following links manually costs one file read per hop. An agent working on `match_skill` needs to load the README, then the graph file, then the contracts file, before it has a complete mental model. That's 3–4 sequential reads, each requiring a decision about whether to go deeper.

`expand_context` collapses this into a single call. Given a module path, it returns a deterministic bundle:

1. The module README (orientation layer)
2. All files linked in the `## 🏗️ Architecture` section (implementation layer)
3. The JSON Schemas of all Pydantic models linked in the `## 📝 Data Contract` section (contract layer)

This is the "Wikipedia book export" pattern: one article plus all articles it directly links to, assembled without noise and without requiring the consumer to navigate the graph manually.

---

## Proposed Direction

### Script: `scripts/expand_context.py`

```
python scripts/expand_context.py src/core/ai/match_skill
```

Output: a single markdown bundle (stdout or file) structured as:

```
## Context Bundle: src/core/ai/match_skill
Generated: <timestamp>

### [1/3] README
<content of src/core/ai/match_skill/README.md>

### [2/3] Architecture Files
#### src/core/ai/match_skill/graph.py
<content>

#### src/core/ai/match_skill/storage.py
<content>

### [3/3] Data Contracts (JSON Schema)
#### MatchEnvelope
<json schema>

#### ReviewPayload
<json schema>
```

### Parsing strategy

- Extract Architecture file links using the same regex as `scripts/validate_doc_links.py` (backtick paths + markdown links), scoped to lines between the `## 🏗️ Architecture` header and the next `##`.
- Extract Pydantic model names from the Data Contract section, import them dynamically from the module's `contracts.py`, and call `.model_json_schema()`.
- Fail explicitly if a linked file does not exist (do not silently skip).

### CLAUDE.md navigation rules

These rules belong in CLAUDE.md regardless of whether the script exists — they encode the navigation protocol for any agent working in this codebase:

**Rule 1 — Read the article before the source:**
When starting work on a module, read `src/<module>/README.md` before reading any source file. The Architecture section tells you which files matter. The Data Contract section tells you what data flows in and out.

**Rule 2 — Contracts before logic:**
Never read `logic.py` or `graph.py` to understand a module's data shape. Read the linked `contracts.py` first. The contract is the module's interface; the logic is the implementation.

**Rule 3 — Anti-drift check:**
After modifying a file, check whether the module README's Architecture section links to it. If it does, verify the description is still accurate. If the file was renamed or moved, update the link.

**Rule 4 — Quality gate:**
Before marking a task complete, run through `docs/standards/docs/documentation_quality_checklist.md`.

---

## Preconditions

This script is only useful if READMEs are conformant:

- [ ] All module READMEs have a `## 🏗️ Architecture` section with backtick file links.
- [ ] All module READMEs have a `## 📝 Data Contract` section pointing to `contracts.py`.
- [ ] `scripts/validate_doc_links.py` passes with no broken references.

Implement `expand_context.py` after these are verified, not before. A script that bundles stale or missing links is worse than no script.

---

## Linked TODOs

- `scripts/` — `# TODO(future): add expand_context.py — see future_docs/expand_context_navigation_skill.md`
- `CLAUDE.md` — `# TODO(future): add navigation rules (read README before source, contracts before logic) — see future_docs/expand_context_navigation_skill.md`
