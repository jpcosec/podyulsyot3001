# Changelog

## 2026-03-18

- Added behavior-only node editor specification in `docs/architecture/node_editor_behavior_spec.md`, defining canonical rules for node properties, relation visibility, focus/edit modes, composition handling, visual mapping configurability, fullscreen workspace + collapsible sidebar behavior, and sandbox isolation requirement.
- Refined `docs/architecture/node_editor_behavior_spec.md` with explicit editor state transitions, single-selection rules, save/discard lifecycle, deterministic relation/node lifecycle actions, collapsed-composition behavior, and filter conflict guarantees for active edit targets.
- Updated `docs/architecture/node_editor_behavior_spec.md` edit-mode contract for the current node-to-node phase to use overlay modal editing (and aligned acceptance checklist AC-10 accordingly).
- Added front-end implementation plan `docs/architecture/node_editor_frontend_implementation_plan.md` for the node-to-node phase, including architecture decisions, phased rollout, acceptance criteria, and risk mitigations based on React Flow patterns.
- Added dedicated sandbox route `/sandbox/node_editor` (with compatibility alias `/sandbox/node_editor_plan`) via `apps/review-workbench/src/pages/NodeEditorPlanPage.tsx`, route wiring in `apps/review-workbench/src/App.tsx`, and discoverability card in `apps/review-workbench/src/pages/SandboxPage.tsx`.
- Reworked `/sandbox/node_editor` into a simple node-only editor in `apps/review-workbench/src/pages/NodeEditorSandboxPage.tsx` (node focus mode, handle-based node-to-node connections, node property modal, relation property modal, dirty/save/discard workflow, relation toggle/filter). To run and view: `./scripts/dev-all.sh` then open `http://127.0.0.1:4173/sandbox/node_editor`.
- Added markdown compliance matrix `docs/architecture/node_editor_compliance_matrix.md` with requirement-by-requirement status, code evidence references, notes, and weighted coverage scoring against `docs/architecture/node_editor_behavior_spec.md`. To run and verify: `./scripts/dev-all.sh`, open `http://127.0.0.1:4173/sandbox/node_editor`, and compare behavior with the matrix.
- Added feedback follow-up document `docs/architecture/node_editor_feedback_doubts_and_gaps.md` listing open doubts and gaps per operator comment (edit affordance location, auto-layout controls, focus visibility policy, fluid spatial ordering, handle flexibility, and focused-periphery behavior), plus decision points and resolution workflow.
- Updated `docs/architecture/node_editor_behavior_spec.md` with confirmed decisions: primary on-node edit affordance, deterministic auto-layout targets (`Layout All` and `Layout Focus Neighborhood`), default focus policy (1-hop fully visible + non-neighbors dimmed with optional hide toggle), smooth liquid transitions, hover-revealed multi-side handles, floating-edge-style shortest-angle anchoring guidance, view-options panel requirement, and mode badge visibility requirement.
- Added implementation decomposition for next build step in `docs/architecture/node_editor_step1_on_node_edit_breakdown.md` (scope, slices, acceptance criteria, risks, and test checkpoints for on-node edit affordance).
- Added stepwise execution plan `plan/node_editor/node_editor_stepwise_implementation_plan.md` with phased delivery order (on-node edit affordance -> focus readability -> deterministic layout controls -> handle/edge fluidity -> view options -> contextual connect flow), plus per-phase verification protocol. To use: review the plan and execute phases against `http://127.0.0.1:4173/sandbox/node_editor` after running `./scripts/dev-all.sh`.
- Added deterministic base CV graph backend contract and payload builder in `src/interfaces/api/models.py` and `src/interfaces/api/read_models.py` using `data/reference_data/profile/base_profile/profile_base_data.json` as source.
- Added new portfolio endpoint `GET /api/v1/portfolio/base-cv-graph` in `src/interfaces/api/routers/portfolio.py` and backend coverage in `tests/interfaces/api/test_read_models.py`.
- Added frontend contracts and API client support for CV graph payload in `apps/review-workbench/src/types/models.ts` and `apps/review-workbench/src/api/client.ts`.
- Added React Flow-based CV graph editor page `apps/review-workbench/src/pages/CvGraphEditorPage.tsx` with single-canvas graph view, minimap/controls/background, and node side-panel editing.
- Added sandbox and alias routes for CV graph editor (`/sandbox/cv_graph`, `/cv-graph`) in `apps/review-workbench/src/App.tsx` and sandbox navigation entry in `apps/review-workbench/src/pages/SandboxPage.tsx`.
- Added CV graph editor styling in `apps/review-workbench/src/styles.css`.
- Relaxed local development CORS handling in `src/interfaces/api/app.py` with localhost/127.0.0.1 port regex support to keep sandbox UI working when Vite auto-selects a non-default port.
- Added new CV profile domain schema in API models (`CvEntry`, `CvSkill`, `CvDescription`, `CvDemonstratesEdge`, `CvProfileGraphPayload`) and exposed it through `GET /api/v1/portfolio/cv-profile-graph` while preserving the legacy `base-cv-graph` endpoint.
- Added deterministic Entry/Skill graph builder `build_cv_profile_graph_payload` in `src/interfaces/api/read_models.py` with content-slugged description keys, optional skill mastery levels, and explicit Entry->Skill demonstrates edges with description key tracing.
- Expanded backend coverage in `tests/interfaces/api/test_read_models.py` for the new Entry/Skill payload.
- Rebuilt `CvGraphEditorPage` as a three-view React Flow editor (document logic, entry-focused, skill-focused) with node/edge transitions, group expand/collapse, editable Entry/Skill side panels, and link toggling between entries and skills.
- Added `@dagrejs/dagre` for deterministic layouting in focused CV graph views and updated CV graph styling for the new editor controls/forms.
- Extended frontend routes with deep links (`/cv-graph/entry/:entryId`, `/cv-graph/skill/:skillId`) and updated review-workbench docs to reflect the new CV graph architecture.
- Redesigned CV graph editor UI to preserve box-in-box group/entry nesting while adding entry click-to-expand right-side inline editing panels, in-node description editing with add controls, and repurposed side panel skill palette behavior.
- Added skill mastery scale support in `apps/review-workbench/src/lib/mastery-scale.ts` (name + numeric level + intensity), and applied mastery-intensity category coloring plus always-visible labels to skill ball nodes.
- Added custom React Flow node components (`EntryNode`, `SkillBallNode`, `GroupNode`) under `apps/review-workbench/src/components/cv-graph/` and switched matching interactions to handle-based `onConnect` linking.
- Integrated Tailwind CSS in `apps/review-workbench` (Tailwind + PostCSS + Autoprefixer) while preserving existing CSS variable theme and module-level styles.
- Fixed CV graph interaction bubbling in node buttons (`EntryNode`, `SkillBallNode`) so entry focus/expand and skill selection no longer double-toggle through overlapping React Flow node click handlers.
- Hardened graph matching behavior in `CvGraphEditorPage` by centralizing entry/skill connection-pair validation, rejecting non entry-skill pairs, and auto-focusing the connected entry/skill after successful `onConnect`.
- Removed top-level Dagre auto-layout from `CvGraphEditorPage` and restored deterministic horizontal group placement to preserve the intended box-in-box document structure visibility.
- Improved initial graph usability by default-collapsing the large skills group, reducing initial fit complexity, and adding React Flow `minZoom` tuning plus instance-driven fit refresh when node topology changes.

