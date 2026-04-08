# BrowserOS Recording To Ariadne

## Explanation

We now have enough evidence to stop treating BrowserOS recording as a vague future task. BrowserOS exposes two realistic recording surfaces that can be used to populate Ariadne:

- Level 1 deterministic recording via MCP request/response interception
- Level 2 agent recording via direct `/chat` SSE capture, including tool-call events

The remaining problem is not whether recording is possible, but how to formalize, store, and normalize those traces into Ariadne artifacts.

## Reference in src

- `src/automation/motors/browseros/cli/client.py`
- `src/automation/motors/browseros/agent/openbrowser.py`
- `src/automation/ariadne/session.py`
- `docs/reference/external_libs/browseros/recording_and_proxy.md`
- `docs/reference/external_libs/browseros/recording_for_ariadne.md`

## What to fix

Implement a BrowserOS recording pipeline that can produce Ariadne-friendly traces from both deterministic MCP control and Level 2 BrowserOS agent sessions.

## How to do it

1. Build an MCP recording layer that logs `tools/call`, responses, and snapshots.
2. Build a `/chat` SSE recorder that stores:
   - `conversationId`
   - prompt
   - reasoning events
   - tool-input events
   - tool-output events
   - final response
3. Define raw trace formats for Level 1 and Level 2 separately.
4. Add normalization logic to convert those raw traces into:
   - Ariadne candidate actions
   - Ariadne observations
   - HITL review items
5. Decide what evidence must be attached to a promotion candidate:
   - snapshots
   - screenshots
   - URLs
   - server/chat stream excerpts
6. Add tests for trace normalization and one live validation path for each recording mode.

## Does it depend on another issue?

Yes — related to:

- `plan_docs/issues/unimplemented/browseros-openbrowser-level-separation.md`
- `plan_docs/issues/unimplemented/browseros-deep-interface-alignment.md`
