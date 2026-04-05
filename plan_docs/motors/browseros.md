# BrowserOS Motor — Current State

Date: 2026-04-04

## What BrowserOS actually does today

BrowserOS is a desktop browser application (Chromium-based) that exposes multiple
programmatic interfaces. The codebase currently uses only the MCP interface for
deterministic apply flows, but BrowserOS exposes significantly more.

### Two execution paths exist in the plan

The refactor plan splits BrowserOS into:

- **CLI motor** — deterministic tool-by-tool MCP execution, no LLM
- **Agent motor** — OpenBrowser LLM agent-driven path for recording/discovery

Only the CLI path is implemented today.

---

## BrowserOS interfaces available

Source: `docs/reference/external_libs/browseros_interfaces.md` (live-verified 2026-04-02)

### Port 9200 — MCP Server (primary, currently used)

JSON-RPC `tools/call` endpoint. 60 browser tools. No LLM required.

**Observation tools:**

- `take_snapshot` — interactive elements with text + numeric IDs (session-scoped)
- `take_enhanced_snapshot` — richer element metadata
- `get_dom` — full DOM HTML
- `search_dom` — query DOM by selector/text
- `get_page_content` — plain text content
- `get_page_links` — all links on page
- `get_console_logs` — browser console output
- `take_screenshot` / `save_screenshot` — PNG capture

**Navigation:**

- `navigate_page`, `new_page`, `new_hidden_page`, `list_pages`, `get_active_page`,
  `show_page`, `move_page`, `close_page`

**Interaction:**

- `click`, `click_at` (coordinates), `fill`, `check`/`uncheck`, `select_option`,
  `upload_file`, `press_key`, `focus`, `clear`, `hover`/`hover_at`, `type_at`,
  `drag`/`drag_at`, `scroll`, `handle_dialog`

**Scripting:**

- `evaluate_script` — execute JavaScript expression in page context

**Utilities:**

- `save_pdf`, `download_file`, `browseros_info`

### Port 9101 — CDP (Chrome DevTools Protocol)

Full Chromium control via WebSocket. Capabilities include DOM events, JS injection,
network monitoring, and input recording. This is the planned recording interface
for the agent motor path (not yet implemented).

### Port 9300 — Chrome Extension WebSocket

Unknown capabilities. Needs exploration.

### SQLite DB — `~/.config/browser-os/.browseros/browseros.db`

Contains `oauth_tokens` (plaintext access/refresh tokens for connected providers),
`identity` (install UUID), and `rate_limiter` records. Read-only use for session
state verification.

### Graph directory — `~/.config/browser-os/.browseros/graph/`

OpenBrowser agent scripts stored as TypeScript files. Each script uses the
`Agent` API (`agent.nav()`, `agent.extract()`, `agent.act()`, `agent.verify()`).
Potential integration point for the agent motor path.

### Browser profile — `~/.config/browser-os/Default/`

Real Chromium profile with cookies, local storage, IndexedDB. Login sessions
persist across restarts. We do not manage this — BrowserOS manages it.

---

## Current implementation (CLI path only)

Four files in `src/apply/`:

### `browseros_client.py` — MCP client

Thin JSON-RPC client over HTTP to `http://127.0.0.1:9200/mcp`.

**Session lifecycle:**
1. `initialize()` — MCP handshake, stores `Mcp-Session-Id` header
2. All subsequent `call_tool()` calls auto-initialize if needed

**Tools currently wrapped:**

| Client method | BrowserOS tool | Purpose |
|---|---|---|
| `new_page()` / `new_hidden_page()` | `new_page` / `new_hidden_page` | Create browser tab |
| `close_page()` / `show_page()` | `close_page` / `show_page` | Tab management |
| `navigate()` | `navigate_page` | URL navigation |
| `take_snapshot()` | `take_snapshot` | Capture + parse interactive elements |
| `click()` | `click` | Click by element ID |
| `fill()` | `fill` | Set input value |
| `select_option()` | `select_option` | Dropdown selection |
| `upload_file()` | `upload_file` | File upload |
| `save_screenshot()` | `save_screenshot` | Save PNG to disk |
| `evaluate_script()` | `evaluate_script` | Raw JS execution |
| `evaluate_script_react()` | `evaluate_script` (composed) | React input workaround |
| `browseros_info()` | `browseros_info` | Server metadata |

