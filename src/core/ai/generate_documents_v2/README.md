# 🏗️ Generate Documents V2

LangGraph-native document generation pipeline that turns canonical ingest artifacts plus profile data into Markdown CV, letter, and email outputs.

## 🏗️ Architecture & Features

The module is organized as a staged graph with explicit subgraphs and persisted per-stage artifacts.

- Top-level graph assembly: `src/core/ai/generate_documents_v2/graph.py`
- State contract: `src/core/ai/generate_documents_v2/state.py`
- Artifact persistence: `src/core/ai/generate_documents_v2/storage.py`
- End-to-end helper pipeline: `src/core/ai/generate_documents_v2/pipeline.py`
- Contracts: `src/core/ai/generate_documents_v2/contracts/`
- Stage nodes: `src/core/ai/generate_documents_v2/nodes/`
- Stage subgraphs: `src/core/ai/generate_documents_v2/subgraphs/`
- Prompt builders: `src/core/ai/generate_documents_v2/prompts/`

Current stage shape in code:

1. load profile inputs
2. ingestion (`J1 -> J2`)
3. semantic bridge / alignment
4. macroplanning / blueprint
5. microplanning / drafting
6. assembly to Markdown bundle
7. explicit profile-update approval (when needed)
8. profile updater

Current limitations that are intentionally not documented as supported behavior:

- the review UI currently exposes approve/reject flows, not full per-field GraphPatch editing
- regional document strategies are not fully implemented; deferred items live in `future_docs/issues/core/ai/generate_documents_v2/`
- profile writeback now requires an explicit approval gate before persistence, but the operator surface is still generic JSON rather than a dedicated profile-diff editor

## ⚙️ Configuration

```env
GOOGLE_API_KEY="your_gemini_key"
GEMINI_API_KEY="your_gemini_key"
```

Profile and section mapping defaults are read from:

- `data/reference_data/profile/base_profile/profile_base_data.json`
- `data/reference_data/profile/section_mapping.json`

## 🚀 CLI / Usage

This module is normally driven through the unified operator CLI.

- Pipeline/API workflow entrypoint: `src/cli/main.py`
- Direct helper for in-process generation: `generate_application_documents()` in `src/core/ai/generate_documents_v2/pipeline.py`
- Graph factory for LangGraph/API use: `build_generate_documents_v2_graph()` in `src/core/ai/generate_documents_v2/graph.py`

Arguments for operator-driven runs are defined in `build_parser()` helpers inside `src/cli/main.py`.

## 📝 Data Contract

The contract layer lives in `src/core/ai/generate_documents_v2/contracts/`.

- base traceability contracts: `src/core/ai/generate_documents_v2/contracts/base.py`
- profile contracts: `src/core/ai/generate_documents_v2/contracts/profile.py`
- job contracts: `src/core/ai/generate_documents_v2/contracts/job.py`
- matching contracts: `src/core/ai/generate_documents_v2/contracts/matching.py`
- blueprint contracts: `src/core/ai/generate_documents_v2/contracts/blueprint.py`
- drafting contracts: `src/core/ai/generate_documents_v2/contracts/drafting.py`
- assembly contracts: `src/core/ai/generate_documents_v2/contracts/assembly.py`
- review/HITL contracts: `src/core/ai/generate_documents_v2/contracts/hitl.py`

## 🛠️ How to Add / Extend

### Stable extension points

These are the surfaces designed for external configuration or downstream use.  Changes here do not require touching node internals.

**1. Graph control fields in `GenerateDocumentsV2State`**
(`src/core/ai/generate_documents_v2/state.py`)

Set these fields in the initial state dict to control pipeline behavior:

| Field | Effect |
|---|---|
| `target_language` | BCP-47 tag (e.g. `"de"`); controls assembly localization and file suffixes |
| `auto_approve_review` | `True` skips the match/blueprint/bundle checkpoints; profile writeback still requires explicit approval |
| `profile_path` | Override default profile JSON path |
| `mapping_path` | Override default section mapping JSON path |
| `profile_evidence` | Inject a raw profile dict directly, bypassing file loading |
| `strategy_type` | Blueprint strategy name forwarded to the LLM prompt (e.g. `"academic"`) |

