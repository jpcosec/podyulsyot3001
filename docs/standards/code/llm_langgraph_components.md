# 🧠 LLM + LangGraph Component Standards

Standards for modules built around LangGraph orchestration and LangChain model invocation. Extends `basic.md`.

Reference implementation: `src/core/ai/match_skill/`, `src/core/ai/generate_documents/`.

---

## 1. Required Layer Structure

Every LangGraph module has this file layout:

```
src/<module>/
  contracts.py     ← schema backbone: all input, output, review, persistence models
  prompt.py        ← prompt construction only: templates, serialization, variable building
  storage.py       ← persistence only: artifact paths, round management, JSON I/O
  graph.py         ← orchestration: state, nodes, edges, chain wiring, Studio factory
  __init__.py      ← public import surface
  main.py          ← CLI entry point
```

Each file owns exactly one concern. Graph nodes never write to disk directly — that belongs in `storage.py`. Prompt logic never lives in `graph.py`.

---

## 2. Node Taxonomy

Every node in a LangGraph module fits one of these types. Name them accordingly:

| Type | Responsibility | Rules |
|---|---|---|
| **Input validation** (`load_*`) | Validate and normalize state inputs, merge prior artifacts | Fail fast — raise if required inputs are missing |
| **LLM boundary** (`run_*_llm`) | Build prompt variables, invoke chain, validate output | Only place that calls the model. No disk I/O. |
| **Persistence** (`persist_*`) | Write artifacts, compute hashes, return refs into state | No business logic. Delegate entirely to `storage.py`. |
| **Breakpoint anchor** (`*_review_node`) | Pause the graph for human input | Intentionally thin — exists only as an interrupt target |
| **Review/routing** (`apply_*`) | Validate review payload, hash-check, route via `Command` | Hash validation mandatory. Safe-return if payload absent. |
| **Context prep** (`prepare_*`) | Merge patch evidence, compute regeneration scope, clear stale inputs | Must confirm routing condition before executing |

For this repository's LangGraph runtime, graph nodes are expected to be synchronous by default.

Rules:
- Prefer `def node(state) -> dict` over `async def` for graph nodes.
- Keep blocking file I/O, persistence, rendering, and other deterministic work in sync helpers instead of mixing sync operations into async nodes.
- Only introduce async nodes when the node's core work is truly async end-to-end and cannot reasonably be handled behind a sync boundary.

---

## 3. Graph State

`GraphState` (TypedDict) carries only routing signals and artifact refs — not full payloads.

```python
class MatchSkillState(TypedDict, total=False):
    source: str
    job_id: str
    status: str
    review_decision: ReviewDecision
    round_number: int
    match_result_hash: str
    artifact_refs: dict[str, str]   # refs, not content
```

Heavy payloads (requirements, evidence, match results) are written to disk by the persistence node and reloaded by nodes that need them. State is the routing bus, not the data bus.

---

## 4. LangChain Boundary

The model invocation boundary is narrow and typed:

```python
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

prompt = ChatPromptTemplate.from_messages([...])
chain = prompt | model.with_structured_output(OutputContract)
result = chain.invoke(prompt_variables)
```

Rules:
- `with_structured_output` against a Pydantic model defined in `contracts.py` — never raw string parsing
- Prompt serialization lives in `prompt.py`, not in the node
- The LLM boundary node validates the returned model before storing it in state

---

## 5. HITL Contract

Human-in-the-loop review is payload-driven, not acknowledgement-driven.

**System responsibilities:**
- Pause at the right moment (`interrupt_before` the review node)
- Persist the review surface before pausing
- Validate payload shape and hash on resume
- Reject stale payloads (hash mismatch)
- Route deterministically from the payload — never guess intent
- Treat a bare resume with no payload as a safe no-op (return to pending state)

**Human responsibilities:**
- Inspect the review surface (`review/current.json`)
- Make an explicit semantic decision per row (approve / request_regeneration / reject)
- Provide patch evidence when requesting regeneration
- Submit a typed `ReviewPayload` — not just pressing Continue

The bare-Continue case must be handled safely: if `review_payload` is absent on resume, return to `pending_review` without crashing. This is not optional — Studio will trigger this case.

---

## 6. Persistence Model

Artifacts live under `output/<module>/<source>/<job_id>/nodes/<module>/`.

Structure:
```
approved/state.json         ← latest approved proposal
review/current.json         ← current review surface
review/rounds/round_NNN/    ← immutable per-round snapshots
  proposal.json
  decision.json
  feedback.json
```

Rules:
- Round directories are immutable once written
- `approved/state.json` is overwritten only on approval
- All persisted payloads should carry a `schema_version` field (see `future_docs/issues/match_skill_hardening_roadmap.md`)
- Hash the approved artifact and store the hash in state for review validation

---

## 7. Studio Exposure

Every LangGraph module exposes a `create_studio_graph()` factory and an entry in `langgraph.json`.

```python
def create_studio_graph():
    """Create a Studio-friendly compiled graph.
    Loads even without model credentials — uses demo chain if API key absent.
    """
    return build_graph(
        chain=_build_studio_chain(),
        checkpointer=InMemorySaver(),
    )

def _build_studio_chain():
    if os.getenv("GOOGLE_API_KEY"):
        return build_default_chain()
    return _DemoChain()
```

The demo chain must produce structurally valid output (pass `with_structured_output` validation) so the full graph lifecycle can be exercised without credentials. It should be clearly identifiable in artifacts (`summary_notes` or similar field).
