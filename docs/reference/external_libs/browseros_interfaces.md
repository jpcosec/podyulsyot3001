# BrowserOS — Technical Interface Reference

> This document catalogs every known programmatic interface to BrowserOS, verified from live inspection of the running instance and the OpenBrowser open-source codebase. Updated: 2026-04-02.

---

## Instance Info

```json
{
  "browseros_version": "0.44.0.1",
  "chromium_version": "146.0.7821.31",
  "install_id": "edf3cf07-bdb1-42c7-be01-de7b3043fbf8",
  "binary": "/home/jp/BrowserOS.AppImage",
  "pid": "check server.lock"
}
```

---

## Port Map

| Port | Protocol | Interface | Notes |
|------|----------|-----------|-------|
| **9200** | HTTP | MCP server | Primary automation interface. All 60 browser tools available here. |
| **9101** | WebSocket | CDP (Chrome DevTools Protocol) | Full Chromium control: DOM events, JS injection, network, input recording. |
| **9300** | WebSocket | Chrome Extension | Requires `Upgrade: websocket`. Capabilities unknown — needs exploration. |

---

## 1. MCP Server — Port 9200

The main automation interface. Accepts JSON-RPC `tools/call` directly — **no LLM required**.

### Handshake (required once per session)

```python
import requests

HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",  # MANDATORY — 500 without this
    "MCP-Protocol-Version": "2025-06-18",              # use this, not 2024-11-05
}
BASE_URL = "http://127.0.0.1:9200/mcp"

def mcp(method, params, call_id=1):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": call_id}
    r = requests.post(BASE_URL, headers=HEADERS, json=payload)
    return r.json()

# Initialize (do this once — get Mcp-Session-Id back)
resp = requests.post(BASE_URL, headers=HEADERS, json={
    "jsonrpc": "2.0", "method": "initialize",
    "params": {
        "protocolVersion": "2025-06-18",
        "capabilities": {"tools": {"listChanged": True}, "sampling": {}},
        "clientInfo": {"name": "postulator", "version": "1.0"}
    },
    "id": 1
})
session_id = resp.headers.get("Mcp-Session-Id")
# Add to HEADERS for subsequent calls: HEADERS["Mcp-Session-Id"] = session_id
```

**Important:** The `Mcp-Session-Id` response header enables session continuity — add it to all subsequent calls to maintain browser context.

### Security flag

```json
"allow_remote_in_mcp": false
```

Only localhost connections are accepted. Remote MCP access is blocked at the server level.

### Available tools (60 total)

**Observation**
```
take_snapshot          — interactive elements with text + IDs (session-scoped IDs)
take_enhanced_snapshot — richer snapshot with more element metadata
get_dom                — full DOM HTML
search_dom             — query DOM by selector/text
get_page_content       — plain text content of page
get_page_links         — all links on page
get_console_logs       — browser console output
take_screenshot        — PNG screenshot as base64
```

**Navigation**
```
navigate_page          — load URL in current or new page
new_page               — open new tab
new_hidden_page        — open hidden tab (no focus change)
list_pages             — list all open tabs with URL + pageId
get_active_page        — get current focused tab
show_page              — bring tab to foreground
move_page              — reorder tabs
close_page             — close tab
```

**Interaction**
```
click                  — click by element ID or CSS selector
click_at               — click by absolute coordinates (x, y)
fill                   — set input value (WARNING: fails on React controlled inputs — see below)
check / uncheck        — checkbox state
select_option          — dropdown selection
upload_file            — file upload (handles OS file picker)
press_key              — keyboard key press
focus                  — focus element
clear                  — clear input field
hover / hover_at       — mouse hover
type_at                — type at coordinates
drag / drag_at         — drag and drop
scroll                 — scroll page
handle_dialog          — respond to browser dialogs (alert, confirm, prompt)
```

**Scripting**
```
evaluate_script        — execute JavaScript in page context (expression param, not script)
```

**Utilities**
```
save_pdf               — save page as PDF
save_screenshot        — save screenshot to file path
download_file          — download file from URL
browseros_info         — BrowserOS version and status
```

### Critical behaviors

**Snapshot IDs are session-scoped.** Element IDs (`[512] link "Apply"`) are stable within a page load but change on any navigation or reload. Always use `element_text` for replay, never numeric IDs.

**React controlled inputs.** `fill` sets the DOM value but does not trigger React's `onChange` — the form state stays unchanged. Use `evaluate_script` with the React native value setter:

