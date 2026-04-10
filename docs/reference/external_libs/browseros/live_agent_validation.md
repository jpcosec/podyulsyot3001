# BrowserOS Live Agent Validation

Date: 2026-04-08
Status: MCP mode validated; direct `/chat` validated; internal UI chat still miswired

## Goal

Validate real BrowserOS agent communication in natural language, independent of the deterministic BrowserOS CLI motor assumptions.

## Correct interaction model

After checking the official docs, the correct way to use BrowserOS "as an agent"
for this project is **not** to drive the internal BrowserOS chat UI as if it were
the primary API surface.

The documented path is:

- BrowserOS exposes MCP tools
- an external coding agent (Claude Code, Codex, Gemini CLI, or our own runtime)
  uses those MCP tools
- the natural-language objective is interpreted by the external agent, which then
  acts through BrowserOS

That is the interaction model demonstrated in `docs.browseros.com/features/use-with-claude-code`.

## What was done

### Attempt 1 - BrowserOS internal UI agent

1. Launched BrowserOS locally from `/home/jp/BrowserOS.AppImage --no-sandbox`.
2. Verified the BrowserOS MCP/chat surfaces were reachable on the local BrowserOS ports exposed by the running instance.
3. Opened a fresh BrowserOS new-tab page.
4. Sent a natural-language prompt through the BrowserOS UI agent input, not through Ariadne replay semantics.

Prompt used:

```text
What is 2+2? Reply with only the word four.
```

## How the prompt was sent

The prompt was injected into the BrowserOS UI input with placeholder:

```text
Ask BrowserOS or search Google...
```

Then the BrowserOS send button in the same prompt container was clicked.

This was done against the live BrowserOS UI DOM because the current `openbrowser.py`
 abstraction is not yet semantically correct for Level 2 agent communication.

## Observed result

The BrowserOS UI accepted the prompt and transitioned into the agent conversation view.
The response shown by BrowserOS was:

```text
Connection failed

Unable to connect to BrowserOS agent. Follow below instructions.
```

So we confirmed:

- natural-language input can be sent to the BrowserOS agent UI
- a response can be received back from the BrowserOS agent UI
- the current blocker is the BrowserOS agent backend connection, not the MCP bridge itself

Additional evidence from console logs:

```text
Failed to load resource: net::ERR_FILE_NOT_FOUND — chrome-extension://.../null/chat
```

That strongly suggests the internal BrowserOS UI agent is misconfigured locally.

Additional runtime notes from later checks:

- BrowserOS backend ports rotated during the session from `9200` to `9201`.
- `http://127.0.0.1:9000/mcp` remained a stable MCP entrypoint.
- `http://127.0.0.1:9000/chat` and `http://127.0.0.1:9201/chat` both accepted direct chat requests.

### Attempt 2 - documented MCP-client mode

To follow the official docs, BrowserOS was then used in the supported MCP-client
pattern: an external agent controlled BrowserOS directly through MCP tools.

Task executed:

```text
Go to YouTube, search for misilo, and take a screenshot as proof this is working.
```

Execution steps performed through BrowserOS MCP:

1. Opened `https://www.youtube.com/` in BrowserOS.
2. Accepted the YouTube cookie prompt.
3. Opened the YouTube search UI.
4. Filled the search box with `misilo`.
5. Submitted the search.
6. Captured a screenshot of the results page.

Observed final URL:

```text
https://www.youtube.com/results?search_query=misilo
```

Observed page evidence included result entries such as:

```text
Misilo El Máximo Capítulos
Misilo! El Máximo - El Precio de la Justicia...
Misilo! El Máximo - President Johny...
```

### Attempt 3 - direct `/chat` endpoint

After separating the broken UI from the backend, BrowserOS was tested directly via
its streaming chat endpoint instead of the internal new-tab UI.

Confirmed working endpoints during this session:

- `http://127.0.0.1:9000/chat`
- `http://127.0.0.1:9201/chat`

Confirmed stable MCP endpoint during this session:

- `http://127.0.0.1:9000/mcp`

