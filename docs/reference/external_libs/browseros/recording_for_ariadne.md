# BrowserOS External Reference - Recording for Ariadne

## Goal

Identify the most credible way to capture BrowserOS interaction traces and convert them into Ariadne artifacts.

## Main options

### Option 1 - Record BrowserOS MCP calls from the outside

Best fit when our own runtime is the acting agent and BrowserOS is used as an MCP server.

Flow:

1. External agent sends MCP calls to BrowserOS.
2. We log every MCP request and response.
3. We correlate element IDs against the latest snapshot.
4. We normalize the trace into Ariadne actions.

Strengths:

- deterministic
- no dependence on BrowserOS internal chat UI
- easy to align with Ariadne replay actions
- already validated in this repo's working BrowserOS MCP path

Weaknesses:

- only captures what our external agent does
- does not capture internal BrowserOS agent sessions automatically

Conclusion:

- This is the best recording path for Level 1 deterministic Ariadne replay generation.

### Option 2 - Record BrowserOS `/chat` SSE stream

Best fit when BrowserOS itself is acting as the Level 2 agent.

Live-validated stream event types include:

- `reasoning-start`
- `reasoning-delta`
- `text-start`
- `text-delta`
- `tool-input-start`
- `tool-input-available`
- `tool-output-available`
- `finish-step`
- `finish`

That means BrowserOS `/chat` can expose:

- the natural-language goal
- intermediate reasoning text
- tool names and tool inputs
- tool outputs
- final assistant response

Strengths:

- captures true Level 2 agent behavior
- gives us a natural trace boundary via `conversationId`
- likely enough to build a conversation + tool trace artifact

Weaknesses:

- may be quota-limited depending on provider/model
- more semantically ambiguous than raw MCP replay
- tool arguments can still rely on snapshot-local element IDs

Conclusion:

- This is the best current candidate for Level 2 Ariadne recording.
- The recorder should store raw SSE first, then normalize later.

### Option 3 - Rely on BrowserOS local session folders

Current evidence does not support this as the primary recording strategy.

- `~/.browseros/sessions/` appears to be a working directory, not a structured action trace.
- No durable `tool_calls.jsonl`-style artifact has been confirmed.

Conclusion:

- Do not base Ariadne recording on BrowserOS session folders.

### Option 4 - Use CDP on port `9101`

This remains useful for raw event recording but is not currently the best primary path.

Strengths:

- high-fidelity browser events
- independent of BrowserOS tool abstraction

Weaknesses:

- low-level and noisy
- requires correlation logic and script reinjection
- less semantically aligned than MCP or `/chat` tool events

Conclusion:

- CDP is a fallback or augmentation layer, not the first recording choice.

## Recommended architecture for Ariadne

### Level 1 recording source

Use an MCP proxy in front of BrowserOS.

Record:

- `initialize`
- `tools/call`
- returned tool outputs
- snapshots used for element resolution

Normalize into:

- Ariadne deterministic actions
- HITL checkpoints
- evidence artifacts

### Level 2 recording source

Use direct BrowserOS `/chat` SSE capture.

Record raw artifacts first:

- `conversationId`
- prompt
- streamed reasoning events
- tool-input and tool-output events
- final response
- screenshots or saved page evidence when relevant

Normalize later into:

- high-level Level 2 session trace
- candidate Ariadne path fragments
- unresolved ambiguities requiring HITL review

## Practical recommendation

For this project, the most realistic path to populate Ariadne is:

1. Deterministic flows: BrowserOS MCP proxy -> Ariadne replay steps
2. Exploratory or agentic flows: BrowserOS `/chat` SSE recorder -> Level 2 trace -> post-normalization into Ariadne

This avoids waiting for BrowserOS to provide its own complete recording subsystem.
