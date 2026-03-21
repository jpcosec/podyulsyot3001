# LangChain Phase 1: Wrappers and Structured Output

## Objective
Replace the in-house AI runtime with LangChain abstractions to solve extraction drift and schema instability while keeping the deterministic LangGraph orchestration intact.

## Scope
1. **LLMRuntime Replacement:** Implement `ChatGoogleGenerativeAI` with `.with_structured_output(Schema)`.
2. **Observability:** Integrate LangSmith for full prompt/response tracing.
3. **Deterministic TextSpan:** LLM returns `exact_quote` (string) only; offsets are calculated deterministically by the backend.
