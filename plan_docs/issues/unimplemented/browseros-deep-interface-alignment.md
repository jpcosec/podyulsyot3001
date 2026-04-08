# BrowserOS Deep Interface Alignment

## Explanation

Our BrowserOS understanding has improved beyond the original MCP-only notes, but the codebase and architecture docs still do not fully reflect the deeper BrowserOS runtime surfaces and their implications.

We now have stronger findings for:

- port `9300` being an internal extension WebSocket bridge
- server-mediated `graph.ts` execution behavior
- `~/.browseros/sessions/` likely being a working directory rather than a ready-made tool-call trace
- MCP Session-Id preserving session context but not stable snapshot element IDs
- `/chat` being a streaming agent endpoint with a richer schema than our current assumptions

Those findings materially affect how Level 2 agent communication, recording, and promotion should be implemented.

## Reference in src

- `docs/reference/external_libs/browseros/readme.txt`
- `docs/reference/external_libs/browseros/live_agent_validation.md`
- `src/automation/motors/browseros/agent/openbrowser.py`
- `src/automation/motors/browseros/cli/client.py`
- `src/automation/ariadne/session.py`

## What to fix

Align the BrowserOS implementation and Level 2 design with the deeper confirmed BrowserOS interface model.

## How to do it

1. Decide which BrowserOS Level 2 runtime path is primary for this project:
   - `/chat`
   - `/act`
   - SDK wrapper
   - graph execution
2. Define a Python-side contract for the chosen Level 2 path, including:
   - request payload
   - streaming/event handling
   - artifact capture
   - HITL callbacks if applicable
3. Stop assuming MCP Session-Id makes element IDs durable; update any recording assumptions accordingly.
4. Treat `9300` as internal unless we intentionally reverse-engineer and document its message protocol.
5. Decide whether Level 2 recording should come from:
   - MCP proxy interception
   - BrowserOS server traces
   - `/chat` or `/act` stream events
6. Update implementation docs and tests so they match the confirmed BrowserOS behavior.
7. Account for the newly validated stable local front door behavior on `9000` and the observed backend port rotation on `920x`.

## Does it depend on another issue?

Yes — related to:

- `plan_docs/issues/unimplemented/browseros-openbrowser-level-separation.md`
- `plan_docs/issues/unimplemented/browseros-agent-interface-coverage.md`