## 2026-03-17

- Started ADR-001 implementation with a Phase 0 UI-first foundation scaffold.
- Added FastAPI review API under `src/interfaces/api/` with:
  - portfolio summary endpoint (`/api/v1/portfolio/summary`),
  - job timeline endpoint (`/api/v1/jobs/{source}/{job_id}/timeline`),
  - match review payload endpoint (`/api/v1/jobs/{source}/{job_id}/review/match`),
  - API health endpoint (`/health`),
  - Neo4j connectivity check endpoint (`/api/v1/neo4j/health`).
- Added filesystem read-model adapters for job timeline and review queue groundwork in `src/interfaces/api/read_models.py` and test coverage in `tests/interfaces/api/test_read_models.py`.
- Added API runner CLI entrypoint `src/cli/run_review_api.py`.
- Added React + TypeScript review workbench scaffold at `apps/review-workbench/` with:
  - routing (`Portfolio` and per-job screens),
  - ADR view shells (`View 1` Graph Explorer, `View 2` Document-to-Graph, `View 3` Graph-to-Document),
  - Cytoscape integration and Slate editor integration,
  - API client wiring to the new backend endpoints.
- Added Neo4j local bootstrap via `docker-compose.neo4j.yml`.
- Added `.env.example` with UI/API/Neo4j environment variables.
- Added Phase 0 local setup runbook `docs/operations/ui_workbench_phase0_bootstrap.md` and indexed it in operations docs and root README.
- Updated `.gitignore` for frontend artifacts (`node_modules/`, `apps/review-workbench/dist/`).
- Added planning governance protocol `plan/worktree_planning_protocol.md` defining: docs=current-state only, plan=next-step tracking, worktree-per-plan policy, and mandatory start/end session continuity checklist.
- Added code-adjacent dependency map `src/DEPENDENCY_GRAPH.md` to support impact analysis and test planning by module dependency.
- Added code-local module docs `src/interfaces/api/README.md` and `apps/review-workbench/README.md` to reduce rediscovery overhead.
- Expanded `.gitignore` for runtime artifacts (`artifacts/`) and TypeScript build metadata (`*.tsbuildinfo`).
- Enforced data non-tracking policy by broadening `.gitignore` to `data/` and removing tracked profile data from git index.
- Added protocol enforcement CLI `src/cli/check_repo_protocol.py` and wired command reference in root `README.md`.
- Added enforcement automation: `.pre-commit-config.yaml`, native hooks in `.githooks/`, and CI workflow `.github/workflows/repo-protocol.yml`.
- Added clean-tree pre-push gate (`--require-clean-tree`) to enforce that local code changes are committed before push.
- Added cross-project rollout CLI `src/cli/propagate_protocol_pack.py` to propagate enforcement hooks/checker/workflow into other repositories (dry-run and apply modes).
- Expanded code-adjacent documentation with `src/core/README.md`, `src/ai/README.md`, `src/nodes/README.md`, and `src/cli/README.md`.
- Expanded `src/DEPENDENCY_GRAPH.md` with pipeline subgraph dependencies and impact-based test mapping for `src/core`, `src/ai`, and `src/nodes`.
- Restructured graph/architecture docs to current-state-only surfaces and moved future-state specs to planning space (`plan/spec/`, `plan/adr/`).
- Added unified dev startup script `scripts/dev.sh` to launch both UI and API in a single terminal with Ctrl+C cleanup.
- Added full-stack startup script `scripts/dev-all.sh` to launch Neo4j + API + UI together and bootstrap Neo4j schema constraints.
- Improved `scripts/dev-all.sh` to auto-select the next free API/UI ports when defaults are occupied.
- Added `plan/adr_001_next_actions.md` — forward-looking action plan with critical path analysis, concrete per-action tasks for completing Phases 0-3 (install deps, start Neo4j, profile migration script, job migration script, dual-read API, comment model, node editor, text-to-node creation, review decision UI, Slate.js integration), testing strategy, and environment dependencies.
- Restored full ADR-001 content to `plan/adr/adr_001_ui_first_knowledge_graph_langchain.md` — previous session had reduced it to a 31-line stub during docs/plan boundary enforcement. Full decision record now restored: context, decisions, Neo4j schema (5 domains, ~20 node types), three view modes, LangChain migration table, consequences, risks, alternatives, deployment.
- Added frontend component sandbox route `/sandbox` with fake data in `apps/review-workbench/src/pages/SandboxPage.tsx`, including isolated previews for `StageStatusBadge`, `JobTree`, `GraphCanvas`, and `RichTextPane`, plus mock View 2 and View 3 shells for quick UI validation without backend/API dependencies.
- Switched graph rendering preference from Cytoscape to Diagrammatic-UI in the frontend: `GraphCanvas.tsx` now uses `diagrammatic-ui` `Graph`, removed `cytoscape`/`react-cytoscapejs` dependencies and `src/react-cytoscapejs.d.ts`, and updated ADR/tracker/docs references to reflect Diagrammatic-UI as the preferred graph layer.
- Replaced `RichTextPane` placeholder with a functional highlight-based text editor in `apps/review-workbench/src/components/RichTextPane.tsx`: select text spans, assign relation categories (`requirement`, `deadline`, `payment`, `contact`, `institution`, `other`), create color-coded highlights, and manage corresponding node cards in a sidebar with matching colors and remove actions.
- Added highlight editor styling in `apps/review-workbench/src/styles.css` (`highlight-editor`, toolbar, canvas, sidebar, cards) including responsive layout and active-selection visuals.
- Added a graph error boundary in `apps/review-workbench/src/components/GraphCanvas.tsx` so Diagrammatic-UI runtime failures no longer blank the page; when graph render fails, views fall back to a node/edge summary panel and keep the text editor and review UI usable.
- Split routes so text tagging is isolated from sandbox noise: added dedicated `TextTaggerPage` at `/sandbox/text_tagger` (and alias `/text-tagger`), removed embedded `RichTextPane` from `SandboxPage`, and linked sandbox to the dedicated text tagger route.
- Rebuilt `RichTextPane` as a drag-to-category text tagger using `@dnd-kit/core`: select text on the left, drag selection chip into responsive category boxes on the right, create color-coded highlights, store exact captured text per note, show category summary as first occurrence + total count, and support inline double-click editing for card fields (node label/details) plus subcategory editing for `other` notes.
- Improved text tagger UX for faster categorization: when text is selected, category boxes now show numbered quick-add hints (`Click or press 1-6 to add`), clicking a category box adds the selected text without dragging, and note cards are draggable (Move handle) so existing notes can be re-categorized by dropping into another category box.
- Refactored text tagger node model to two editable main categories (`requirement`, `info`) with editable subcategories for both. Added collapsible note cards (Expand/Collapse), searchable note list, and scrollable notes container in the sidebar; updated quick-add shortcuts to `1` (Requirement) and `2` (Info).
- Upgraded note cards into full form cards: whole-card draggable recategorization, always-expanded on creation, subcategory dropdowns driven by code parameters (`SUBCATEGORY_OPTIONS`) with `other` custom input support, and red clickable basket removal control.
- Restructured categorization UI into explicit two levels (main tabs + subcategory tabs), updated visual semantics (requirement uses red intensity levels; info subcategories use distinct non-red colors), removed dedicated collapse/expand button, and switched collapse/expand to card-body click behavior (remove basket remains isolated).
- Refined category hierarchy behavior: level 1 now renders as tab-style main categories only (no "All categories" tab), level 2 remains subcategory boxes with clear visual separation; requirement main/sub levels use red spectrum and info subcategories use mixed palette.