Minimal successful chat request:

```json
{
  "conversationId": "uuid",
  "message": "Say only ready.",
  "provider": "browseros",
  "model": "browseros-auto",
  "mode": "chat"
}
```

Observed SSE response shape:

```text
data: {"type":"start"}
data: {"type":"reasoning-start", ...}
data: {"type":"reasoning-delta", ...}
data: {"type":"text-start", ...}
data: {"type":"text-delta", ...}
data: {"type":"finish", ...}
data: [DONE]
```

Minimal successful agent-mode request with browser tool use:

```json
{
  "conversationId": "uuid",
  "message": "Tell me the title of the active BrowserOS page.",
  "provider": "browseros",
  "model": "browseros-auto",
  "mode": "agent"
}
```

Observed SSE event types included:

```text
tool-input-start
tool-input-delta
tool-input-available
tool-output-available
```

Example BrowserOS tool event from the stream:

```text
data: {"type":"tool-input-available","toolCallId":"functions.get_active_page:0","toolName":"get_active_page","input":{}}
data: {"type":"tool-output-available","toolCallId":"functions.get_active_page:0","output":{...}}
```

This is the first confirmed evidence that BrowserOS `/chat` can provide a usable
Level 2 recording stream without relying on the broken internal UI.

One heavier direct `/chat` task later failed with:

```text
HTTP 429: Too Many Requests
```

So `/chat` is live, but the hosted default provider/model can still be quota-limited.

## Proof artifacts

- Internal UI-agent failure screenshot: /tmp/browseros-proof/agent-four.png
- YouTube home proof before search: /tmp/browseros-proof/youtube-home-before-search.png
- Successful MCP-client search proof: /tmp/browseros-proof/youtube-misilo-results.png
- Internal UI troubleshooting guide screenshot: /tmp/browseros-proof/browseros-troubleshooting-guide.png
- Direct `/chat` stream capture: /tmp/browseros-proof/direct-chat-stream.txt
- End-to-end discovery to replay artifacts: /tmp/browseros-proof/live-discovery-replay-2/

### Attempt 4 - low-load discovery to replay proof

Goal:

```text
Use browser actions to navigate to https://example.com and then stop.
```

What was validated:

1. BrowserOS `/chat` captured a real Level 2 agent session.
2. The trace normalized into shared BrowserOS promotion candidates.
3. The grouped/validated candidates promoted into a draft replay path.
4. The promoted path was replayed through the deterministic BrowserOS replayer on a fresh page.

Observed replay destination:

```text
https://example.com/
```

Observed replay title:

```text
Example Domain
```

Artifacts written:

- /tmp/browseros-proof/live-discovery-replay-2/trace.json
- /tmp/browseros-proof/live-discovery-replay-2/candidates.json
- /tmp/browseros-proof/live-discovery-replay-2/assessment.json
- /tmp/browseros-proof/live-discovery-replay-2/playbook.json
- /tmp/browseros-proof/live-discovery-replay-2/replay_result.json
- /tmp/browseros-proof/live-discovery-replay-2/replay_page.json
- /tmp/browseros-proof/live-discovery-replay-2/replay.png

## Practical conclusion

There are now several validated facts:

1. **BrowserOS MCP is live and controllable** on this machine.
2. **BrowserOS natural-language UI agent surface is reachable**, but the internal BrowserOS UI is miswired to `null/chat`.
3. **BrowserOS direct `/chat` works** and returns structured SSE events, including tool-call events in `mode=agent`.
4. **The documented integration model works**: using BrowserOS as an MCP server from an external agent successfully completed a real browser task end-to-end.
5. **Discovery to replay now has a live proof**: a BrowserOS agent trace was promoted into a draft replay path and successfully replayed deterministically on a fresh page.

That means the next work should focus on two separate tracks:

- treat MCP-client control as the primary validated BrowserOS integration path
- treat direct `/chat` SSE as a credible Level 2 recording source
- investigate the BrowserOS internal UI wiring separately if in-browser chat is still desired
