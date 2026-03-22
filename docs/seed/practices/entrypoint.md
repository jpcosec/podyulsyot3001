# Development Entry Point (PhD 2.0)

Welcome to PhD 2.0. This repository operates under "Determinism and Decoupling" architecture. To maintain system sanity and enable AI agents to operate without destroying the codebase, all development must follow an unbreakable lifecycle.

---

## The Golden Rule (Zero-Tolerance Policy)

**No code change is valid unless it fulfills all 5 pillars:**

| Pillar | Requirement |
|--------|-------------|
| **Planned** | Every change starts as a document in `plan/` |
| **Tested** | Every functional change must have an E2E test in TestSprite |
| **Documented** | Technical truth in `docs/runtime/` must reflect code reality |
| **Registered** | Every change leaves a trace in `changelog.md` and checklists |
| **Committed** | Standardized commit format required for traceability |

---

## Mandatory Change Lifecycle

Every intervention (human or AI agent) must follow this exact sequential flow:

### Phase 1: Planning and Design (plan/)

Before touching a single line of code, define what you're going to do.

1. Open `planning_template_ui.md` (for UI) or `planning_template_backend.md` (for backend/pipeline)
2. Create a new spec file in `plan/[domain]/` (e.g., `plan/ui/feature_x.md`)
3. Define data contracts, UI/backend composition, and acceptance criteria

### Phase 2: Execution (The Code)

Once the plan exists officially, proceed with implementation using routing rules and agent templates.

1. Consult `11_routing_matrix.md` to know which domain and pipeline stage to inject your code
2. If using AI, invoke **Template 2 (Implement Flow)** to convert your plan into real code
3. For quick bug fixes, use **Template 4 (Hotfix Flow)**, but be prepared to document in Phase 4

### Phase 3: Mandatory Testing (TestSprite & QA)

Written code does not exist until it's tested.

| Test Type | What to Verify |
|-----------|----------------|
| Local verification | No console errors, no TypeScript errors, no hanging states |
| E2E (TestSprite) | Component rendering, expected element states, correct navigation |

### Phase 4: Documentation Closure (Synchronization)

Code works and tests pass. Now synchronize the project brain.

| Action | Description |
|--------|-------------|
| **Promote to Docs** | Move/overwrite plan document to `docs/runtime/` as official documentation. Delete the original plan file. |
| **Update README** | If change alters overall architecture, ensure domain README is accurate |
| **Changelog** | Add entry to `changelog.md` under current date |
| **Checklist** | Mark task as completed `[x]` in `index_checklist.md` |

### Phase 5: Git Workflow (The Commit)

Do NOT run `git commit -m "fix"`. Use the mandatory format:

```bash
feat(domain): implement <view/feature name> (<spec-id>)

- <component or module 1>
- <component or module 2>
- E2E tests in TestSprite configured and passing
- Documentation in docs/runtime updated
```

### Phase 6: Meta-Review (System Evolution)

Development of a task does not end when code works in production — it ends when the overall system learns from the friction that occurred during the session.

#### Human Review (Sanity Check)
At session end, the human operator must review the steps taken by the AI agent (or developer) and evaluate whether base documentation instructions were clear or caused confusion.

#### Rabbit Hole Identification
If AI hallucinated, got stuck trying to execute commands without permissions, or the router failed to find correct context, the human must isolate the cause of that friction.

#### Meta-Documentation Correction
Take session findings and immediately patch the foundational documentation:
- Protocol failed → Update `12_context_router_protocol.md`
- Missing keyword → Inject into `11_routing_matrix.md`
- Ambiguous rule → Rewrite `13_agent_intervention_templates.md`

#### Iterative Immunity
No logical error or contradiction in system rules should survive the session that discovered it.

---

## Quick Authorization Checklist (Definition of Done)

**Do NOT open a PR or consider task complete if any box is unchecked:**

| # | Pillar | Checklist Item |
|---|--------|----------------|
| 1 | **Code** | Functionality meets operator objectives without TypeScript/Console errors or broken dependencies |
| 2 | **Testing** | TestSprite (E2E) tests defined, executed successfully, and cover base cases |
| 3 | **Docs** | `plan/` cleaned, `docs/runtime/` contains final technical documentation reflecting actual code state |
| 4 | **Changelog** | New rigorous entry added to `changelog.md` explaining the change |
| 5 | **Commit** | Commit follows conventions format (feat/fix/docs + structured details) |
| 6 | **Meta-Review** | Human audited session, identified logical friction in development process, and patched meta-documentation to prevent future rabbit holes |

---

## Lifecycle Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                     PHASE 1: PLANNING                           │
│  planning_template*.md → plan/[domain]/feature.md              │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PHASE 2: EXECUTION                          │
│  Implement via agent or manually → Code in src/                 │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PHASE 3: TESTING                            │
│  Local verification → TestSprite E2E tests                     │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PHASE 4: DOCUMENTATION                      │
│  Promote plan → docs/runtime → Delete plan → Changelog          │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PHASE 5: GIT                                │
│  Standardized commit message                                    │
└─────────────────────────┬───────────────────────────────────────┘
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     PHASE 6: META-REVIEW                        │
│  Audit session → Fix friction → Update meta-docs               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Related Documents

| Document | Purpose |
|----------|---------|
| `11_routing_matrix.md` | Context routing for AI agents |
| `12_context_router_protocol.md` | How the router and mutator work |
| `13_agent_intervention_templates.md` | Standardized agent workflows |
| `planning_template_ui.md` | UI feature spec template |
| `planning_template_backend.md` | Backend/pipeline spec template |
