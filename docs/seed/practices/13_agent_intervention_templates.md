# Agent Intervention Templates

Standardized workflows for AI agents operating in the PhD 2.0 context. Each template defines coordinates, execution steps, and rules to prevent context leakage.

---

## ⚠️ CRITICAL: Always Use DocMutator Tools

LLMs are literal. You MUST explicitly call the DocMutator methods — do NOT use generic OS tools (bash, echo, etc.) to write files.

**Why?** DocMutator tools have:
- Atomic lock protection (prevents race conditions)
- Automatic path resolution
- Audit trails

**Available Tools (from `src/tools/doc_mutator.py`):**

| Tool | When to Use |
|------|-------------|
| `sync_code_to_docs(domain, stage, generated_docs)` | Template 1 |
| `implement_plan(domain, stage, plan_doc, generated_code, generated_docs)` | Template 2 |
| `draft_plan(domain, stage, plan_filename, plan_content)` | Template 3 |
| `hotfix(domain, stage, fixed_code, updated_docs, skip_docs)` | Template 4 |

---

## Overview: The 4 Flows

| Flow | Direction | Use Case | Modifies |
|------|-----------|----------|----------|
| **Sync** | Code → Docs | Docs became stale after code changes | docs/ only |
| **Implement** | Plan → Code → Docs | Execute an existing design | code + docs |
| **Design** | Runtime → Plan | Propose new architecture | plan/ only |
| **Hotfix** | Code → Code | Fix bug, respect contracts | code + docs |

---

## Template 1: Sync Flow (Code → Docs)

**Use when:** You wrote code manually or AI generated code, and runtime documentation is outdated.

### Coordinates

- Domain: `[INSERT_DOMAIN, e.g. ui]`
- Stage: `[INSERT_STAGE, e.g. match]`

### Execution

1. `fetch_context(domain='[DOMINIO]', stage='[STAGE]', state='runtime', include_code=True)`
2. Analyze the source code provided in context
3. Analyze the corresponding Markdown doc in `docs/runtime/` or `docs/ui/`
4. Rewrite the Markdown to reflect STRICTLY the code reality
5. **Call the tool**: `sync_code_to_docs(domain='[DOMINIO]', stage='[STAGE]', generated_docs={'docs/path.md': 'rewritten content'})`

### Rules

- Do NOT speculate about future features
- Remove any mention of features that no longer exist in code
- Do NOT modify source code (only docs)

### Postcondition

```
docs/runtime/[DOMAIN]/[STAGE].md → UPDATED via sync_code_to_docs()
code → UNCHANGED
```

---

## Template 2: Implement Flow (Plan → Code → Docs)

**Use when:** An existing design document lives in `plan/` and you want the agent to write real code.

### Coordinates

- Domain: `[INSERT_DOMAIN]`
- Stage: `[INSERT_STAGE]`
- Plan to implement: `[PLAN_FILENAME, e.g. B2_extract_understand.md]`

### Execution

1. `fetch_context(domain='[DOMINIO]', stage='[STAGE]', state='plan')` — read target design
2. `fetch_context(domain='[DOMINIO]', stage='[STAGE]', state='runtime', include_code=True)` — understand base state
3. Write code to fulfill EXACTLY what the plan demands
4. **Call the tool**: `implement_plan(domain='[DOMINIO]', stage='[STAGE]', plan_doc='plan/[DOMAIN]/[FILENAME]', generated_code={'src/file.tsx': 'code'}, generated_docs={'docs/runtime/path.md': 'doc'})`

### Rules

- Code MUST match plan specifications exactly
- **Use implement_plan tool** — it automatically deletes the plan after success
- Do NOT manually delete files

### Postcondition

```
plan/[DOMAIN]/[PLAN] → DELETED automatically by implement_plan()
code → CREATED/MODIFIED
docs/runtime/ → PROMOTED automatically by implement_plan()
```

### ⚠️ Permission Fix

The phrase "recommend (or execute) deletion" is **broken**. Use `implement_plan()` — it handles deletion automatically.

---

## Template 3: Design Flow (Runtime → Plan)

**Use when:** You want the agent to propose architecture, refactor, or UI design WITHOUT touching working code.

### Coordinates

- Domain: `[INSERT_DOMAIN]`
- Stage: `[INSERT_STAGE]`
- Design requirement: `[DESCRIBE_WHAT_YOU_WANT, e.g. "Add bulk regeneration button"]`

### Execution

1. `fetch_context(domain='[DOMINIO]', stage='[STAGE]', state='runtime', include_code=True)` — understand current system
2. Create a detailed technical proposal solving the "Design requirement"
3. **Call the tool**: `draft_plan(domain='[DOMINIO]', stage='[STAGE]', plan_filename='proposal_name.md', plan_content='# Proposal\n...')`

### Rules

- Write to `plan/[DOMAIN]/` ONLY
- NEVER modify source code (`.py`, `.tsx`)
- NEVER modify files in `docs/runtime/` or `docs/ui/`

### Postcondition

```
plan/[DOMAIN]/[PROPOSAL].md → CREATED via draft_plan()
code → UNCHANGED
docs/runtime/ → UNCHANGED
```

---

## Template 4: Hotfix Flow (Code → Code → Docs)

**Use when:** There's a bug, linting error, or you need AI to fix something quickly based on current business rules.

### ⚠️ CRITICAL FIX

**OLD (BROKEN) RULE**: "docs → UNCHANGED after hotfix"

This guaranteed documentation drift. After 5 hotfixes, Context Router breaks.

**NEW RULE**: Docs MUST be updated after every code change.

### Coordinates

- Domain: `[INSERT_DOMAIN]`
- Stage: `[INSERT_STAGE]`
- Problem: `[DESCRIBE_BUG, e.g. "span_resolver fails on multiline text offsets"]`

