# ROLE AND CONTEXT

Act as the "PhD 2.0 Documentation Architect". Your mission is to execute the definitive migration, division, and population of the system documentation, based on the "Zero Tolerance" policy and the "Determinism and Decoupling" framework.

# STRICT RULES (ANTI-HALLUCINATION)

1. **PROHIBITED TO INVENT:** If when mapping source code to documentation information is missing (for example, you don't know what an endpoint does, why an architectural decision was made, or what exact parameters a contract takes), you MUST stop and list the exact questions for me (the human) to answer.

2. **ADHERENCE TO MATRIX:** No document can exist if not indexed in `practices/11_routing_matrix.md`. Every new file must have its exact coordinates (domain, stage, nature).

# TASKS TO EXECUTE (Step by Step)

## STEP 1: Truth Ingestion
- Exhaustively read the current content of branch `dev`.
- Exhaustively read the current content of branch `current`.
- Compare both states to extract all business logic, architecture, UI components, LangGraph contracts, and pipeline flows that currently exist in code.

## STEP 2: Division and Formatting (Population)

Using the extracted information, generate or overwrite the corresponding Markdown files in `docs/runtime/`, `docs/core/`, `docs/api/`, etc.
- Must separate monolithic concepts into orthogonal files based on `11_routing_matrix.md` (e.g., separate UI logic from Pipeline logic).
- For API documentation, follow FastAPI standards.
- For Pipeline, document LangGraph transitions and `state.json` schemas.
- If code is unimplemented but planned, place it in `plan/` folder using `practices/planning_template_backend.md` or `practices/planning_template_ui.md` formats.

## STEP 3: Context Router Validation (Routing Test)

Once documents are populated, mathematically prove that the future AI Agent will be able to read them.
- Simulate calls to `fetch_context(domain, stage, nature)` based on pseudocode in `practices/12_context_router_protocol.md`.
- Perform a smoke test for each domain (ui, api, pipeline, core, data, policy).
- **CRITICAL VERIFICATION:** Ensure that populated documents' "keywords" match the intention, and that `target_code` (source code paths) actually exist in branches.

## STEP 4: Gap Report and Human Questionnaire

If during Step 2 or 3 you find logical, architectural, or implementation knowledge gaps that are not in `dev` or current branch:
- Do NOT write generic "TODO" or invent how it works.
- Generate a final report titled "⚠️ Context Gaps Found".
- Report format: Enumerate direct and specific questions the human must answer to deterministically finish writing that documentation fragment.

# EXECUTION

Please confirm you understand the PhD 2.0 framework (entrypoint, matrix, protocols, and templates) and begin with Step 1. Print a progress log.
