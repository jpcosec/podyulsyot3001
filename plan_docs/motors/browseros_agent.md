# BrowserOS Agent Motor — Placeholder

Date: 2026-04-05
Status: design-only, no code exists (interface reference material exists)

## What this motor should do

Navigate and discover paths through portals using the OpenBrowser LLM agent and
human-in-the-loop interaction. This is the "explorer" motor: it navigates unknown
flows, handles dynamic/unpredictable UI, and discovers branching points and dead ends.

When activated, the agent motor runs a recording pipeline: watch the session,
record raw events, process them into normalized steps, and update the Ariadne
path/map. Recording is not a separate agent — it's what the agent motor does
as part of its normal operation.

Use cases:

- Navigate a new apply flow for a portal that has no existing Ariadne path
- Discover branching points and dead ends in a portal's apply flow
- Handle unknown/dynamic form fields that deterministic replay can't anticipate
- Human-assisted navigation when the agent gets stuck (CAPTCHA, login, ambiguous UI)
- Produce normalized Ariadne paths from agent sessions (watch → record → process → update)

## Relationship to other motors

- **This motor produces, other motors consume.** The agent motor records paths;
  BrowserOS CLI, Crawl4AI, OS native, and vision replay them.
- **Ariadne is the handoff point.** Agent recordings normalize into Ariadne common
  language on capture (Option A from the issues doc). Once stored, any motor's
  translator can compile them into backend-specific replay instructions.
- **Not a default execution path.** Normal apply runs use BrowserOS CLI or Crawl4AI.
  The agent motor is invoked for new portals, changed portals, or flows that need
  adaptive behavior.

## What already exists (reference material, no code)

Source: `docs/reference/external_libs/browseros/readme.txt` (see `graph_and_hitl.md` and `deep_findings.md`)

### OpenBrowser Agent API

TypeScript scripts in `~/.config/browser-os/.browseros/graph/` using the `Agent` SDK:

| Method | What it does |
|---|---|
| `agent.nav(url)` | Navigate to URL |
| `agent.extract(prompt, {schema})` | LLM extracts structured data from current page (Zod schema) |
| `agent.act(prompt, {context?, maxSteps?})` | LLM performs multi-step actions on page |
| `agent.verify(prompt)` | LLM verifies a condition is true → `{success, reason}` |

Context variables use `{{varName}}` syntax, same as current playbook templates.

### HumanInteractTool (built-in HITL)

The agent framework's formal HITL API. When the agent needs human input:

| interactType | Meaning |
|---|---|
| `confirm` | Yes/no question → boolean |
| `input` | Free text request → string |
| `select` | Choose from options → string[] |
| `request_help` | Login required or CAPTCHA → human solves, returns boolean |

`request_help` subtypes: `request_login` (portal auth needed), `request_assistance`
(anything else). Built-in login check: before surfacing `request_login`, the tool
screenshots the page and asks the LLM "is this page logged in?" — skips interruption
if yes.

Our pipeline would implement the `callback` interface to route these to the
operator's terminal or Textual TUI.

### CDP recording interface (port 9101)

Full Chrome DevTools Protocol via WebSocket. Documented capabilities:

- `Page.frameNavigated` — URL changes and redirects
- `Runtime.consoleAPICalled` — output from injected capture script
- `Network.requestWillBeSent` — form submissions (POST requests)
- `Input` domain — raw input events (if enabled)

An in-page capture script is documented that logs click, change, and submit events
as JSON via `console.log()`, captured through CDP `Runtime.consoleAPICalled`.
On navigation, the script must be re-injected.

### MCP proxy architecture

A transparent proxy between the OpenBrowser agent and BrowserOS MCP (port 9200)
that intercepts all tool calls:

```
OpenBrowser agent → [Postulator MCP Proxy :9201] → BrowserOS MCP :9200
```

The proxy logs every tool call, correlates element IDs with the last snapshot's
text labels, substitutes known profile values with `{{variables}}`, and accumulates
playbook steps. A Python FastAPI skeleton exists in the interfaces doc.

Fallback if OpenBrowser's MCP URL is not configurable: `iptables` redirect or
`socat` forwarding.

## What needs to be documented before implementation

### Recording pipeline

How does a raw agent session become an Ariadne path?

- [ ] **Capture**: what raw data is collected during an agent session?
  - MCP tool calls (via proxy) — action log with element text + values
  - CDP events (via WebSocket) — navigation, form submissions, console output
  - Snapshots — periodic `take_snapshot` for element correlation
  - Screenshots — visual evidence per step
  - Agent prompts/responses — what the LLM decided and why
  - HITL interactions — what the human was asked and answered

- [ ] **Correlation**: how are raw events grouped into steps?
  - Snapshot before action → action → snapshot after action = one step
  - Navigation events mark step boundaries
  - Agent `act()` calls may contain multiple MCP tool calls = one logical step