## 2026-03-16

- Updated `plan/index_checklist.md` to reflect actual implementation status: marked Pre-Step S through Step 6-13 (collapsed) as complete, added explicit gap items for missing review gates/core-io/sync_json_md, and added ADR-001 migration phases.
- Added ADR-001 (`docs/architecture/adr_001_ui_first_knowledge_graph_langchain.md`): UI-first review workbench with Neo4j knowledge graph, full LangChain migration, and hybrid scraping architecture. Supersedes `plan/subplan/langchain_langgraph_adoption_evaluation.md` (Option B hybrid replaced by full migration). Defines three view modes (Graph Explorer, Document-to-Graph, Graph-to-Document), Neo4j schema with TextSpan provenance, comment/annotation model with feedback categorization, and 6-phase implementation sequence.
- Updated `docs/architecture/README.md` to index ADR-001 under new Architecture Decision Records section.
- Updated `docs/index/canonical_map.md` to add Architecture Decisions section and mark `langchain_langgraph_adoption_evaluation.md` as superseded.
- Revised ADR-001 schema based on scraping gap analysis of 3 TU Berlin jobs (201637, 201601, 201578). Expanded Job domain from 4 node types to 12: added `OrganizationalUnit`, `Person`, `ResearchContext`, `ResearchProject`, `PositionTerms` (replacing flat `Constraint` bag), `TeachingDuty`, `ApplicationMethod`, `DomainTag`, `LegalNotice`, `SourceDocument`. Added `domain` enum to `Requirement` (education, language, technical, research, teaching, soft_skill, administrative). Added `TextSpan` provenance model for View 2 bidirectional highlighting.