**Snapshot parsing:** `take_snapshot()` returns a list of `SnapshotElement` dataclasses
parsed from text lines matching `[{id}] {type} "{text}"`. Elements are identified
by numeric IDs that are session-scoped (stable within a page load, change on navigation).

**Tools available but NOT wrapped:** `take_enhanced_snapshot`, `get_dom`, `search_dom`,
`get_page_content`, `get_page_links`, `get_console_logs`, `click_at`, `press_key`,
`focus`, `clear`, `hover`, `hover_at`, `type_at`, `drag`, `drag_at`, `scroll`,
`handle_dialog`, `check`, `uncheck`, `take_screenshot` (base64 variant),
`save_pdf`, `download_file`, `list_pages`, `get_active_page`, `move_page`.

### `browseros_models.py` — Playbook data model

Pydantic models defining the playbook schema (currently BrowserOS-coupled, will
become Ariadne common language models post-refactor):

- `BrowserOSPlaybook` — top-level: meta, entry_point, path, steps, dead_ends, bifurcations
- `PlaybookStep` — one replayable step: observe block, actions, next button, human/dry-run gates
- `PlaybookAction` — executable action: tool, selector_text, value, fallback
- `ObserveBlock` — expected elements that must be present before step executes
- `PlaybookMeta` — source, flow, version, status metadata
- `PlaybookEntryPoint` — URL pattern, trigger element, ariadne_tag
- `PlaybookFallback` — alternative action when primary target is absent

**Action tools defined:** `click`, `fill`, `select_option`, `upload_file`, `evaluate_script_react`

### `browseros_executor.py` — Playbook executor

`BrowserOSPlaybookExecutor` replays a playbook against a live BrowserOS page.

**Execution loop per step:**
1. `take_snapshot()` — observe current page state
2. `_assert_expected_elements()` — verify all expected elements are present (fuzzy text match)
3. Check `dry_run_stop` / `human_required` gates
4. Execute each action: resolve element by text → call client method
5. Click `next_button_text` if present

**Element resolution:** fuzzy text matching against snapshot elements.
`_resolve_element_id()` first tries exact normalized match, then substring match.
Raises `BrowserOSObserveError` if not found.

**Template rendering:** `{{key.subkey}}` placeholders resolved from nested context dict.
Unresolved placeholders in selector_text raise an error; unresolved in value skip
the action with a warning.

**Fallback handling:** if primary selector_text is not found and `action.fallback`
exists, recursively execute the fallback action instead.

### `browseros_backend.py` — Provider wiring

`BrowserOSApplyProvider` — source-specific provider backed by BrowserOS MCP.

**Constructor takes:** source_name, portal_base_url, playbook_path, candidate_profile,
data_manager, client.

**Execution flow:**
1. Idempotency check (block if already submitted)
2. Read ingest artifact for application_url
3. Load and validate playbook JSON
4. Create hidden page → navigate to application URL
5. Run executor with playbook + context
6. Save screenshot + application record + apply meta
7. Close page (finally block)

**Currently registered providers:**
- `linkedin` — playbook: `src/apply/playbooks/linkedin_easy_apply_v1.json`

(Only LinkedIn has a BrowserOS path today.)

---

## The LinkedIn playbook (only packaged playbook)

File: `src/apply/playbooks/linkedin_easy_apply_v1.json`

Path: `linkedin.easy_apply.standard`
Status: `dry_run_complete` (recorded 2026-04-01, stopped before submit)

