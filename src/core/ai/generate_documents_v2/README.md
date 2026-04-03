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
7. profile updater placeholder

Current limitations that are intentionally not documented as supported behavior:

- profile updater is a no-op in `src/core/ai/generate_documents_v2/graph.py`
- review pauses exist in the graph, but there is no full generate-documents-specific GraphPatch editing UI yet
- regional document strategies are not fully implemented; deferred items live in `future_docs/issues/`

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

1. Add or update a contract in `src/core/ai/generate_documents_v2/contracts/` first if the data shape changes.
2. Add the stage logic in `src/core/ai/generate_documents_v2/nodes/` and keep node functions narrow and testable.
3. Wire or adjust the corresponding subgraph in `src/core/ai/generate_documents_v2/subgraphs/`.
4. Persist new stage outputs through `PipelineArtifactStore` in `src/core/ai/generate_documents_v2/storage.py`.
5. Add focused tests under `tests/test_generate_documents_v2/`.
6. If the change is deferred or intentionally not implemented now, record it in `future_docs/issues/` instead of over-documenting it here.

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
- **Review flow feels incomplete** -> this is expected; richer generate-documents review editing is tracked in `future_docs/issues/`.
- **Regional formatting expectations are missing** -> current behavior is generic; advanced regional strategies are deferred and tracked in `future_docs/issues/`.
