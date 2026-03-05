# Changelog

## 2026-03-05

- Refactored documentation into concept-oriented folders to reduce ambiguity between philosophy, graph design, templates, business rules, and reference material.
- Moved graph docs to `docs/graph/` and philosophy docs to `docs/philosophy/`.
- Moved policy docs to `docs/business_rules/` and schema/glossary docs to `docs/reference/`.
- Moved template discipline docs to `docs/templates/`, including taxonomic LLM templates under `docs/templates/llm/`.
- Moved prompt specifications under templates to `docs/templates/prompts/`.
- Added `docs/index/README.md` and `docs/index/conceptual_tree.md` as the canonical navigation and conceptual tree for documentation maintenance.
- Added `docs/index/canonical_map.md` and `docs/index/pruning_plan.md` to make canonical ownership and migration cleanup explicit.
- Added compatibility stubs in legacy paths (`docs/architecture/`, `docs/overview/`, `docs/prompts/`) that point to canonical moved documents.
- Updated top-level `README.md` documentation map to reflect the new structure and canonical paths.
- Added root `.gitignore` to exclude `.serena/`, `.pytest_cache/`, and Python cache artifacts.

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
