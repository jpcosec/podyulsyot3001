# PhD 2.0 Rebuild Master Plan (HITL, Node-by-Node)

> Status note (2026-03-20): this is a historical master-plan snapshot, not a current codebase mirror. It contains outdated paths, pre-migration assumptions, and target-state structures that no longer match the runnable repo exactly. Treat it as planning context only. For current runtime truth, use `README.md`, `docs/runtime/graph_flow.md`, `docs/runtime/data_management.md`, and `docs/index/canonical_map.md`.


## Purpose

Rebuild PhD 2.0 from the current "wax model" into production-grade behavior, with strict human approval at every step.

Core principles:

1. No placeholder progress.
2. No silent fallback-as-success.
3. No style drift.
4. No step can continue without explicit human approval.

This plan uses real data from the original `phd` workspace and validates artifacts step by step.

---

## Baseline Diagnosis (Current State)

Current repo has a good skeleton, but critical logic is still placeholder in key paths, e.g.:

- `src/ai/nodes/match/logic.py` uses stub fallback behavior.
- `src/core/nodes/render/logic.py` and `src/core/nodes/package/logic.py` are markdown passthrough/concatenation.
- Several generation nodes still produce generic template-like outputs.
- Runtime and node scaffolding are present and useful; behavior depth is missing.

This plan keeps the structure and replaces wax behavior incrementally.

---

## Final Architecture (Target End State)

## Source Tree Roles

- `src/core/` deterministic contracts, tools, validators, deterministic nodes.
- `src/ai/` non-deterministic LLM runtime + LLM nodes + graph orchestration.
- `src/interfaces/` CLI/operator workflows.

## Deterministic vs Non-Deterministic Boundary

- Deterministic: parsing, validation, provenance, review synchronization, policy enforcement, rendering, packaging.
- Non-deterministic: LLM generation only inside AI node logic and shared AI runtime.
- Forbidden: importing AI code from core.

## Canonical Data Layout

`data/jobs/<source>/<job_id>/`

- `raw/`
- `nodes/<node>/{input,proposed,review,approved,meta}`
- `runtime/checkpoints/`
- `final/`

---

## Global Execution Protocol (All Steps)

1. Implement exactly one planned step.
2. Run tests allowed for that step.
3. Run a real HITL execution for that step on real job data.
4. Human inspects output files.
5. Human approval required before next step starts.

No forward implementation is allowed before approval.

---

## Testing Policy (Critical)

## Deterministic steps

- Unit/integration tests are required.
- HITL run is still required before marking step "ready".

## LLM-involved steps (`match`, `build_application_context`, `generate_motivation_letter`, `tailor_cv`, `draft_email`)

- No semantic fixture-based acceptance.
- Only valid semantic acceptance is HITL on real cases.
- Automated tests may cover only:
  - schema validation,
  - required artifact presence,
  - gating/routing behavior,
  - error handling (without asserting semantic text quality).

---

## Anti-Wax / Anti-Drift Rules

1. No hardcoded generic content in approved outputs (`Candidate`, `Placeholder`, fixed generic letters).
2. No broad exception swallowing that returns "ok" outputs.
3. No fake fallbacks that simulate LLM success.
4. Node shape is mandatory: `contract.py`, `logic.py`, `node.py` (plus `prompt/` for LLM nodes); I/O is centralized in `src/core/io/`.
5. Every approved artifact requires valid provenance and hash-checkable input refs.
6. Downstream nodes must consume only approved upstream artifacts.
7. Style consistency:
   - concise, explicit, self-explanatory code,
   - small focused functions,
   - no cross-domain leakage (`core` vs `ai`).

---

## Step Plan

## Pre-Step S - Scraping Recovery (Before Everything)

Final state:
- Deterministic scraping tools exist in PhD 2.0 core.
- Raw ingestion paths can be created from URL/listing and from existing legacy raw data.

Current state:
- Scraping logic exists in original `phd/src/scraper`, not fully integrated as first-class PhD 2.0 core tools.

Add in this step:
- Port/adapt scraping modules into `src/core/tools/scraping/`.
- Add CLI surface for scraping/import flows.
- Ensure outputs align with PhD 2.0 data layout.

Gate:
- Deterministic tests pass.
- HITL: run scraping/import on one real job and inspect `raw/` artifacts.

---

## Step 0 - Recover Non-Deterministic Runtime (LLM Foundation)

Final state:
- Shared AI runtime exists for all LLM nodes (prompt loading, schema parse, retry policy, explicit failure behavior).
- No node uses silent stub fallback as success.

Current state:
- LLM behavior is fragmented and partially stubbed.

Add in this step:
- Build `src/ai/llm/` shared layer.
- Port reusable patterns from original `phd` graph agent/parser stack.
- Enforce explicit failure if model output is invalid/unavailable.

Gate:
- Contract-level automated checks pass.
- HITL smoke call succeeds against one real node prompt flow.
- Human approval required.

---

## Step 1 - Ingest Node

Final state:
- Real legacy raw import + normalized ingest state/provenance.

Current state:
- Basic import exists.

Add in this step:
- Harden contracts and metadata.
- Ensure deterministic, auditable ingest artifacts.

Gate:
- Deterministic tests.
- HITL artifact inspection (`raw/`, `nodes/ingest/*`).

---

## Step 2 - Extract_Understand Node

Final state:
- Real extraction of requirements, themes, responsibilities, constraints from raw/job docs.

Current state:
- Simplified extraction.

Add in this step:
- Robust extraction logic and stronger structured output contract.