```python
script = """
const el = document.querySelector('{selector}');
const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
setter.call(el, '{value}');
el.dispatchEvent(new Event('input', {{ bubbles: true }}));
"""
mcp("tools/call", {"name": "evaluate_script", "arguments": {"expression": script, "page": page_id}})
```

Confirmed required on: XING salary field, XING date spinbuttons, any React/Vue SPA.

**Date spinbuttons.** `<input type="number" role="spinbutton">` (used by XING for start date). Standard `fill` and `press_key` both fail. Only the React native setter via `evaluate_script` works reliably.

---

## 2. CDP — Port 9101

Full Chrome DevTools Protocol access. This is our **recording interface**.

```python
import asyncio, websockets, json

CDP_BASE = "http://127.0.0.1:9101"

async def get_targets():
    """List all debuggable pages."""
    import requests
    return requests.get(f"{CDP_BASE}/json").json()

async def cdp_session(target_id: str):
    ws_url = f"ws://127.0.0.1:9101/devtools/page/{target_id}"
    async with websockets.connect(ws_url) as ws:
        # Enable event domains
        await ws.send(json.dumps({"method": "Page.enable", "id": 1}))
        await ws.send(json.dumps({"method": "Runtime.enable", "id": 2}))
        await ws.send(json.dumps({"method": "Input.enable", "id": 3}))  # if available

        # Inject in-page event capture
        await ws.send(json.dumps({
            "method": "Runtime.evaluate",
            "params": {"expression": CAPTURE_SCRIPT},
            "id": 4
        }))

        async for msg in ws:
            event = json.loads(msg)
            yield event
```

### CDP capabilities for recording

| Domain | Event | What we get |
|--------|-------|-------------|
| `Page` | `frameNavigated` | URL changes, redirects |
| `Runtime` | `consoleAPICalled` | Our injected capture script output |
| `Network` | `requestWillBeSent` | Form submissions (POST requests) |
| `Input` | (if enabled) | Raw input events |

### In-page capture script

```javascript
(function() {
  if (window.__postulator_recorder) return;
  window.__postulator_recorder = true;

  const log = (type, data) =>
    console.log(JSON.stringify({__rec: true, type, ts: Date.now(), ...data}));

  document.addEventListener('click', e => log('click', {
    tag: e.target.tagName,
    text: (e.target.innerText || e.target.value || '').trim().slice(0, 100),
    x: e.clientX, y: e.clientY,
    name: e.target.name || e.target.id || null
  }), true);

  document.addEventListener('change', e => log('change', {
    tag: e.target.tagName, name: e.target.name,
    value: e.target.type === 'password' ? '{{REDACTED}}' : e.target.value,
    type: e.target.type
  }), true);

  document.addEventListener('submit', e => log('submit', {
    action: e.target.action, method: e.target.method
  }), true);
})();
```

Events arrive via `Runtime.consoleAPICalled` with `__rec: true` in the JSON. Filter and accumulate. On navigation (`Page.frameNavigated`), re-inject the script on the new page.

### Correlating CDP events → playbook steps

After capturing raw events, correlate with periodic snapshots:
1. Click at `(x, y)` → take snapshot → find element whose text matches what's visible at those coordinates
2. Change on `input[name="salary"]` → find element in snapshot with that name → `fill(element_text="Gehalt", value="{{salary_expectation}}")`
3. Submit → `click(element_text="Jetzt bewerben")`

---

## 3. Chrome Extension — Port 9300

Requires WebSocket upgrade. Initial probe returned `426 Upgrade Required`.

```python
import websocket  # pip install websocket-client
ws = websocket.WebSocket()
ws.connect("ws://127.0.0.1:9300")
# Send and observe what protocol it speaks
```

**Status:** Unknown capabilities. Likely the communication channel between BrowserOS server and the Chromium extension running inside the browser. May expose page state, user interactions, or extension-specific controls. **Needs exploration.**

---

## 4. SQLite Database — `~/.config/browser-os/.browseros/browseros.db`

```sql
-- Tables
identity       -- single row: browseros_id (install UUID)
rate_limiter   -- LLM provider rate limiting records
oauth_tokens   -- provider credentials (see below)
```

### `oauth_tokens` schema