## 2026-03-13

- Updated regeneration behavior in `src/nodes/match/logic.py` so review rounds focus only on `patch` requirements from prior feedback, while non-scoped requirements are rendered as context-only rows outside the revalidation loop.
- Updated match review rendering to include explicit `Req ID` in actionable tables and to emit dedicated regeneration-scope sections during regeneration rounds.
- Extended match prompt input in `src/nodes/match/prompt/user_template.md` to include optional `<regeneration_scope>` guidance so model updates stay centered on requested patch points.
- Updated `src/nodes/review_match/logic.py` table parser to support `Req ID`-keyed scoped decisions (subset review) while preserving strict validation for unknown IDs and invalid checkbox markup.
- Added/updated tests in `tests/nodes/match/test_match_logic.py` and `tests/nodes/review_match/test_review_match_logic.py` to cover scoped regeneration review behavior.
- Wired post-approval document generation into prep flow by routing `review_match.approve` to `generate_documents` before terminal `package` in `src/graph.py`.
- Updated prep graph helper tests (`tests/core/graph/test_prep_match_helpers.py`) for the new `generate_documents` node registration.
- Updated graph docs (`docs/graph/nodes_summary.md`, `docs/graph/node_io_matrix.md`) to reflect the current runnable flow: `scrape -> translate_if_needed -> extract_understand -> match -> review_match -> generate_documents -> package`.
- Fixed `generate_documents` prompt XML-tag validation drift in `src/nodes/generate_documents/prompt/user_template.md` by removing a stray literal `<candidate_base_cv>` mention from instructions that conflicted with strict tag counting.
- Added prompt-path coverage test in `tests/nodes/generate_documents/test_generate_documents_logic.py` to ensure real template rendering passes XML boundary validation.
- Hardened `src/nodes/generate_documents/contract.py` normalization to tolerate common Gemini structured-output drift (`cv_summary`/`email_body` lists, CV injection alias fields such as `achievements_to_inject` and `statements`, nested `email_deltas.email_body`, and partial `letter_deltas` payloads).
- Extended profile normalization in `src/nodes/generate_documents/logic.py` to ensure template-safe optional fields (`publications[].url`, `languages[].note`) are always present under strict Jinja rendering.
- Added contract tests in `tests/nodes/generate_documents/test_contract.py` for drift normalization paths used by live generation runs.

## 2026-03-12

- Added deterministic migration planning doc `plan/subplan/deterministic_parity_migration_from_phd.md`, defining scope, legacy-to-target deterministic inventory, phased work packages (`core/io`, review substrate, delivery chain, observability), risks, and acceptance gates.
- Added product/operations planning doc `plan/subplan/review_ui_and_flow_observability.md`, defining review workbench scope plus per-job timeline and global portfolio dashboard requirements, rollout phases, and validation constraints.
- Added architecture evaluation doc `plan/subplan/langchain_langgraph_adoption_evaluation.md`, including option matrix (custom, hybrid, full migration), non-negotiable safety constraints, required spikes, decision gate, and recommended incremental path.
- Updated planning/documentation indexes to include new priority-track docs: `plan/index_checklist.md`, `docs/index/canonical_map.md`, `docs/index/README.md`, and root `README.md`.

## 2026-03-11

- Added incident diagnosis document `docs/operations/reviewed_jobs_pipeline_diagnosis.md` for reviewed-job pipeline resume failures, including reproduction evidence, root-cause analysis (legacy review hash-lock mismatch, empty checkpoints, missing `langgraph` dependency), and a recovery/verification plan.
- Updated `docs/operations/README.md` to index the new diagnosis document.
- Added recovery CLI `src/cli/migrate_review_hash_lock.py` to migrate legacy reviewed `nodes/match/review/decision.md` files into hash-locked format while preserving existing checkbox decisions and comments, with automatic backup files (`decision.legacy_reviewed*.md`) and `--dry-run` support.
- Added migration tests in `tests/cli/test_migrate_review_hash_lock.py`.
- Added checkpoint-independent batch continuation CLI `src/cli/run_available_jobs.py` to execute available prep-match jobs from artifacts (including regeneration flows) without relying on LangGraph checkpoint history.
- Updated available-jobs planner logic to read the active review surface (`nodes/match/review/decision.md`) before falling back to `decision.json`, avoiding stale-round dry-run decisions.
- Added CLI tests in `tests/cli/test_run_available_jobs.py`.
- Added operator runbook `docs/operations/available_jobs_recovery_runbook.md` and indexed it from `docs/operations/README.md`.
- Applied hash-lock migration and continuation on available TU Berlin jobs: regenerated review rounds for `201578`, `201588`, `201601`, `201606`, and `201695` (now pending review in round 2), generated first review for `201637` (pending review in round 1), and confirmed `201661` as completed on approve route.
- Added comments inventory doc `docs/reference/comments_inventory.md` with collected `#TODO`, `<!-- -->`, and `<--` marker occurrences, and indexed it in `docs/reference/README.md`.
- Refined `docs/reference/comments_inventory.md` into a path-tree view and explicitly excluded `data/` and `pipeline/` from the analysis, per operator request.
- Extended `docs/reference/comments_inventory.md` scope to include `docs/` (excluding self-reference) and reported docs-specific comment-marker counts.

