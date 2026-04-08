# BrowserOS External Reference - Deep Findings

## 10. Deep-Dive Findings

### 10.1 Port 9300 (extension)

Status: **partially confirmed**

- Port `9300` is the BrowserOS extension/controller port.
- It uses **WebSocket** internally between the BrowserOS server and the extension.
- Publicly documented behavior is limited: it appears to bridge into `chrome.*`
  APIs, especially areas like tabs, history, and bookmarks.
- Source review suggests richer tab/window/group capabilities also flow through
  this layer.
- We still do **not** have a stable public message schema for third-party use.

Practical implication:
- Treat `9300` as an internal integration surface, not as a stable public API.

### 10.2 `graph/` execution model

Status: **mostly confirmed**

- BrowserOS can execute graph code **without UI interaction** once the server-side
  flow is triggered.
- The current official flow appears to be server-mediated graph generation and
  execution, where the server writes a temporary `graph.ts`, imports it, and runs
  `run(agent)`.
- We do **not** have evidence that dropping an arbitrary file into a watched
  `graph/` directory is enough for BrowserOS to auto-discover and run it.

Practical implication:
- Do not assume "write `graph.ts` into a folder and BrowserOS will pick it up".
- If we want programmatic Level 2 execution, the more credible paths are:
  - `/chat` / agent endpoints
  - SDK usage
  - server-mediated graph execution

### 10.3 `~/.browseros/sessions/`

Status: **likely not a structured tool-call trace**

- Current evidence suggests `~/.browseros/sessions/<conversationId>` is used as a
  per-session working directory when no explicit working dir is provided.
- It appears tied to lifecycle/retention and scratch session storage.
- We did **not** find evidence that BrowserOS writes a durable structured log such
  as `tool_calls.jsonl` or a ready-made Level 2 replay trace there.
- Large temporary artifacts appear to go to system temp directories instead.

Practical implication:
- We should not assume Level 2 recording is "free" from `~/.browseros/sessions/`.
- Recording likely still requires an MCP proxy, explicit tracing, or server-side
  agent instrumentation.

### 10.4 MCP Session-Id behavior

Status: **mostly confirmed**

- MCP session continuity preserves HTTP/MCP session context.
- It does **not** appear to make snapshot element IDs stable across arbitrary
  future calls.
- BrowserOS tool semantics consistently imply that element references are tied to
  the **latest snapshot**.
- The safe operating rule remains: **take a fresh snapshot before interaction**.

Practical implication:
- Element IDs should be treated as snapshot-local, not durable identifiers.
- Any recorder/replayer must correlate actions against the latest snapshot, not
  store naked element IDs as stable references.

### 10.5 `/chat` endpoint from Python

Status: **confirmed enough for integration design**

- BrowserOS exposes `POST /chat` as a streaming agent endpoint.
- It behaves like an SSE/UI event stream rather than returning a single JSON
  response body.
- Required fields observed in source review:

```json
{
  "conversationId": "uuid",
  "message": "string",
  "provider": "anthropic|openai|google|openrouter|azure|ollama|lmstudio|bedrock|browseros|openai-compatible|moonshot",
  "model": "string"
}
```

- Optional fields observed in source review:

```json
{
  "contextWindowSize": 123,
  "browserContext": {},
  "userSystemPrompt": "string",
  "isScheduledTask": false,
  "userWorkingDir": "/abs/or/session/dir",
  "supportsImages": true,
  "mode": "chat|agent",
  "declinedApps": ["gmail", "notion"],
  "previousConversation": [
    { "role": "user", "content": "..." },
    { "role": "assistant", "content": "..." }
  ],
  "apiKey": "string",
  "baseUrl": "string",
  "resourceName": "string",
  "region": "string",
  "accessKeyId": "string",
  "secretAccessKey": "string",
  "sessionToken": "string",
  "upstreamProvider": "string"
}
```

Minimal Python shape:

```python
import uuid
import requests

url = "http://127.0.0.1:9100/chat"

payload = {
    "conversationId": str(uuid.uuid4()),
    "message": "Open example.com and tell me the page title",
    "provider": "openai",
    "model": "gpt-4.1",
    "apiKey": "YOUR_KEY",
    "mode": "agent",
}

with requests.post(url, json=payload, stream=True) as response:
    response.raise_for_status()
    for line in response.iter_lines(decode_unicode=True):
        if line:
            print(line)
```

Important nuance:
- For programmatic automation, `/act` or the SDK-level agent surface may be more
  appropriate than `/chat`, because `/chat` is shaped around the conversation/UI
  model.

Additional live findings from this machine:

- `POST /chat` was confirmed live on BrowserOS local endpoints.
- During this session, BrowserOS accepted direct chat requests on:
  - `http://127.0.0.1:9000/chat`
  - `http://127.0.0.1:9201/chat`
- The BrowserOS new-tab UI was separately observed to be miswired to `null/chat`,
  so the direct endpoint is more trustworthy than the in-browser chat surface.
- `mode=agent` streams include structured tool-call events such as:
  - `tool-input-start`
  - `tool-input-available`
  - `tool-output-available`

Practical implication:
- `/chat` is not just a conversational UI stream; it is also a plausible Level 2
  recording source because it exposes tool calls and tool outputs directly.

### 10.6 Stable endpoint behavior on this machine

Status: **confirmed for this installation, but not yet generalized**

- BrowserOS backend ports rotated during the session (`9200` -> `9201`, `9300` -> `9301`).
- `http://127.0.0.1:9000/mcp` remained reachable and behaved like a stable MCP front door.
- `http://127.0.0.1:9000/chat` also remained reachable even when the backend server port changed.

Practical implication:
- For local integration on this machine, `9000` looks like the best default entrypoint.
- The raw `920x` port should be treated as discoverable runtime state, not a hard-coded constant.

## 11. Remaining Unknowns

- [ ] Exact WebSocket message schema for port `9300`
- [ ] Whether BrowserOS supports direct arbitrary `graph.ts` execution without the current server-mediated graph flow
- [ ] Whether BrowserOS writes any hidden structured per-session agent trace that we have not yet discovered
- [ ] Exact production-ready contract for `/act` vs `/chat` and which one should back our Level 2 contract
- [ ] Whether `9000` is always the stable BrowserOS front door or just a local-wrapper convention in this installation