```sql
CREATE TABLE oauth_tokens (
  browseros_id TEXT NOT NULL,
  provider TEXT NOT NULL,          -- "google", "github", etc.
  access_token TEXT NOT NULL,      -- LIVE ACCESS TOKEN — plaintext
  refresh_token TEXT NOT NULL,     -- LIVE REFRESH TOKEN — plaintext
  expires_at INTEGER NOT NULL,
  email TEXT,
  account_id TEXT,
  created_at TEXT,
  updated_at TEXT,
  PRIMARY KEY (browseros_id, provider)
);
```

**This is a significant interface.** OAuth access tokens for whatever accounts the user has connected to BrowserOS are stored here in plaintext. This is useful for:
- Reading the user's connected accounts and their email addresses
- Verifying which providers are authenticated without making any network calls
- Understanding session state before attempting portal navigation

**Security note:** Never write to this table, never log its contents, never include it in artifacts. Read-only use only, and only for session state verification.

```python
import sqlite3
DB = "/home/jp/.config/browser-os/.browseros/browseros.db"

def get_connected_providers():
    conn = sqlite3.connect(DB)
    rows = conn.execute("SELECT provider, email, expires_at FROM oauth_tokens").fetchall()
    conn.close()
    return [{"provider": r[0], "email": r[1], "expires_at": r[2]} for r in rows]
```

---

## 5. Graph Directory — `~/.config/browser-os/.browseros/graph/`

BrowserOS stores OpenBrowser agent scripts here as TypeScript files. Each subdirectory is a script ID.

```
graph/
  code_l3aod1jcXf6w/
    graph.ts    ← the agent TypeScript script
```

### What `graph.ts` looks like

The TypeScript script uses the OpenBrowser SDK `Agent` API:

```typescript
export async function run(agent: Agent) {
  await agent.nav("https://www.xing.com/jobs/...");

  const state = await agent.extract("Is the apply modal open?", {
    schema: z.object({ isOpen: z.boolean() })
  });

  await agent.act("Fill the Vorname field with the user's first name", {
    context: { firstName: "Juan Pablo" },
    maxSteps: 5
  });

  const result = await agent.verify("The application was submitted successfully.");
  return { success: result.success };
}
```

### OpenBrowser Agent API (full)

| Method | Signature | What it does |
|--------|-----------|-------------|
| `agent.nav(url)` | `(url: string) => Promise<void>` | Navigate to URL |
| `agent.extract(prompt, {schema})` | Zod schema → structured data | LLM extracts structured info from current page |
| `agent.act(prompt, {context?, maxSteps?})` | Natural language → actions | LLM performs actions on page (multi-step) |
| `agent.verify(prompt)` | `=> {success, reason}` | LLM verifies a condition is true |

**`agent.act` with context:** Variables in `context` are interpolated into the prompt with `{{varName}}` syntax. This is how profile data gets passed to the agent without embedding it in the prompt string.

**This means we can write agent scripts and drop them in `graph/` for BrowserOS to execute.** The graph directory is the integration point for Level 2 execution from our pipeline.

---

## 6. HumanInteractTool — The Formal HITL API

Built into the OpenBrowser agent framework. When the agent needs human input, it calls this tool. The `callback` registered with the agent handles it.

```typescript
// interactType options:
"confirm"      // "Are you sure you want to submit?" → boolean
"input"        // "Enter your salary expectation" → string
"select"       // "Choose your German level" + options → string[]
"request_help" // "Login required" or "CAPTCHA" → boolean (solved?)
```

```typescript
// helpType for request_help:
"request_login"       // Portal requires authentication
"request_assistance"  // Anything else (CAPTCHA, unknown form, etc.)
```

**Login check:** Before surfacing `request_login` to the human, the tool takes a screenshot and asks the LLM "is this page logged in?" If yes, it skips the interruption. This is built-in.

**For our pipeline:** We implement the `callback` interface in Python (via the `/chat` endpoint or by writing a TypeScript wrapper) to route `request_help` and `input` calls to our HITL channel (terminal → Textual TUI).

---

## 7. Browser Profile — `~/.config/browser-os/Default/`

The real Chromium user profile. Contains:
- `Cookies` — login sessions for all portals (XING, StepStone, LinkedIn, etc.)
- `Local Storage/` — portal-specific app state
- `IndexedDB/` — heavier app storage

This is what makes BrowserOS already logged in to portals. We do not manage this — BrowserOS manages it. Our job is to not break it (don't clear cookies, don't open incognito).