## 2026-03-07

- Added `docs/reference/data_management_actual_state.md` as the canonical implementation-first data management/usage/meaning reference, documenting current artifact paths, control-plane payload usage, match review round semantics, and explicit gaps versus target-state architecture.
- Updated documentation indexes to include the new canonical entrypoint for current runtime data behavior: `docs/reference/README.md`, `docs/index/canonical_map.md`, `docs/index/README.md`, and root `README.md`.
- Refactored `docs/graph/node_io_matrix.md` to explicitly split **current implemented node I/O** (prep-match runnable path plus `generate_documents` status) from **target-state I/O contracts**, reducing ambiguity between real runtime behavior and planned architecture.
- Refactored `docs/graph/nodes_summary.md` with the same explicit split between **current implemented runtime graph** and **target full-graph contract**, including separate routing semantics, checkpoint/resume invariants, node role summaries, and Mermaid views.
- Added `docs/graph/match_review_cycle.md` as an implementation-first walkthrough of the `match <-> review_match` loop, covering artifact writes, round immutability, hash-lock validation, decision parsing, regeneration semantics, and operator resume workflow.
- Split UI migration planning into two dedicated docs:
  - internal engineering subplan: `plan/subplan/ui_review_cycle_adaptation_internal.md`
  - designer handoff brief: `plan/subplan/ui_review_cycle_designer_handoff.md`

## 2026-03-06

- Backfilled TU Berlin jobs `201399` and `201553` from archived translated artifacts (`/home/jp/phd-workspaces/phd/data/pipelined_data/tu_berlin`), restoring local raw inputs and synthetic `scrape`, `translate_if_needed`, and `extract_understand` approved states under `data/jobs/tu_berlin/`.
- Updated `data/jobs/tu_berlin/_batch_extract_report.json` to mark `201399` and `201553` as successfully extracted with requirement/constraint counts derived from the restored artifacts.
- Executed matching for backfilled jobs `201399` and `201553` (creating `nodes/match/approved/state.json` and `nodes/match/review/` round artifacts) and updated `data/jobs/tu_berlin/_batch_match_report.json` to reflect `pending_review` status.
- Hardened Step 5 (`review_match`) fail-closed behavior in `src/nodes/review_match/logic.py` by enforcing `source_state_hash` validation, auto-regenerating unreviewed legacy `decision.md` files without hashes, and raising actionable errors for invalid checkbox markup.
- Updated match decision rendering in `src/nodes/match/logic.py` to always include review front matter (`source_state_hash`, node, job_id, round) and default optional prompt fields (`prev_round`, `round_feedback`) to prevent undefined-template failures.
- Added/updated tests for Step 5 hardening (`tests/nodes/match/test_match_logic.py`, `tests/nodes/review_match/test_review_match_logic.py`) including stale-hash and invalid-markup failure cases; full test suite passes (`51 passed`).
- Added planning proposal `plan/step6_13_delta_generation_and_text_reviewers.md` describing the Step 6-13 delta-first generation strategy, deterministic assembly split, and explicit integration plan for text reviewer assistance nodes (non-routing).
- Refined the Step 6-13 proposal with confirmed implementation decisions: `generate_documents` as graph-visible node, id-based CV injections, deterministic Jinja template rendering (CV/letter/email), anti-fluff as reviewer indicator, and plain-language definition of `text-reviewer-assist`.
- Updated the Step 6-13 proposal so `text-reviewer-assist` is deterministic-only (no LLM call), producing non-routing indicator artifacts for human review support.
- Implemented `generate_documents` as a graph-visible node package under `src/nodes/generate_documents/` with structured delta contracts, node-local prompts, deterministic Jinja templates (`cv_template.jinja2`, `cover_letter_template.jinja2`, `email_template.jinja2`), id-based CV injection validation, and deterministic assist indicator artifacts (`assist/proposed/state.json`, `assist/proposed/view.md`).
- Added tests for the new node and contracts (`tests/nodes/generate_documents/test_contract.py`, `tests/nodes/generate_documents/test_generate_documents_logic.py`) and validated repository health with full suite pass (`55 passed`).

## 2026-03-05

