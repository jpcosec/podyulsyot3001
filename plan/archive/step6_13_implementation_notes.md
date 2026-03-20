# Step 6-13 Implementation Notes

Companion to: `plan/archive/step6_13_delta_generation_and_text_reviewers.md`

Status: active notes — updated as decisions are made.

---

## Settled decisions

- **`generate_documents` shared kernel is non-negotiable.** One LLM call produces all `DocumentDeltas` (CV + letter + email). Per-document separate calls are not in scope.
- **`experience_id` over `company_name`** in `DocumentDeltas.cv_injections` — stable profile ID anchoring, not mutable strings.
- **Text reviewers are advisory only and deterministic.** No LLM call, no decision fields, no routing output. Deterministic `review_<doc>` nodes remain sole routing authority.

## Implemented now (current branch)

- Added graph-visible `generate_documents` node package under `src/nodes/generate_documents/` with:
  - structured contracts (`DocumentDeltas`, deterministic indicator envelope),
  - delta generation logic,
  - deterministic Jinja templates for CV/letter/email,
  - deterministic anti-fluff/style indicator artifacts under `assist/proposed/`.
- Added tests for new contracts and node logic:
  - `tests/nodes/generate_documents/test_contract.py`
  - `tests/nodes/generate_documents/test_generate_documents_logic.py`
- Full test suite is green after implementation (`55 passed`).

---

## Sequencing gate (must resolve before Phase A)

`src/core/io/` (`WorkspaceManager`, `ArtifactReader`, `ArtifactWriter`, `ProvenanceService`) does not exist yet.
Phase A (`build_application_context` + `review_application_context`) depends on it.
Starting Phase A without it repeats the current bootstrap anti-pattern (inline path construction, data payloads in `GraphState`).

**Gate: `src/core/io/` must be implemented and tested before Phase A coding begins.**

`sync_json_md` service is similarly absent and required for generating review surfaces in Phase A nodes.

**Gate: `sync_json_md` must exist before any node that produces a reviewable `review/decision.md`.**

---

## Open questions (Section 11) — need explicit answers before coding

### Q1: Is `generate_documents` graph-visible or internal service?

Consequences of each choice:

| Choice | Impact |
|---|---|
| Graph-visible node | Must appear in `docs/runtime/graph_flow.md` and `node_io_matrix.md`; gets its own `nodes/generate_documents/` package; checkpoint captures its output |
| Internal service called by assembler nodes | Stays invisible to LangGraph; no topology doc changes; harder to checkpoint its output independently |

Resolved: graph-visible.

### Q2: Partial regeneration state bookkeeping

When reviewer requests regeneration on only CV (not letter), the shared kernel is re-called.
The new call may produce different letter deltas even if letter was not the regeneration target.

Two options:

1. **Re-call kernel for full `DocumentDeltas`, accept that all deltas may change** — simple, but letter reviewer's prior approval is voided.
2. **Per-part delta pinning** — persist each part's delta hash separately; re-call only the parts flagged for regeneration; merge unchanged parts from prior run.

Option 2 preserves cross-part consistency but requires a delta cache and merge logic.
Decision needed before implementing the hash-based reuse in Section 6.2.

### Q3: Anti-fluff policy mode

`warning` vs `fail-closed` for critical policy violations.
For MVP: warnings + reviewer flags (as stated in Section 8).
Hardening threshold: define what triggers escalation to fail-closed (e.g., forbidden phrase in final approved output, zero approved-claim refs in letter body).

### Q4: Text reviewer assist nodes — mandatory in Phase D or optional at launch?

Resolved direction: deterministic text-review indicators are now implemented without LLM and can be consumed immediately as advisory artifacts.

---

## Canonical doc updates required before implementation

These docs must be updated before the corresponding implementation phase, not after:

| Doc | Required update | Before phase |
|---|---|---|
| `docs/runtime/graph_flow.md` | Add `generate_documents` node; add `reviewer_<doc>_assist` nodes if graph-visible | Phase B / Phase D |
| `docs/runtime/node_io_matrix.md` | Add rows for `generate_documents`, assembler node changes, and assist nodes | Phase B / Phase D |
| `plan/runtime/artifact_schemas.md` | Add `DocumentDeltas` schema; add `nodes/<node>/assist/proposed/` path convention | Phase B / Phase D |
| `docs/runtime/core_io_and_provenance.md` | No change needed — already specifies the target; implement against it | — |

Rule: no implementation begins until the canonical doc for that phase is updated and reviewed.

---

## Artifact path gap

`nodes/<node>/assist/proposed/state.json` and `nodes/<node>/assist/proposed/view.md` are referenced in Section 7.4 but absent from `plan/runtime/artifact_schemas.md`.

Must be added to artifact schemas before Phase D coding. The `assist/` subdirectory is a new convention and needs a clear ownership rule (who writes it, who reads it, whether it carries provenance).

---

## Contract completeness prerequisite

Before `generate_documents` can be implemented, its upstream inputs must be schema-stable:

- `nodes/review_match/approved/state.json` — currently written but uses simplified `MatchEnvelope` (missing `schema_version`, `doc_type`, `source_text_ref`, `RequirementMapping` matrix). Must be aligned with spec before `generate_documents` depends on it.
- `nodes/build_application_context/approved/state.json` — does not exist yet; schema must be defined and approved as part of Phase A.

`DocumentDeltas.cv_injections[].experience_id` must be validated against the profile snapshot at generation time. The profile snapshot path (`data/reference_data/profile/base_profile/profile_base_data.json`) must be accessible through `WorkspaceManager`.

---

## Phase execution checklist additions

For each phase, add to the existing acceptance criteria:

- [ ] Canonical docs updated for that phase before coding starts.
- [ ] `core/io/` integration confirmed (no inline path construction in new nodes).
- [ ] No data payloads added to `GraphState` (only `artifact_refs` pointers).
- [ ] Provenance written for all approved artifacts.
