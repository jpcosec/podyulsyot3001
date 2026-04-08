# BrowserOS Shared Promotion Intermediate

**Explanation:** Level 1 MCP recordings and Level 2 `/chat` traces now exist, but they still converge late and inconsistently. Without a shared intermediate promotion model, each recording path risks diverging in how it becomes an Ariadne draft path.

**Reference:** `src/automation/motors/browseros/agent/normalizer.py`, `src/automation/motors/browseros/agent/promoter.py`, `src/automation/motors/browseros/cli/recording.py`, `plan_docs/contracts/browseros_level2_trace.md`, `plan_docs/contracts/recording.md`

**What to fix:** Define and implement one shared BrowserOS promotion intermediate that both Level 1 and Level 2 recordings must produce before path generation.

**How to do it:** 1. Add a shared candidate/step-evidence model for BrowserOS recording outputs. 2. Make Level 2 normalization emit that shared model instead of its own isolated shape. 3. Add Level 1 MCP normalization that emits the same model. 4. Update promotion code to consume only the shared intermediate.

**Depends on:** `plan_docs/issues/gaps/browseros-runtime-endpoint-resolution.md`