- [ ] **Normalization**: how are BrowserOS-specific recordings converted to common language?
  - MCP tool names → Ariadne intent vocabulary (`click` → `click`, `fill` → `fill`,
    `evaluate_script` with React pattern → `fill_react_controlled`)
  - Element IDs → `AriadneTarget` with text field (from snapshot correlation)
  - Profile values → `{{placeholder}}` templates
  - Observed elements → `ObserveBlock` expected elements
  - This is the BrowserOS→common translator (inverse direction, per Issue 4)

- [ ] **Promotion**: when does a recording become a replayable path?
  - Draft: raw normalized recording, not yet verified
  - Verified: successfully replayed at least once via a deterministic motor
  - Canonical: approved for production use, stored in Ariadne traces

### Agent script authoring

- [ ] How do we write and deploy agent scripts?
  - Write TypeScript using the `Agent` API
  - Drop in `~/.config/browser-os/.browseros/graph/`
  - **Unknown**: does BrowserOS auto-discover new scripts, or does it require UI interaction?

- [ ] What does a recording agent script look like?
  - Navigate to portal → start recording (proxy + CDP)
  - `agent.act("Apply to this job", {context: profileData})`
  - Capture the full tool call log
  - Normalize into Ariadne path

- [ ] Should agent scripts be generic or portal-specific?
  - Generic: "apply to the job on this page" — agent discovers the flow
  - Portal-specific: "follow LinkedIn Easy Apply" — agent follows known structure
  - Probably both: generic for discovery, portal-specific for guided recording

### HITL routing

- [ ] How does `HumanInteractTool` callback reach the operator?
  - Option A: terminal `input()` (current pattern in BrowserOS CLI `setup_session`)
  - Option B: Textual TUI integration (route to review UI)
  - Option C: webhook/API for remote operation
  - Define the callback interface before implementing

- [ ] What state does the operator see during a recording session?
  - Current page screenshot?
  - Agent's current intent/prompt?
  - Accumulated steps so far?
  - Live snapshot element list?

### Bifurcation and dead-end detection

- [ ] How does the agent motor identify branching points?
  - Agent encounters multiple possible paths → log as bifurcation
  - Agent hits a wall (external ATS, expired job, CAPTCHA) → log as dead end
  - Human flags a branch point during HITL interaction

- [ ] How are bifurcations stored in Ariadne?
  - Current playbook has `bifurcations` dict mapping ariadne_tag → condition → destination
  - Should this structure be in the common language or is it metadata-only?

### Session management

- [ ] How does the agent motor handle portal authentication?
  - Reuse BrowserOS browser profile (cookies persist in `~/.config/browser-os/Default/`)
  - `request_login` HITL callback if session expired
  - OAuth tokens in BrowserOS SQLite DB for verification (read-only)

- [ ] How long can a recording session last?
  - Single flow recording (one portal, one job) — minutes
  - Exploratory discovery session (multiple paths) — potentially long
  - Define timeout and checkpoint behavior

### Backend contract for Ariadne translation

This motor is special: it produces common-language artifacts, it doesn't consume them.

- **Output**: normalized `AriadneStep` sequences with targets, actions, observe blocks,
  bifurcations, dead ends, and HITL annotations
- **Input**: portal definition (where to start, what profile data to use) and
  optionally an existing partial Ariadne path to continue from

The "translator" for this motor is the normalization pipeline (BrowserOS → common),
not a compilation pipeline (common → BrowserOS).

### Error taxonomy mapping

- `ReplayAborted` — operator cancelled the recording session
- `PortalStructureChanged` — not applicable (agent adapts, doesn't fail on structure)
- `ObservationFailed` — agent could not extract meaningful page state
- `TranslationError` — raw recording could not be normalized to common language

## Implementation dependencies

- Ariadne common-language models (defines what the normalized output looks like)
- Ariadne error taxonomy
- MCP proxy implementation (intercepts agent tool calls)
- CDP WebSocket client (captures page events)
- HITL callback interface definition
- Ariadne `recorder.py` and `storage.py` (receives and stores normalized paths)

## Open questions

1. Can we deploy agent scripts to the `graph/` directory and have BrowserOS
   execute them without UI interaction? (Documented as unknown.)
2. Is the BrowserOS `/chat` endpoint usable from Python to trigger an agent run
   programmatically? What is the exact schema?
3. Should the MCP proxy run persistently or only during recording sessions?
4. How do we handle agent non-determinism? Two recordings of the same flow may
   produce different step sequences. Does Ariadne merge them or keep both?
5. What is the minimum viable recording session? (Navigate + one action + snapshot
   = one-step path? Or do we require a complete flow?)
6. Port 9300 (Chrome extension WebSocket) — could this provide recording data
   that's easier to capture than CDP? Needs exploration.