Gate:
- Deterministic tests.
- HITL review of extracted understanding against source job text.

---

## Step 3 - Translate Node

Final state:
- Real translation policy with explicit no-op only when source equals target.

Current state:
- Partial field translation.

Add in this step:
- Expand translated fields used downstream.
- Tight contract around language metadata.

Gate:
- Deterministic tests.
- HITL inspect translated artifacts.

---

## Step 4 - Match Node (LLM)

Final state:
- Real matcher behavior (ported/adapted from original phd logic/prompt strategy), no fake success fallback.

Current state:
- Placeholder/stub path still possible.

Add in this step:
- Integrate recovered LLM runtime.
- Implement real evidence/claim mapping output.
- Keep prompt locality per node.

Gate:
- Automated: contract + artifact + review file generation.
- HITL: semantic review on real jobs in `decision.md`.
- Human approval required.

---

## Step 5 - Review_Match Node

Final state:
- Strict decision enforcement (`approve`, `request_regeneration`, `reject`) and correct branching signal.

Current state:
- Parsing exists; branch semantics need explicit guarantee.

Add in this step:
- Deterministic decision-to-routing output.
- Strong stale hash + ambiguity rejection behavior.

Gate:
- Deterministic parser tests.
- HITL approve/regenerate/reject loop test.

---

## Step 6 - Build_Application_Context Node (LLM)

Final state:
- Grounded context built from approved mapping + profile + constraints.

Current state:
- Simplified aggregation.

Add in this step:
- Real synthesis logic with claim traceability and policy enforcement.

Gate:
- Automated: schema/artifacts/provenance.
- HITL: inspect context quality and grounding.

---

## Step 7 - Review_Application_Context Node

Final state:
- Strict review semantics with replay protection and downstream-safe approved artifact.

Current state:
- Basic review behavior exists.

Add in this step:
- Harden deterministic review application and routing signal.

Gate:
- Deterministic tests.
- HITL review/decision/resume cycle.

---

## Step 8 - Generate_Motivation_Letter Node (LLM)

Final state:
- Real letter generation using approved claims only, with consumed refs.

Current state:
- Generic templated behavior.

Add in this step:
- Real node-local prompt behavior via shared AI runtime.
- Policy checks against unapproved claims.

Gate:
- Automated: contract/artifact/provenance/policy checks.
- HITL: human content review on real job.

---

## Step 9 - Review_Motivation_Letter Node

Final state:
- Deterministic review decision application and approved reviewed artifact with provenance.

Current state:
- Basic review-state replacement.

Add in this step:
- Robust decision-application logic and consistency checks.

Gate:
- Deterministic tests.
- HITL decision/validate/resume cycle.

---

## Step 10 - Tailor_CV Node (LLM)

Final state:
- Real CV tailoring from approved context + reviewed motivation.

Current state:
- Minimal markdown summary behavior.

Add in this step:
- Proper tailored CV output for rendering path.
- Claim policy enforcement.

Gate:
- Automated: schema + policy checks.
- HITL: inspect CV semantic quality and grounding.

---

## Step 11 - Review_CV Node (Deterministic)

Final state:
- CV review decisions are parsed deterministically with three states and produce approved CV artifacts.

Current state:
- CV output proceeds without a dedicated review gate.

Add in this step:
- Add `review_cv` node for explicit CV approval/regeneration/rejection.
- Require validated `decision.json` before CV is considered approved.

Gate:
- Deterministic parser tests.
- HITL decision/validate/resume cycle for CV review.

---

## Step 12 - Draft_Email Node (LLM)

Final state:
- Real email generation grounded in approved context, not generic template.

Current state:
- Generic static-like email structure.

Add in this step:
- Prompt-driven constrained output tied to job and approved claims.

Gate:
- Automated: schema/artifacts.
- HITL: semantic review of email.

---

## Step 13 - Review_Email Node (Deterministic)

Final state:
- Email review decisions are parsed deterministically with three states and produce approved email artifacts.

Current state:
- Email output proceeds without a dedicated review gate.

Add in this step:
- Add `review_email` node for explicit email approval/regeneration/rejection.
- Require validated `decision.json` before email is considered approved.

Gate:
- Deterministic parser tests.
- HITL decision/validate/resume cycle for email review.

---

## Step 14 - Render Node (Deterministic)

Final state:
- Actual DOCX/PDF rendering pipeline outputs.

Current state:
- Markdown passthrough.

Add in this step:
- Integrate production renderer stack.
- Produce real render artifacts and provenance.

Gate:
- Deterministic tests.
- HITL inspect generated PDFs.

---

## Step 15 - Package Node (Deterministic)

Final state:
- Final application bundle/PDF + manifest with hashes + provenance.

Current state:
- Markdown concatenation.

Add in this step:
- Real merge/package/compression flow and final manifest.

Gate:
- Deterministic tests.
- HITL final package inspection for real job case.

---

## Step Completion Template (Use Every Time)

- Step ID:
- Target node/tool:
- Current state summary:
- Final state definition:
- Changes introduced:
- Automated checks run:
- HITL run command(s):
- Artifacts inspected:
- Result: PASS / FAIL
- Human approval: APPROVED / REWORK

---

## Definition of Done (Whole Rebuild)

1. All steps S + 0..15 approved in sequence.
2. No placeholder or generic hardcoded outputs in approved artifacts.
3. All review gates enforce strict deterministic parsing and stale-hash checks.
4. LLM node acceptance achieved through HITL on real job data.
5. Rendering/packaging produce real final deliverables with manifest + provenance.
6. Style and architecture boundaries preserved with no drift.
