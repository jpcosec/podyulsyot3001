# Extract Understand Node (from dev branch)

**Why deferred:** Current focus is pipeline orchestration. This node's business logic exists on the dev branch and can be ported once the unified pipeline runs end-to-end.
**Last reviewed:** 2026-03-29

## What it does (dev branch reference)

LLM-based structured extraction from raw job posting text. Takes `IngestedData.raw_text` (scraped+translated markdown) and produces `JobUnderstandingExtract`:

### Output contract (from dev `src/nodes/extract_understand/contract.py`)

```python
JobUnderstandingExtract:
  job_title: str
  analysis_notes: str                    # extraction rationale
  requirements: list[JobRequirement]
    - id: str                            # e.g. "REQ_001"
    - text: str                          # human-readable requirement
    - priority: "must" | "nice"
    - text_span: TextSpan                # source location in raw_text
  constraints: list[JobConstraint]
    - constraint_type: str
    - description: str
  risk_areas: list[str]
  contact_info: ContactInfo              # primary detected contact
  contact_infos: list[ContactInfo]       # all detected contacts
  salary_grade: str | None               # e.g. "TV-L E13"
```

### Deterministic post-processing

After LLM extraction, the node runs:
- Email detection via regex
- Name detection via regex (PhD titles, normal names)
- Text span resolution (line/offset locations for requirements)
- Contact merging (dedup LLM contacts with regex-detected ones)
- Salary grade detection via regex (E12, TV-L E15, etc.)

### What the refactored branch needs

When porting, rewrite as a native LangChain `with_structured_output()` call. The dev branch uses a custom LLM wrapper — replace with the same pattern used in `match_skill/graph.py`. Keep the deterministic post-processing as-is.

## Other dev branch nodes to port later

These exist on dev but are not yet in the refactored branch:

- **render node**: Copies markdown from generate_documents to render directory, computes SHA256 manifest. Currently the refactored branch has `src/core/tools/render/` which is more advanced (Pandoc + Jinja2 + multi-engine).
- **package node**: Copies rendered docs to `final/`, verifies hash integrity, creates `PackageManifest`.
- **build_application_context, tailor_cv, draft_email, review_* nodes**: Referenced in dev graph edges but NOT implemented. These are future scope.

## Linked TODOs

- `src/` — `# TODO(future): port extract_understand LLM node from dev branch — see future_docs/new_feature/extract_understand_node.md`
