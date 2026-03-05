# Taxonomic LLM Template Folder

Related references:

- `docs/philosophy/execution_taxonomy_abstract.md`
- `docs/templates/taxonomy_template_catalog.md`
- `docs/templates/node_template_discipline.md`
- `docs/architecture/core_io_and_provenance_manager.md`

## Purpose

This folder provides deep implementation templates for LLM logic by taxonomy category.

It defines, for each template:

- entries (required inputs),
- outputs (artifacts and schemas),
- structure (logic and contract shape),
- prompt management rules.

## Reading order

1. `00_general_llm_call_template.md`
2. `10_llm_extracting_template.md`
3. `20_llm_matching_template.md`
4. `30_llm_redacting_template.md`
5. `40_llm_reviewing_assistance_template.md`

## Scope boundary

- These are logic and contract templates.
- Deterministic review-gate authority remains outside this folder and is implemented by non-LLM review parser nodes.
