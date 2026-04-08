# BrowserOS OpenBrowser Level Separation

## Explanation

`src/automation/motors/browseros/agent/openbrowser.py` currently mixes two different semantic layers of BrowserOS interaction.

- **Level 1 / deterministic execution**: low-level BrowserOS MCP tool calls (`click`, `fill`, `upload`, snapshots, DOM queries).
- **Level 2 / agent exploration**: natural-language goal communication with the BrowserOS/OpenBrowser agent, plus observation/recording of what the agent does.

That coupling is causing both architectural confusion and incorrect implementation choices, such as treating the agent like a deterministic replayer or assuming it should directly return replay paths.

## Reference in src

- `src/automation/motors/browseros/agent/openbrowser.py`
- `src/automation/motors/browseros/agent/provider.py`
- `src/automation/motors/browseros/cli/client.py`
- `src/automation/ariadne/session.py`
- `docs/automation/ariadne_semantics.md`
- `plan_docs/motors/browseros_agent.md`

## What to fix

Split the BrowserOS/OpenBrowser integration into explicit semantic levels and introduce contracts that make the boundary unambiguous.

## How to do it

1. Add a contract for **Level 2 agent communication**:
   - send natural-language goals
   - observe agent progress/results
   - capture artifacts and conversation traces
   - do **not** require deterministic replay semantics at this layer
2. Keep **Level 1 deterministic BrowserOS MCP execution** isolated in the CLI/motor client layer.
3. Refactor `openbrowser.py` so it represents a Level 2 interface rather than a fake deterministic motor or direct `ReplayPath` provider.
4. Define how Level 2 outputs transition into Ariadne recording/promotion:
   - raw conversation + actions + evidence
   - normalization step
   - optional promotion into `AriadnePath`
5. Decide whether the Level 2 contract should be backed by `/chat`, `/act`, the SDK, or graph execution.
6. Add tests that enforce the semantic split and prevent regressions where Level 2 code starts depending on Level 1 replay assumptions.

## Does it depend on another issue?

Yes — related to `plan_docs/issues/unimplemented/browseros-agent-interface-coverage.md`.
