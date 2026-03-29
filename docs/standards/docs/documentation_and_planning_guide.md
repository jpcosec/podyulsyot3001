# 📖 Documentation & Planning Guide

This is the single source of truth for how this project is documented, planned, and navigated.

> **Core principle:** Clean, well-structured code beats documentation. READMEs explain *why* and *what* and orient the reader — the *how* lives in the code itself. Documentation that duplicates code always drifts; documentation that points to code stays honest.

---

## 1. How to Navigate This Repository

### Entry points

```
README.md                  ← repository overview and orientation
docs/standards/docs/       ← documentation conventions (this file and siblings)
src/<module>/README.md     ← per-module orientation
future_docs/               ← deferred work and known problems
plan_docs/                 ← active execution plans (ephemeral)
changelog.md               ← record of significant changes
```

`docs/` is a navigation layer, not a content store. It holds cross-cutting guides and links out to module-level READMEs. It does not duplicate what the code or module READMEs already say.

### Reading order for a new contributor

1. `README.md` — understand the system shape and purpose.
2. `docs/standards/docs/` — understand documentation conventions before touching anything.
3. `src/<module>/README.md` — orient on the specific area you're working in.
4. The source files linked from that README — the code is the authoritative source.

---

## 2. How to Write a README

READMEs explain **why the module exists**, **what it does**, and **where the important pieces are**. They do not re-document what the code already makes explicit.

### Mandatory sections

Every module README must contain these sections, in order, with emoji markers:

| Section | Emoji | Purpose |
|---|---|---|
| Architecture & Features | 🏗️ | Shape of the system and its design rationale |
| Configuration | ⚙️ | Required env vars and setup, in code blocks |
| CLI / UI / Usage | 🚀 | Intent and entry points — not argument tables |
| Data Contract | 📝 | What flows in and out — points to the model files |
| How to Add / Extend | 🛠️ | Numbered steps for extending the module |
| How to Use | 💻 | Copy-pasteable quickstart |
| Troubleshooting | 🚑 | Symptom → Diagnosis → Solution |

### Architecture section rules

Describe the structural shape, then **link to the exact file**. The file is authoritative. File links are validated by `scripts/validate_doc_links.py` — a broken link is a CI failure.

```markdown
## 🏗️ Architecture & Features

The match skill runs as a LangGraph `StateGraph` with a single human breakpoint.

- Graph definition and node wiring: `src/match_skill/graph.py`
- State schema: `MatchSkillState` in `src/match_skill/graph.py`
- Artifact persistence: `MatchArtifactStore` in `src/match_skill/storage.py`
```

Never describe a function signature or field list in a README — that belongs in docstrings.

### CLI / UI section rules

Describe the *intent* of the interface. Do not copy argument tables — they drift. Instead, point to where the self-documentation lives in the code so an agent can read it directly without executing anything.

```markdown
## 🚀 CLI / Usage

Run a match thread from requirement and profile-evidence JSON files.
Arguments are defined in the `build_parser()` function in `src/cli/run_match_skill.py`.

Resume a paused thread after HITL review:

    python -m src.cli.run_match_skill --source <source> --job-id <id> --resume
```

For Settings-driven configuration, point to the Settings class file instead of `--help`.

### Data contract section rules

The Pydantic model file **is** the contract. Point to it — do not restate field names or types in the README.

```markdown
## 📝 Data Contract

Input and output schemas are defined in `src/match_skill/contracts.py`:
- `RequirementInput` — one requirement from the job posting
- `MatchEnvelope` — full LLM structured output
- `ReviewPayload` — what the TUI sends back into the graph
```

---

## 3. How to Write Code Documentation

### Module docstrings

Every Python file opens with a module docstring — an executive summary of what the module does and its role in the system.

### Class and method docstrings

Every public class, method, and function has a structured docstring with purpose, args, and return value. For ABCs, the class docstring explicitly lists all abstract methods as the developer contract.

### Pydantic field descriptions

