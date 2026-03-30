# LLM-Agent-Native Context Layer (OpenViking Integration)

**Why deferred:** The core pipeline works correctly as human-operated tooling. This work is about making it navigable by an LLM agent (Claude Code or similar) without needing to execute code to understand the system. It also explores integrating [OpenViking](https://github.com/volcengine/OpenViking), a context database designed for LLM agents, as the backing store for structured context resources.
**Last reviewed:** 2026-03-29

---

## What is OpenViking

OpenViking (https://github.com/volcengine/OpenViking) is an open-source context database built around the concept of "Context as a Resource". It provides:

- A layered resource model (raw memory → domain knowledge → logic/tools) for structuring what an agent knows.
- A resource URI scheme (`viking://resources/<name>/`) for addressing context chunks.
- Schema validation for tool inputs/outputs so agents cannot pass malformed data between modules.

The integration idea: map this project's existing artifacts (logs, READMEs, Pydantic contracts, `future_docs/`) onto OpenViking's resource model so an agent working in this codebase can query structured context instead of reading raw files.

---

## Problem / Motivation

The project is documented for humans but not yet structured for autonomous LLM agents. An agent working in this codebase currently has to:

- Execute `--help` or read argparse source to understand CLI arguments (one tool call per interface).
- Infer data contracts by reading Python files, not from a machine-readable schema.
- Discover deferred design decisions only if it happens to read `future_docs/` — there is no explicit instruction to check it.
- Parse free-text logs with no reliable structure for programmatic indexing.

The gap is not documentation quality — it is the absence of a **context loading strategy** designed for an agent consumer.

---

## Proposed Direction

Four concrete improvements, in order of implementation cost:

### 1. JSON Schema export for inter-module contracts

Every `contracts.py` defines Pydantic models. Export them to static JSON Schema files so an agent (or any consumer) can validate data between modules without importing Python.

```
src/core/ai/match_skill/schemas/
  RequirementInput.schema.json
  MatchEnvelope.schema.json
  ReviewPayload.schema.json
```

Implementation: a script `scripts/export_schemas.py` that calls `.model_json_schema()` on all public models in each `contracts.py` and writes them to `src/<module>/schemas/`. Run as part of CI to keep them in sync.

This also enables validation in non-Python consumers (LangGraph Studio, external APIs).

### 2. Module overviews as structured agent context

Rename or supplement each `src/<module>/README.md` with a predictable machine-loadable format. The idea is not a new file type — it is a **convention on README structure** so an agent can load `src/<module>/README.md` and get:

- What the module does (first paragraph, always)
- Key file paths (Architecture section, always linked)
- Entry points (CLI/Usage section, always pointing to code)

Our existing README standard already enforces this. The additional step is adding `src/<module>/README.md` paths explicitly to `CLAUDE.md` so agents know where to look without scanning the tree.

### 3. `future_docs/` as explicit agent search target

Before an agent concludes "I don't know how this was designed to work", it should check `future_docs/`. This is a **CLAUDE.md instruction**, not a code change:

```
# In CLAUDE.md:
# When you cannot find the rationale for a design decision in the code or READMEs,
# check future_docs/ — it holds deferred problems with their architectural context.
```

### 4. Log event indexing via `LogTag` structure

`LogTag` already emits parseable bracketed tags (`[❌]`, `[🧠]`, etc.) into `logs/`. A lightweight indexer script could scan log files and produce a structured event summary (errors, LLM calls, fallbacks) without needing to parse free text.

This is low priority until the pipeline runs at a scale where log volume makes manual scanning impractical.

---

## Linked TODOs

- `scripts/` — `# TODO(future): add export_schemas.py — see future_docs/llm_agent_native_context.md`
- `CLAUDE.md` — `# TODO(future): add future_docs/ search instruction for agents — see future_docs/llm_agent_native_context.md`
- `src/shared/log_tags.py` — `# TODO(future): add log indexer script — see future_docs/llm_agent_native_context.md`