- Refactored documentation into concept-oriented folders to reduce ambiguity between philosophy, graph design, templates, business rules, and reference material.
- Moved graph docs to `docs/graph/` and philosophy docs to `docs/philosophy/`.
- Moved policy docs to `docs/business_rules/` and schema/glossary docs to `docs/reference/`.
- Moved template discipline docs to `docs/templates/`, including taxonomic LLM templates under `docs/templates/llm/`.
- Moved prompt specifications under templates to `docs/templates/prompts/`.
- Added `docs/index/README.md` and `docs/index/conceptual_tree.md` as the canonical navigation and conceptual tree for documentation maintenance.
- Added `docs/index/canonical_map.md` and `docs/index/pruning_plan.md` to make canonical ownership and migration cleanup explicit.
- Removed temporary compatibility stubs after canonical links were migrated to reduce duplicate documentation surfaces.
- Updated top-level `README.md` documentation map to reflect the new structure and canonical paths.
- Added root `.gitignore` to exclude `.serena/`, `.pytest_cache/`, and Python cache artifacts.
- Added folder-level indexes: `docs/philosophy/README.md`, `docs/graph/README.md`, `docs/templates/README.md`, `docs/business_rules/README.md`, `docs/reference/README.md`, `docs/operations/README.md`, and `docs/architecture/README.md`.
- Reduced cross-document redundancy by moving canonical ownership to single docs and replacing repeated taxonomy/routing/path content with references:
  - taxonomy definitions owned by `docs/philosophy/execution_taxonomy_abstract.md`,
  - flow routing owned by `docs/graph/nodes_summary.md`,
  - artifact structure owned by `docs/reference/artifact_schemas.md`,
  - failure taxonomy owned by `docs/philosophy/structure_and_rationale.md`.
- Added explicit "Authority scope" sections to core docs to reduce future drift and clarify ownership boundaries.
- Merged graph flow documentation into canonical `docs/graph/nodes_summary.md` and removed `docs/graph/graph_definition.md`.
- Added prompt rendering engine specification (Jinja2 + `LogicInput.model_dump()` contract) in `docs/templates/llm/00_general_llm_call_template.md` and `docs/templates/prompts/README.md`.
- Added explicit CLI/LangGraph resume contract to operations docs, including `thread_id = f"{source}_{job_id}"`, `review-validate` data-plane behavior, and `graph.invoke(None, config)` resume behavior.
- Added `docs/reference/contract_composition_framework.md` as canonical contract design guidance for envelope/primitive composition and style constraints in `contract.py`.
- Linked contract composition guidance from templates/index/reference docs to make it part of the active implementation path.
- Added extracting taxonomy worked case document: `docs/reference/extracting_contract_case_job_understanding.md` with concrete primitives, `JobUnderstandingExtract` envelope, extracting input contract, `logic.py` integration, and profile normalization extension note.
- Added matching taxonomy worked case document: `docs/reference/matching_contract_case_matrix_and_escape_hatch.md` with matrix primitives, `MatchEnvelope` source-text pointer, deterministic review rendering contract, and manual missing-requirement regeneration flow.
- Added redacting taxonomy worked case document: `docs/reference/redacting_contract_case_traceable_dual_output.md` with style/strategy primitives, dual output envelope (`state` + `markdown_content`), and deterministic consumed-evidence anti-hallucination checks.
- Updated `docs/reference/contract_composition_framework.md` to align canonical primitives and envelopes with matrix-based matching (`EvidenceEvaluation`/`RequirementMapping`), redacting dual-output behavior, and redacting polymorphism over `RedactingStateBase`.
- Added reviewing taxonomy worked case document: `docs/reference/review_contract_case_decision_and_assistance.md` defining deterministic decision parsing (`DecisionEnvelope`) and optional LLM review assistance (`ReviewAssistEnvelope`) as separate contracts.
- Added prompt anatomy standard in `docs/templates/prompts/prompt_anatomy_standard.md`, formalizing the two-file structure (`system.md` + `user_template.md`), XML-style input encapsulation, Jinja2 conditional blocks, and execution-step layout for future prompt refactors.
- Added `docs/architecture/graph_reactivity_protocol.md` to formalize immediate emergent-evidence regeneration vs deferred feedback-memory learning as separate graph reactivity channels.
- Implemented `src/ai/prompt_manager.py` with node-local template loading, strict Jinja2 rendering, and XML-tag boundary validation; added tests in `tests/ai/test_prompt_manager.py`.
- Implemented `src/ai/llm_runtime.py` with structured Gemini execution (`response_schema` JSON mode + strict Pydantic validation) and added runtime unit tests in `tests/ai/test_llm_runtime.py`.
- Added `docs/architecture/graph_state_contract.md` to formalize GraphState as a control-plane ledger (metadata + artifact refs, no business payload embedding).
- Added `src/core/graph/state.py` and `src/core/graph/__init__.py` with typed GraphState contract and `build_thread_id(source, job_id)` helper; added test `tests/core/graph/test_state.py`.
- Added `src/graph.py` as LangGraph orchestration builder with review-loop conditional routing and review interrupt defaults; added tests in `tests/core/graph/test_orchestrator.py`.
- Added `src/nodes/extract_understand/` scaffold with node-local prompts (`prompt/system.md`, `prompt/user_template.md`) and `contract.py` including `analysis_notes` in `JobUnderstandingExtract`.
- Implemented `src/nodes/extract_understand/logic.py` using `PromptManager` + `LLMRuntime` and state-driven input assembly; added tests in `tests/nodes/extract_understand/test_logic.py`.
- Added compatibility runtime export module `src/ai/runtime.py` pointing to the canonical `LLMRuntime` implementation.
- Added ingestion-stage node scaffolding: `src/nodes/scrape/` (`IngestedData` contract + scraping logic) and `src/nodes/translate_if_needed/` (conditional translation normalization logic).
- Updated graph defaults to include prep stages (`scrape -> translate_if_needed -> extract_understand -> match`) before review cycles.
- Added ingestion/prep tests: `tests/nodes/scrape/test_scrape_logic.py` and `tests/nodes/translate_if_needed/test_translate_if_needed_logic.py`; expanded graph orchestrator tests for new default flow.
- Added matching-stage scaffold in `src/nodes/match/` (contract, prompts, and `logic.py`) using strict structured output via `MatchEnvelope`.
- Added review-stage scaffold in `src/nodes/review_match/` with deterministic markdown generation/parsing and `DecisionEnvelope` persistence for review routing.
- Ran batched open-job smoke run (`scrape -> translate_if_needed -> extract_understand`) and persisted report at `data/jobs/tu_berlin/_batch_extract_report.json`.
- Added prep-match graph helpers in `src/graph.py`: `build_prep_match_node_registry()`, `create_prep_match_app()`, and `run_prep_match()` with canonical `thread_id` wiring.
- Added minimal prep-match CLI runner `src/cli/run_prep_match.py` and tests for profile evidence loading in `tests/cli/test_run_prep_match.py`.
- Copied canonical profile base snapshot into this repo at `data/reference_data/profile/base_profile/profile_base_data.json`.
- Updated prep-match CLI profile loader to accept both evidence-list JSON and `profile_base_data.json` shape (auto-transform to `my_profile_evidence`).
- Added session handoff/entrypoint doc: `docs/operations/next_session_entrypoint.md`.
- Updated prep-match runner to use persistent sqlite checkpoints per job (`data/jobs/<source>/<job_id>/graph/checkpoint.sqlite`) enabling `--resume` across CLI invocations.
- Updated match stage to persist `nodes/match/approved/state.json` and bootstrap `nodes/match/review/decision.md` before review interrupt.
- Hardened `MatchEnvelope.decision_recommendation` normalization to tolerate multilingual/free-text model outputs while preserving strict enum contract.
- Updated deterministic `decision.md` rendering to include explicit requirement text and resolved evidence descriptions (not only IDs) for easier human review.
- Refined profile ingestion for matching: moved summary/tagline seeds into `cv_generation_context` in `profile_base_data.json` and stopped emitting `P_SUM` evidence, keeping matching evidence strictly auditable.
- Added migration spec `docs/operations/match_review_rounds_current_state_and_migration.md` describing current round behavior, audit gaps, and required implementation changes for immutable per-round review history.
- Added `src/core/round_manager.py` as infrastructure utility to manage immutable `round_<NNN>` artifacts under `nodes/match/review/rounds/`.
- Refactored `src/nodes/match/logic.py` to use `RoundManager`: each execution creates a new round folder, writes canonical `rounds/round_<NNN>/decision.md`, then mirrors to active `review/decision.md`.
- Implemented fail-closed regeneration input policy in `src/nodes/match/logic.py`: `request_regeneration` now requires a valid latest `feedback.json` with actionable patch entries.
- Implemented feedback patch injection in `src/nodes/match/logic.py`: effective evidence now includes prior round `patch_evidence` artifacts without mutating base profile files.
- Updated `src/nodes/match/prompt/user_template.md` to include optional `<round_feedback>` block for informed regeneration based on previous-round reviewer feedback.
- Refactored `src/nodes/review_match/logic.py` to persist immutable per-round artifacts (`decision.md`, `decision.json`, `feedback.json`) and mirror active `review/decision.json`.
- Added automatic `feedback.json` generation from parsed review decisions, including optional `PATCH_EVIDENCE:` JSON extraction from reviewer comments.
- Added tests for round manager and updated review/match node tests for new round-folder layout and fail-closed regeneration behavior.
- Hardened review checkbox parsing in `src/nodes/review_match/logic.py` to accept human-edited spacing variants (for example `[]` and `[ x]`) while still failing closed on invalid markers.
- Standardized runtime prompts to English for extraction and matching by rewriting node-local prompt files in `src/nodes/extract_understand/prompt/` and `src/nodes/match/prompt/`, with explicit "output text must be in English" rules.
- Normalized job artifact language for `tu_berlin/201397` by converting generated `state.json` content under extract/match approved artifacts to English.