**5 steps:**
1. `contact_info` — verify/fill name, phone, email (pre-filled from LinkedIn profile)
2. `cv_selection` — select saved CV or upload new one (with fallback)
3. `experience_review` — observe only, no actions
4. `additional_questions` — observe only, `human_required: "conditional"` for unknown fields
5. `review` — final review, `dry_run_stop: true`, `human_required: true` for submit confirmation

**Notable features used:**
- `bifurcations` — documented decision tree at entry point and step 4
- `dead_ends_observed` — empty but structurally present
- `ariadne_tag` — every step tagged for Ariadne path naming
- `fallback` — step 2 falls back from "select saved CV" to "upload CV"
- Localized element text (Spanish: "Solicitud sencilla", "Enviar solicitud")

---

## Capabilities summary

| Capability | CLI path (implemented) | Agent path (planned) |
|---|---|---|
| Page management | Yes (create, navigate, close) | Not implemented |
| Snapshot observation | Yes (text-based element parsing) | Planned via CDP recording |
| Element interaction | Yes (click, fill, select, upload) | Planned via `agent.act()` |
| JS execution | Yes (evaluate_script, React workaround) | Planned via `agent.extract()` |
| Screenshots | Yes (save to disk) | Not implemented |
| Playbook replay | Yes (full executor loop) | Not applicable (agent is adaptive) |
| Path recording | Not implemented | Planned (CDP + MCP proxy) |
| HITL gates | Yes (human_required, dry_run_stop) | Planned via HumanInteractTool |
| Session setup | Yes (manual login, page visible) | Not implemented |

## BrowserOS features used vs available

**Used today (12 of 60 tools):**

- `browseros_info`, `new_page`, `new_hidden_page`, `close_page`, `show_page`
- `navigate_page`, `take_snapshot`
- `click`, `fill`, `select_option`, `upload_file`
- `evaluate_script` (direct + React composition), `save_screenshot`

**Available but not used (48+ tools):**

- Enhanced observation: `take_enhanced_snapshot`, `get_dom`, `search_dom`,
  `get_page_content`, `get_page_links`, `get_console_logs`
- Coordinate interaction: `click_at`, `hover_at`, `type_at`, `drag_at`
- Keyboard/state: `press_key`, `focus`, `clear`, `check`, `uncheck`, `handle_dialog`
- Navigation: `list_pages`, `get_active_page`, `move_page`
- Utilities: `save_pdf`, `download_file`
- Full CDP interface (port 9101) — recording, network monitoring, event capture
- Extension WebSocket (port 9300) — unknown capabilities
- Graph directory — agent script deployment
- OpenBrowser Agent API — `agent.nav()`, `agent.extract()`, `agent.act()`, `agent.verify()`

## Known critical behaviors

1. **Snapshot IDs are session-scoped.** Element IDs change on any navigation/reload.
   The executor correctly uses text matching, not numeric IDs, for replay.
2. **React controlled inputs.** `fill` does not trigger React `onChange`. The
   `evaluate_script_react()` workaround uses the native value setter + input event
   dispatch. Confirmed required on XING salary fields and date spinbuttons.
3. **MCP Session-Id.** Required for session continuity. The client stores it from
   the initialize response header.

## Existing documentation

- Apply README: `src/apply/README.md`
- BrowserOS interface reference: `docs/reference/external_libs/browseros_interfaces.md`

## Known gaps between docs and code

1. **Agent path is entirely unimplemented.** The interface reference documents CDP
   recording, MCP proxy architecture, and OpenBrowser agent API in detail, but
   none of this exists as code yet.
2. **Only LinkedIn has a BrowserOS provider.** XING and StepStone are Crawl4AI-only
   for apply despite XING being documented as needing the React workaround.
3. **Playbook model is BrowserOS-coupled.** `browseros_models.py` is the proto-Ariadne
   common language but uses BrowserOS tool names (`take_snapshot`, `evaluate_script_react`)
   instead of backend-neutral intents.
4. **No recording pipeline.** The interface reference has a detailed MCP proxy
   skeleton and CDP capture script, but no code implements recording or
   normalization into playbook format.