**Persistence across restarts:** Cookies survive BrowserOS restarts because they live in the filesystem profile, not in memory. Login sessions persist as long as the portal's session expiry allows (typically weeks to months for "remember me" sessions).

---

## 8. Server State Files

```
~/.config/browser-os/.browseros/
  server_config.json   — ports, flags, version info (read-only reference)
  server.lock          — PID of running BrowserOS process
  server.state         — creation timestamp + PID
  browseros-server.log — server log (JSON lines, useful for debugging MCP errors)
```

### Reading the server log for MCP debugging

```bash
tail -f ~/.config/browser-os/.browseros/browseros-server.log | python3 -c "
import sys, json
for line in sys.stdin:
    try:
        obj = json.loads(line)
        if obj.get('msg') or obj.get('err'):
            print(obj)
    except: pass
"
```

---

## 9. MCP Proxy Architecture (Gap 4 — Recording Level 2)

When the OpenBrowser LLM agent runs, it calls BrowserOS tools via `SimpleHttpMcpClient` pointing at `http://127.0.0.1:9200/mcp`. From the source code, `httpUrl` is a constructor parameter — **it is configurable**.

A transparent proxy between OpenBrowser and BrowserOS gives us the full tool call log for free:

```
OpenBrowser agent
    │  tools/call {"name": "click", "arguments": {"element": 512}}
    ▼
[Postulator MCP Proxy :9201]
    │  log call + correlate element ID with last snapshot → playbook step
    │  forward unchanged
    ▼
BrowserOS MCP :9200
    │  response
    ▼
[Proxy]
    │  log response
    ▼
OpenBrowser agent
```

### Python proxy skeleton

```python
from fastapi import FastAPI, Request
import httpx, asyncio

app = FastAPI()
BROWSEROS_URL = "http://127.0.0.1:9200/mcp"
last_snapshot: dict = {}  # updated on every take_snapshot call
playbook_steps: list = []

@app.post("/mcp")
async def proxy_mcp(request: Request):
    body = await request.json()
    method = body.get("method")
    params = body.get("params", {})

    # Intercept and record tool calls
    if method == "tools/call":
        tool_name = params.get("name")
        args = params.get("arguments", {})
        _record_step(tool_name, args)

    # Forward to BrowserOS
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            BROWSEROS_URL,
            json=body,
            headers=dict(request.headers),
        )
        result = resp.json()

    # Capture snapshots for element ID correlation
    if method == "tools/call" and params.get("name") == "take_snapshot":
        last_snapshot["elements"] = _parse_snapshot(result)

    return result

def _record_step(tool_name: str, args: dict):
    """Normalize tool call to a playbook step."""
    step = {"action": tool_name, "args": args}

    # Resolve numeric element IDs to text
    element_id = args.get("element")
    if element_id and last_snapshot.get("elements"):
        text = last_snapshot["elements"].get(int(element_id), {}).get("text")
        if text:
            step["args"] = {**args, "element_text": text}
            del step["args"]["element"]

    # Replace known profile values with {{variables}}
    step = _substitute_variables(step)
    playbook_steps.append(step)
```

### If OpenBrowser MCP URL is not configurable at runtime

Use `iptables` to transparently intercept without modifying OpenBrowser:

```bash
# Redirect all local traffic to 9200 → our proxy at 9201
sudo iptables -t nat -A OUTPUT -p tcp --dport 9200 -m owner ! --uid-owner proxy_uid -j REDIRECT --to-port 9201
# Our proxy runs on 9201 and forwards to 9200 using a direct socket (bypasses iptables)
```

Or simpler with `socat` for testing:
```bash
socat TCP-LISTEN:9201,fork,reuseaddr TCP:127.0.0.1:9200
```

---

## 10. Known Unknowns

- [ ] **Port 9300 (extension)** — WebSocket protocol and available capabilities
- [ ] **`graph/` write** — can we drop a new `graph.ts` and have BrowserOS execute it, or does it require a UI interaction to load?
- [ ] **`~/.browseros/sessions/`** — does BrowserOS log agent tool calls here during a session? If yes, Level 2 recording is free
- [ ] **MCP Session-Id behavior** — does a session ID preserve snapshot element IDs across calls, or only HTTP session state?
- [ ] **BrowserOS `/chat` endpoint from Python** — what is the exact schema for triggering an agent run programmatically (not via UI)?