## 2026-03-04

- Started non-LLM bounded-nondeterministic code recovery in `src/core/tools/`.
- Added translation service with bounded retries and explicit `ToolFailureError`/`ToolDependencyError` behavior.
- Added scraping service with listing crawl, URL paging, language heuristic, and explicit fetch failure handling.
- Added initial unit tests for translation and scraping services under `tests/core/tools/`.
- Added human-reviewable demo report for non-LLM recovery: `docs/operations/non_llm_recovery_demo.md`.
- Added rebuild master documentation baseline for PhD 2.0.
- Added architecture rationale document defining layer boundaries, node contracts, and anti-wax controls.
- Added operator guide for HITL interaction flow, review workflow, and troubleshooting.
- Added top-level `README.md` linking the documentation set and defining rebuild principles.
- Added `plan/index_checklist.md` as the root-level execution index for all rebuild steps.
- Moved stepwise rebuild master plan from `docs/` to `plan/phd2_stepwise_plan.md` to keep `docs/` focused on final-state system documentation.
- Added `docs/overview/project_overview.md` with end-to-end purpose, boundaries, runtime model, and quality criteria.
- Added `docs/architecture/graph_definition.md` with canonical graph flow, branch semantics, checkpoints, and node contract expectations.
- Added `docs/overview/document_glossary.md` documenting the meaning of repository docs and runtime artifact files.
- Expanded `docs/operations/tool_interaction_and_known_issues.md` with a concrete operator session and artifact verification checks.
- Updated `README.md` documentation map to separate stepwise plan docs (`plan/`) from final-state system docs (`docs/`).
- Added `docs/architecture/node_io_matrix.md` with node-by-node input/output contracts, review gates, and downstream consumers.
- Added `plan/template/README.md` defining canonical folder templates and checklists for deterministic and AI-powered nodes.
- Standardized review decision model to three states across docs: `approve`, `request_regeneration`, `reject`.
- Updated graph and planning docs to include new review stages: `review_cv` and `review_email`.
- Updated step plan/checklist sequencing to reflect CV/email review gates before render/package (now through Step 15).
- Updated artifact schema documentation to 17 primary artifact types and added reviewed CV/email artifacts.
- Added prompt specs for new review nodes: `docs/prompts/cv_review_parser.md` and `docs/prompts/email_review_parser.md`.
- Added architecture-level execution classification model: classify by LLM usage first, then determinism class only for non-LLM steps.
- Updated node I/O matrix to use execution classes `LLM`, `NLLM-D`, and `NLLM-ND`.
- Added LLM task taxonomy and task-to-category mapping (`extracting`, `matching`, `reviewing`, `redacting`) in graph docs.
- Added `docs/architecture/smart_template_discipline.md` with GraphState contract, retry/fail-stop routing rules, base node package shape, taxonomy templates, and HITL interrupt contract.
- Added `docs/architecture/template_problem_statement.md` to formalize the template-design problem before defining the smart template discipline.
- Added `docs/architecture/core_io_and_provenance_manager.md` to define Data Plane architecture (`WorkspaceManager`, `ArtifactReader/Writer`, `ProvenanceService`) and Control Plane/Data Plane boundaries.
- Added `docs/architecture/core_io_manager.md` as a compatibility alias pointing to the canonical Core I/O + Provenance document.
- Updated architecture docs to remove per-node `reader.py`/`writer.py` from canonical node package shape.
- Updated plan templates to align with centralized I/O discipline.
- Added macro-node/subgraph architecture guidance, including explicit `prep_subgraph = ingest -> extract_understand -> translate` and review-cycle subgraphs.
- Added `docs/architecture/execution_taxonomy_abstract.md` to formalize taxonomy-first classification (`llm-based` vs `no-llm-based`, plus abstract intent/predictability/gate axes) before node/subgraph mapping.
- Added `docs/architecture/taxonomy_template_catalog.md` with implementation templates for each taxonomy leaf and a deterministic review-gate parser complement.
- Refined `docs/architecture/taxonomy_template_catalog.md` after review comments: clarified non-masking retry behavior, added LLM-scope note, added LLM category difference table, and clarified that LLM reviewing is assistance-only (non-gating).
- Added `docs/architecture/taxonomic_llm_templates/` folder with step-by-step deep templates: general LLM call, extracting, matching, redacting, and reviewing-assistance.
- Reworked `00_general_llm_call_template.md` into a concrete runtime template with explicit Gemini structured-call example, typed error contract, and strict prompt/input/output boundaries.

