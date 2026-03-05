# PhD 2.0 Rebuild Index Checklist

This is the execution index for the rebuild. Complete steps in order and do not advance without explicit human approval.

Reference docs:

- `plan/phd2_stepwise_plan.md`
- `plan/template/README.md`
- `docs/philosophy/structure_and_rationale.md`
- `docs/operations/tool_interaction_and_known_issues.md`

## Step Checklist

- [ ] **Pre-Step S - Scraping Recovery**: integrate deterministic scraping/import tooling into PhD 2.0 layout and verify `raw/` artifacts on real jobs.
- [ ] **Step 0 - Non-Deterministic Runtime Recovery**: rebuild shared LLM runtime, remove silent fallback success paths, and validate model-path behavior.
- [ ] **Step 1 - Ingest**: implement robust legacy raw import with normalized ingest artifacts and provenance.
- [ ] **Step 2 - Extract_Understand**: extract structured requirements/themes/responsibilities/constraints from real job source artifacts.
- [ ] **Step 3 - Translate**: enforce translation policy (no-op only on same source/target language) and produce canonical translated fields.
- [ ] **Step 4 - Match (LLM)**: implement real matching logic and evidence/claim mapping with review-ready outputs.
- [ ] **Step 5 - Review_Match**: enforce strict review decisions and deterministic routing (`approve`, `request_regeneration`, `reject`).
- [ ] **Step 6 - Build_Application_Context (LLM)**: generate grounded application context from approved mapping, profile, and constraints.
- [ ] **Step 7 - Review_Application_Context**: apply deterministic review semantics with replay protection and approved output safety.
- [ ] **Step 8 - Generate_Motivation_Letter (LLM)**: generate motivation letter from approved claims only, with traceable claim consumption.
- [ ] **Step 9 - Review_Motivation_Letter**: apply edits deterministically and preserve provenance for approved motivation artifacts.
- [ ] **Step 10 - Tailor_CV (LLM)**: produce render-ready tailored CV content grounded in approved context and motivation.
- [ ] **Step 11 - Review_CV**: validate CV draft decisions with strict parser states and route continue/regenerate/reject.
- [ ] **Step 12 - Draft_Email (LLM)**: draft grounded, job-specific application email without generic fallback templates.
- [ ] **Step 13 - Review_Email**: validate email draft decisions with strict parser states and route continue/regenerate/reject.
- [ ] **Step 14 - Render**: produce real DOCX/PDF render outputs from approved artifacts.
- [ ] **Step 15 - Package**: assemble final application bundle/PDF with manifest hashes and provenance.

## Completion Rule

For every step above, mark complete only when all three are true:

1. deterministic checks for that step pass,
2. HITL run is executed on real job data,
3. human approval is explicitly recorded.