### Execution

1. `fetch_context(domain='[DOMINIO]', stage='[STAGE]', state='runtime', include_code=True)`
2. Read the documentation to understand the business contract the code MUST fulfill
3. Analyze source code to find the problem origin
4. Modify ONLY the source code strictly necessary to fix the issue
5. **Call the tool**: `hotfix(domain='[DOMINIO]', stage='[STAGE]', fixed_code={'src/file.py': 'fixed code'}, updated_docs={'docs/runtime/path.md': 'updated doc'})`

### Rules

- Modify ONLY the code strictly necessary to resolve the problem
- Ensure your fix doesn't violate rules in the documentation
- **ALWAYS update docs after code change** (no exceptions)
- Use `skip_docs=True` ONLY for critical production emergencies

### Postcondition

```
code → MODIFIED via hotfix()
docs/runtime/ → UPDATED via hotfix()
```

### Emergency Exception

If `skip_docs=True`, code is fixed but docs remain unchanged. This is a **debt**: must be resolved within 24 hours via `sync_code_to_docs()`.

---

## CLI Integration

Package these templates into a simple command:

```bash
./agent.sh --mode implement --domain ui --stage match --target "B3_match_redesign.md"
```

### CLI Options

| Flag | Values | Description |
|------|--------|-------------|
| `--mode` | `sync`, `implement`, `design`, `hotfix` | Which template to use |
| `--domain` | `ui`, `api`, `pipeline`, `core`, `data`, `policy` | Technical domain |
| `--stage` | `scrape`, `translate`, `extract`, `match`, `strategy`, `drafting`, `render`, `package` | Pipeline stage |
| `--target` | filename | Plan file or problem description |
| `--include-code` | `true`, `false` | Include source code in context (default: true for sync/hotfix, false for design) |
| `--skip-docs` | flag | Skip doc update (hotfix only, creates 24h debt) |

### Example Commands

```bash
# Sync docs after manual code changes
./agent.sh --mode sync --domain ui --stage match

# Implement an existing plan
./agent.sh --mode implement --domain ui --stage extract --target "B2_extract_understand.md"

# Design a new feature
./agent.sh --mode design --domain ui --stage strategy --target "Add bulk regeneration"

# Fix a bug
./agent.sh --mode hotfix --domain pipeline --stage extract --target "span_resolver multiline"
```

---

## Prevention Rules Summary

| Mode | Can write to code? | Can write to docs/runtime? | Can write to plan/? | Use Tool | Docs required? |
|------|-------------------|---------------------------|-------------------|----------|----------------|
| sync | NO | YES (overwrite) | NO | `sync_code_to_docs()` | YES |
| implement | YES | YES (promote) | NO (auto-delete) | `implement_plan()` | YES |
| design | NO | NO | YES (create) | `draft_plan()` | N/A |
| hotfix | YES | YES (update) | NO | `hotfix()` | **YES** (use `skip_docs` only in emergencies) |

---

## Decision Matrix

```
Is there a bug to fix?
├─ YES → hotfix (Template 4)
│        └─ Call hotfix(domain, stage, fixed_code, updated_docs)
│            → or hotfix(domain, stage, fixed_code, {}, skip_docs=True) for emergency
└─ NO
  ├─ Is there a design document in plan/?
  │   ├─ YES → implement (Template 2)
  │   │        └─ Call implement_plan(domain, stage, plan_doc, generated_code, generated_docs)
  │   └─ NO
  │       ├─ Do you want to propose something new?
  │       │   ├─ YES → design (Template 3)
  │       │   │        └─ Call draft_plan(domain, stage, filename, content)
  │       │   └─ NO
  │       │       └─ Did code change without updating docs?
  │       │           ├─ YES → sync (Template 1)
  │       │           │        └─ Call sync_code_to_docs(domain, stage, generated_docs)
  │       │           └─ NO → STOP (nothing to do)
```

### Debt Resolution

After `skip_docs=True` hotfix, you MUST call within 24 hours:
```
sync_code_to_docs(domain='<same>', stage='<same>', generated_docs={...})
```

---

## ⚠️ AI Agent Restrictions (System Enforcement)

**This repository is protected by Git Hooks and Branch Protection Rules.**

| Rule | What Happens | How to Comply |
|------|--------------|---------------|
| `commit-msg` hook | Blocks commits without valid format or TestSprite evidence | Include `TestSprite: Passed` or `TestSprite: ID-123` in commit body |
| `pre-push` hook | Blocks push if tests fail | Ensure `pytest` and `npm run typecheck` pass |
| GitHub PR rules | Requires 1+ approval and passing CI | Get human review before merge |

### Commit Message Format (Required)

```
<type>(<domain>): <description> (<spec-id>)

- <component 1>
- <component 2>
- TestSprite: <Passed|ID-123>
```

**Valid examples:**
```
feat(ui): implement strategy form (spec-123)
  - StrategyForm component
  - DeltaEditor component
  TestSprite: Passed

fix(pipeline): correct span offset (hotfix-456)
  - Fixed multiline handling
  TestSprite: ID-789
```

### What Happens If You Violate Rules

| Violation | Result |
|-----------|--------|
| Missing `(spec-id)` | `commit-msg` hook blocks commit |
| Missing `TestSprite:` | `commit-msg` hook blocks commit |
| Failing tests + push | `pre-push` hook blocks push |
| Push without PR | GitHub blocks merge (requires approval) |

### Safe Workflow for AI Agents

1. Before any code change: Read the spec in `plan/`
2. After implementation: Run tests locally (or document that they pass)
3. When committing: Use exact format with `TestSprite:` line
4. When pushing: Ensure pre-push hook passes (or document test failure)

**Do NOT attempt to bypass these rules — they protect the codebase integrity.**
