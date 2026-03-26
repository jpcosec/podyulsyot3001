# Changelog

## 2026-03-26

- Normalized implementation planning docs for node editor refactor.
- Fixed ordering/dependency conflicts across `plan/steps/README.md` and `plan/IMPLEMENTATION_ORDER.md`.
- Added preflight and final validation steps (`SPEC_GRP_001_step00_prereqs.md`, `step-05-final-validation.md`).
- Updated key specs to avoid circular dependency traps, phantom imports, and drag/history inconsistencies.
- Replaced per-step E2E expectations with local verification guidance and consolidated E2E at the end.
- Repaired core documentation links and updated reviewer entrypoint to real repository paths.
- Added GRP-001 Step 00 prereq artifacts: graph data provider module, worker smoke baseline, and QA preflight documentation.
- Implemented UI-001-01 shadcn setup in `apps/review-workbench` with required UI primitives and utility wiring.