`Field(description=...)` is dual-purpose: it's read by humans and consumed by LLMs. Write it accordingly — semantic, specific, with examples for fields that carry ambiguous values. For multilingual fields, include examples in both languages.

```python
# ✅
responsibilities: list[str] = Field(
    description="Job responsibilities ('Deine Aufgaben', 'Your Impact'). Extract as a list of short action phrases."
)
```

Mark MANDATORY vs. OPTIONAL fields in class-level comments so the boundary is visible without reading validation logic.

### Error contracts

Define domain-specific exceptions at the top of the file. Never rely on bare `Exception` for flow control.

```python
class ToolDependencyError(Exception): pass
class ToolFailureError(Exception): pass
```

Never swallow errors silently. If you catch a broad exception to trigger a fallback, log it with `[⚠️]` first and re-raise with `from e` to preserve the stack trace.

Expose operational limits (chunk sizes, retry budgets, rate limits) as `@property` on ABCs — not buried in loops or config dicts.

### Observability log tags

Logs are real-time execution documentation. **Never write emoji tag strings by hand** — import `LogTag` from `src/shared/log_tags.py`. This prevents typos and enforces the shared vocabulary.

```python
from src.shared.log_tags import LogTag

logger.info(f"{LogTag.LLM} Generating match proposal for {job_id}")
logger.warning(f"{LogTag.WARN} Rate limit hit, retrying in {delay}s")
logger.error(f"{LogTag.FAIL} Schema validation failed: {err}")
```

| `LogTag` | Tag | Meaning |
|---|---|---|
| `LogTag.SKIP` | `[⏭️]` | Skipped — already processed (idempotency) |
| `LogTag.CACHE` | `[📦]` | Cache hit / loaded existing artifact |
| `LogTag.LLM` | `[🧠]` | LLM reasoning or dynamic generation — **not for deterministic paths** |
| `LogTag.FAST` | `[⚡]` | Fast / deterministic path — no LLM involved |
| `LogTag.FALLBACK` | `[🤖]` | Fallback mechanism active |
| `LogTag.OK` | `[✅]` | Success / validation passed |
| `LogTag.WARN` | `[⚠️]` | Expected / handled error |
| `LogTag.FAIL` | `[❌]` | Hard failure — pipeline breaks |

Note: the enum enforces the tag vocabulary, not semantic correctness. Using `LogTag.LLM` on a deterministic path is still wrong — that's a code review concern.

---

## 4. How to Plan

Active execution plans live in `plan_docs/`. They are **ephemeral** — deleted when the work is done.

```
plan_docs/
  match_skill_tui_refactor.md
  render_docx_engine.md
```

A plan file contains: goal, constraints, ordered steps, and open questions. It is a working document — edit it freely as understanding improves. It is not documentation; do not write it as if future readers will study it.

**Lifecycle:**

```
spec / requirement
      ↓
  plan_docs/<plan>.md   ←  written before touching code
      ↓  (execution complete, all tests pass)
  deleted               ←  changelog.md updated with what changed and why
```

If an execution plan reveals a deferred item (something real but out of scope), move it to `future_docs/` before closing the plan.

---

## 5. How to Mark Future Work

See [`future_docs_guide.md`](future_docs_guide.md) for the full convention.

**Short version:**

1. Create `future_docs/<topic>.md` describing the problem, why it's deferred, and a proposed direction.
2. Leave an inline marker at the relevant code location:

```python
# TODO(future): <short description> — see future_docs/<topic>.md
```

3. When the item is prioritized, promote to `plan_docs/`, delete the `future_docs/` entry, and remove the inline marker when done.

---

## 6. Documentation Lifecycle Rules

- Update the module README **at the same time** as the code change, not after.
- When a Pydantic field changes meaning, update its `Field(description=...)` in the same commit.
- When a new fallback or retry mechanism is added, add the corresponding `[🤖]` or `[⚠️]` log line.
- When architectural patterns change, update the Architecture section and its file links.
- Documentation that describes removed behaviour must be deleted, not left as historical comment.