## 2026-03-04 (documentation enrichment)

Enriched documentation from original design docs (`phd/docs/phd 2.0/`) into the rebuild's cleaner structure.

### New documents

- Added `docs/architecture/artifact_schemas.md` with full JSON schemas for all 17 pipeline artifact types, adapted to canonical `nodes/<node>/` layout.
- Added `docs/architecture/claim_admissibility_and_policy.md` with claim admissibility classes (direct/bridging/inadmissible), evidence compatibility rules, coverage transition state machine, downstream consumption policy, and review directive format.
- Added `docs/architecture/feedback_memory.md` with feedback event schema, classification dimensions, three-layer storage model, per-stage retrieval strategy, conflict model, and operational lifecycle pattern.
- Added `docs/architecture/sync_json_md.md` with API surface, behavior lifecycle, staleness protection, parser robustness requirements, safety-critical posture, and 7 adversarial test categories.
- Added `docs/prompts/README.md` as prompt pack index with design principles and artifact path conventions.
- Added 9 prompt specification files: `matcher.md`, `match_review_parser.md`, `application_context_builder.md`, `motivation_letter_writer.md`, `motivation_letter_review_parser.md`, `cv_tailorer.md`, `email_drafter.md`, `cv_renderer.md`, `feedback_distiller.md`.

### Enhanced documents

- Enhanced `docs/architecture/structure_and_rationale.md` with node failure taxonomy (9 types), continuation matrix (fail-stop vs retryable), and retry logging requirements.
- Enhanced `docs/overview/project_overview.md` with Mermaid system diagram, architectural layers (input/interpretation/alignment/generation/delivery), and "human-supervised application alignment system" conceptual framing.
- Enhanced `docs/architecture/graph_definition.md` with review directive format specification and parsing rules for `decision.md` files.
- Enhanced `docs/operations/tool_interaction_and_known_issues.md` with Obsidian integration notes and optional HTML view enhancement mention.
- Enhanced `docs/overview/document_glossary.md` with entries for profile artifacts, feedback artifacts, new architecture docs, and prompt docs.
- Updated `README.md` documentation index with new "Design depth" and "Prompt specifications" sections.