Full field documentation is in the `GenerateDocumentsV2State` docstring.

**2. Profile and section mapping patch files**
(`src/core/ai/generate_documents_v2/profile_loader.py`)

Drop JSON patch files alongside the profile to extend content without code changes:

- `profile_patches.json` beside the profile file — add skills, traits, or entries
- `section_mapping_patches.json` beside the mapping file — reorder, retarget, or update section rules

The patch format is documented in `load_profile_kg` and `load_section_mapping` in `profile_loader.py`.

**3. `SectionMappingItem.country_context`**
(`src/core/ai/generate_documents_v2/contracts/profile.py`)

This field is the reserved seam for regional document strategies.  It defaults to `"global"` and is currently unused by the pipeline.  A future `regional_document_strategies` phase will filter or reorder `SectionMappingItem` lists by this field before the blueprint node runs — no changes to node signatures or contracts are required for that extension.

**4. LLM model injection via `build_*_chain(model=...)`**
(`src/core/ai/generate_documents_v2/nodes/`)

Every node exposes a `build_<stage>_chain(model=None)` factory.  Pass a pre-configured `ChatGoogleGenerativeAI` (or any LangChain-compatible model) to override the default Gemini 2.5 Flash model.  Used in tests and for swapping model tiers without touching prompts.

**5. `build_profile_kg(raw_data, patch_path=None)`**
(`src/core/ai/generate_documents_v2/profile_loader.py`)

The dict-based entry point for profile loading.  Call this directly (instead of `load_profile_kg`) when the profile dict is already in memory, or pass `patch_path=None` to skip patching.

### Internal — requires direct edits

The following are implementation detail and do not have stable public interfaces yet.  Extending them means editing the relevant files directly and running the test suite.

| Area | Location | How to change |
|---|---|---|
| Prompt text and structure | `src/core/ai/generate_documents_v2/prompts/` | Edit the module for the relevant stage |
| Node logic | `src/core/ai/generate_documents_v2/nodes/` | Edit the node and update its tests |
| Subgraph wiring | `src/core/ai/generate_documents_v2/subgraphs/` | Edit the subgraph builder |
| Top-level graph topology | `src/core/ai/generate_documents_v2/graph.py` | Edit node registration and edge definitions |
| Contract shapes | `src/core/ai/generate_documents_v2/contracts/` | Edit the Pydantic model and update all callers |

### Adding a new pipeline stage

1. Add or update a contract in `src/core/ai/generate_documents_v2/contracts/` first if the data shape changes.
2. Add the stage logic in `src/core/ai/generate_documents_v2/nodes/` and keep node functions narrow and testable.
3. Wire or adjust the corresponding subgraph in `src/core/ai/generate_documents_v2/subgraphs/`.
4. Persist new stage outputs through `PipelineArtifactStore` in `src/core/ai/generate_documents_v2/storage.py`.
5. Add focused tests under `tests/unit/core/ai/generate_documents_v2/`.
6. If the change is deferred or intentionally not implemented now, record it in `future_docs/issues/core/ai/generate_documents_v2/` instead of over-documenting it here.

## 💻 How to Use

```bash
# Run the operator workflow through the unified CLI
python -m src.cli.main pipeline --source stepstone --job-id <ID> --profile-evidence path/to/profile.json

# Run generation-only mode
python -m src.cli.main generate --source stepstone --job-id <ID> --language en --render
```

## 🚑 Troubleshooting

- **Pipeline stops before documents are produced** -> inspect stage artifacts under `data/jobs/<source>/<job_id>/nodes/generate_documents_v2/`.
- **Profile data is missing or wrong** -> verify the profile JSON path or the default base profile file consumed by `src/core/ai/generate_documents_v2/graph.py`.
- **Review flow feels incomplete** -> this is expected; richer generate-documents review editing is tracked in `future_docs/issues/core/ai/generate_documents_v2/`.
- **Profile changes are proposed but not written** -> approve the dedicated `hitl_4_profile_updates` checkpoint before `profile_updater` will persist changes.
- **Regional formatting expectations are missing** -> current behavior is generic; advanced regional strategies are deferred and tracked in `future_docs/issues/core/ai/generate_documents_v2/`.
