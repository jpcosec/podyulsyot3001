# 🧪 LLM + LangGraph Implementation Methodology

How to build, validate, and harden a LangGraph-based feature. Extends `basic.md` and `llm_langgraph_components.md`.

This is a process guide, not a code standard — it defines the sequence and validation gates, not the component shape.

---

## 1. Implementation Sequence

Build in this order. Each step produces something verifiable before the next begins.

1. **Define contracts** (`contracts.py`) — input models, LLM output model, review model, persistence model. Nothing else exists yet.
2. **Build storage** (`storage.py`) — artifact paths, round management, JSON I/O. Test in isolation with toy data.
3. **Build prompt** (`prompt.py`) — template, serialization, variable construction. Verify the rendered prompt manually before wiring to the model.
4. **Build graph** (`graph.py`) — state, nodes, edges. Wire to a demo chain first so the graph topology can be validated without model credentials.
5. **Add CLI** (`main.py`) — run/resume flow. Test with the demo chain before adding real model credentials.
6. **Expose to Studio** — add `create_studio_graph()` and `langgraph.json` entry. Verify topology in Studio before live runs.
7. **Validate with real model** — add credentials, run end-to-end, inspect artifacts.
8. **Harden** — expand tests, handle edge cases discovered during real usage.

The key invariant: the graph must be exercisable at every step, even before credentials exist. The demo chain enables this.

---

## 2. Why the Demo Chain Exists

The demo chain is not a mock — it is a structural enabler.

Without it:
- Studio cannot render the graph if the model node raises on missing credentials
- Development and debugging require live API calls
- Tests that cover graph topology need real credentials

With it:
- Studio always loads and shows the full topology
- Graph lifecycle (pause → resume → route) can be validated without a model
- Tests use the demo chain by default; integration tests opt into the real chain

The demo chain must produce output that passes schema validation. A chain that returns garbage is not useful. Make it deterministic and structurally correct.

---

## 3. Validation Gates

After each phase, verify before proceeding:

| Phase | Verification |
|---|---|
| Contracts | Pydantic models instantiate correctly. `model_json_schema()` produces expected shapes. |
| Storage | Artifact files are written and reloaded correctly. Hashes are stable. |
| Graph (demo chain) | Automated tests cover: approve, regenerate, reject, stale hash, bare-Continue. |
| CLI | `--help` works. Run/resume cycle completes with demo chain. |
| Studio | Graph topology visible. Pause at review node confirmed. Thread history visible. |
| Real model | End-to-end run produces valid artifacts. Review surface is human-readable. |

Do not proceed to the next phase if the current phase's gate fails.

---

## 4. Test Coverage Contract

Minimum automated test coverage for any LangGraph module:

- **Approve flow**: graph runs, persists, pauses, resumes with approval, completes.
- **Regeneration flow**: review requests regeneration, context is prepared, second round runs.
- **Rejection flow**: review rejects, graph ends cleanly.
- **Stale hash rejection**: resume with a hash that doesn't match current proposal is rejected.
- **Bare-Continue safety**: resume with no payload returns to pending state without crashing.

Tests use `InMemorySaver` and injected fake chains — never the real model. CLI tests patch `build_graph` to inject the fake app.

---

## 5. Issue Discovery Pattern

Real usage against Studio reveals issues that tests miss. The most common class:

**Implicit assumptions about resume state.** Tests inject state directly. Studio users click buttons. These produce different state shapes.

When Studio reveals a crash:
1. Reproduce with a targeted test using `InMemorySaver` and the demo chain.
2. Fix the node to handle the missing/unexpected state safely.
3. Add the test case to the minimum coverage contract above.

The bare-Continue case (resuming with no `review_payload`) was discovered this way. It is now a required test case because of that.

---

## 6. Studio Verification Checklist

Before considering a LangGraph feature production-ready:

- [ ] Graph topology visible in Studio (`langgraph.json` correct)
- [ ] Graph pauses at the review breakpoint
- [ ] Thread state is inspectable in the right-hand panel
- [ ] Resume with a valid payload routes correctly
- [ ] Resume with no payload returns safely to pending state
- [ ] Artifacts are written to the expected paths after each phase
- [ ] Demo chain produces valid, identifiable output (no credential required)
