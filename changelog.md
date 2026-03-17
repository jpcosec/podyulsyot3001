# Changelog

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
