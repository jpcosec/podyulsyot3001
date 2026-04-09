# BrowserOS Chat Dependency Inventory Is Not Explicit

**Explanation:** The repository still contains BrowserOS `/chat` integrations, but there is no single explicit inventory of which current workflows, modules, tests, and docs actually depend on `/chat` versus MCP.

**Reference:**
- `src/automation/motors/browseros/agent/`
- `docs/reference/external_libs/browseros/`
- `plan_docs/contracts/browseros_level2_trace.md`

**What to fix:** Produce an explicit inventory of all current `/chat` dependencies and classify each one by workflow purpose and support level.

**How to do it:**
1. Identify all code paths, docs, and contracts that mention or use `/chat`.
2. Classify each as required, optional, experimental, or legacy.
3. Record the inventory in docs or an ADR-supporting artifact.

**Depends on:** none
