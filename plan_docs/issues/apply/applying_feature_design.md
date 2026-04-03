# Applying Feature — Design Document

> Status: **ready for implementation.** Design is complete and validated.
> Last updated: 2026-04-02 — finalized architecture, scoped OpenCV to ultra-stealth only, added Clean Slate Protocol, observe polling, fill fallback, missing-profile tool, legacy transition plan.

---

## 1. What We Are Building

Postulator 3001 currently produces tailored CV and motivation letter documents. The applying feature closes the last mile: **submitting the application automatically**.

The challenge is not just filling a form. Every portal is a maze with different paths, anti-bot layers, account walls, and unknown bifurcations. The system must be able to walk known paths cheaply, discover new paths safely, and always recover gracefully when it gets lost.

---

## 2. The Three-Level Applying Stack

The core design decision is a **graduated execution strategy** ordered by cost and safety:

### Level 3 — Deterministic Replay (preferred)
- We have already applied successfully through this portal before.
- Ariadne's Thread gives us a recorded map of the maze: the path, its known branches, and its known dead ends.
- We replay the path deterministically, substituting profile data and document paths into the recorded steps.
- Token cost: **zero**. Execution time: seconds.
- On failure (unknown state, DOM change, unexpected modal): **escalate to Level 2**, record the new path, promote back to Level 3 next time.

### Level 2 — OpenBrowser Agent
- No known path exists, or the recorded path failed.
- We trigger OpenBrowser with a system prompt that includes the job URL, profile context, and a strict output requirement: **"When done or at an irremediable dead-end, your final output MUST be an Ariadne's Thread JSON following the exact playbook schema, detailing every step you took using element texts (not IDs)."**
- The agent does the work AND produces the recording. No proxy, no CDP observer — the agent self-documents.
- HITL is handled natively via `HumanInteractTool` (`request_login`, `request_assistance`).
- Token cost: OpenBrowser's tokens, not ours. Used only when Level 3 is unavailable or broken.
- On success: the returned JSON is validated, stored in `apply_knowledge/`, and becomes the Level 3 path for next time.
- **Important:** The agent is both executor and recorder. We get the playbook for free with no instrumentation overhead.

**System prompt requirements for Level 2:**
1. Include the **exact Pydantic/JSON schema** of the Ariadne playbook format — no schema = hallucinated structure.
2. Include a **1-shot example** (`playbook_linkedin_easy_apply_v1.json`) so the agent knows what the output looks like.
3. Require `save_screenshot` calls at two mandatory moments: just before clicking submit, and immediately after the success confirmation screen.
4. Instruct: "If you encounter a required field whose answer is not in the provided profile/portal_answers, call `ask_user_for_missing_data(question_text)` and wait for the response before continuing."

**`ask_user_for_missing_data` tool:** When the agent encounters a question not in `portal_answers` (e.g. "Do you have a driver's license?"), instead of hallucinating an answer it calls this tool. The tool surfaces the question to the operator (terminal/TUI), stores the answer back in the profile (`profile_loader`) so it exists in `portal_answers` for all future applications, and resumes.

### Level 1 — Human (last resort)
- Triggered when: CAPTCHA that cannot be bypassed, first-time account creation on a new domain, portal behaviour that the LLM agent cannot resolve.
- Human takes over in BrowserOS. We record their session via snapshot diff or CDP.
- The recorded session feeds directly back into Level 3 (after review).
- HITL channel for MVP: terminal. Future: Textual TUI (same pattern as match_skill review).

---

## 3. Ariadne's Thread — The Maze Map

Ariadne's Thread is the **deterministic replay engine and path knowledge base**. Its job:

1. **Record** — during Level 2 or Level 1 execution, capture enough page state at each step to replay it later without ambiguity. Specifically: URL pattern, element text (not numeric IDs — those are session-scoped), snapshot signature of key elements, action taken, outcome.

2. **Replay** — given a known path, execute each step in order, resolving `{{variables}}` from the current job's profile and artifact context.

3. **Branch detection** — known bifurcations (easy apply modal vs. external ATS redirect vs. login wall) are encoded as branching conditions in the playbook. The executor evaluates which branch applies at runtime.

4. **Dead end classification** — known failure modes (404/expired job, Cloudflare block, unsupported ATS) are detected early and aborted cleanly with the correct escalation level rather than failing mid-form.

5. **Growth** — every escalation that resolves successfully adds a new path (or branch) to the knowledge base. The maze map grows with every run.

6. **Record** — when a human or LLM agent handles a session, the recorder captures their actions automatically and silently. The human is never asked to describe what they did. After the session, they get a generated playbook draft to confirm (one click), not to author.

### Key design rule: text selectors, not IDs — mandatory
Snapshot element IDs are stable within a single page load but change on every reload. **100% confirmed.** The playbook MUST use `selector_text` (element visible text) or a stable CSS path. Numeric IDs are forbidden in stored playbooks. This was validated in the LinkedIn Easy Apply dry-run and the XING session.

### Playbook format (confirmed — based on `playbook_linkedin_easy_apply_v1.json`)

Four confirmed components:

```json
{
  "source": "xing",
  "version": "2026-04-01",
  "entry_point": {
    "note": "Entry point is source-specific. Direct URL may 403 — use the safe navigation path.",
    "xing": {
      "start_url": "https://www.xing.com/jobs/find",
      "navigate_to_job": "search by job_id, click card in results panel"
    },
    "stepstone": {
      "start_url": "https://www.stepstone.de/work/{{keywords}}?am=INTERNAL",
      "navigate_to_job": "find card with matching job_id in listing, click to open panel",
      "warning": "Direct job URL (-inline.html) returns 403. Must come from search page."
    },
    "linkedin": {
      "start_url": "https://www.linkedin.com/jobs/view/{{job_id}}",
      "note": "Direct navigation works — LinkedIn does not block"
    }
  },
  "known_paths": {
    "easy_apply_modal": {
      "trigger": {"element_text": "Jetzt bewerben", "url_contains": "xing.com"},
      "steps": [
        {
          "id": "step_1",
          "observe": {
            "take_snapshot": true,
            "expected_elements": ["Nombre", "Apellido", "Email"],
            "on_missing": "bifurcation:unknown_form",
            "timeout_ms": 8000,
            "retry_interval_ms": 500
          },
          "actions": [
            {"action": "fill", "selector_text": "Nombre", "value": "{{profile.first_name}}"},
            {"action": "fill", "selector_text": "Apellido", "value": "{{profile.last_name}}"},
            {"action": "evaluate_script_react", "selector": "input[name='salary']", "value": "{{portal_answers.salary_expectation}}"}
          ]
        }
      ]
    }
  },
  "bifurcations": {
    "external_ats": {"detect": {"url_contains": ["greenhouse.io", "lever.co", "workday.com"]}, "response": "dead_end"},
    "captcha": {"detect": {"snapshot_contains": ["recaptcha", "verify you are human"]}, "response": "hitl:request_assistance"},
    "login_required": {"detect": {"url_contains": "/login", "element_text": "Anmelden"}, "response": "hitl:request_login"},
    "unknown_form": {"detect": {"observe_mismatch": true}, "response": "hitl:request_assistance"}
  },
  "dead_ends_observed": {
    "job_expired": {"url_patterns": ["404", "not-found", "stelle-nicht-mehr"]},
    "antibot_block": {"snapshot_contains": ["Access Denied", "Cloudflare"]}
  }
}
```

**The `observe` block is the safety mechanism.** Before executing a step's actions, the executor takes a snapshot and verifies `expected_elements` are present. If they're missing, we're either in an unexpected state or the UI changed — trigger the appropriate bifurcation. This is what prevents silent mid-form failures.

**ID resolution is always real-time.** The executor never stores element IDs between steps. Before each action: take snapshot → find element by `selector_text` → get its current numeric ID → pass ID to MCP in the same call. IDs are ephemeral and only valid within a single page load.

**`observe` polls, not one-shot.** If `expected_elements` are not found immediately, the executor retries every `retry_interval_ms` until `timeout_ms` is reached. Only then is it declared a mismatch. This handles slow SPA renders without false bifurcation triggers.

**`fill` auto-fallback.** The executor first tries native MCP `fill`. After the fill, it re-snapshots the element and checks if the value was applied. If the value is still empty (React controlled input), it automatically retries with `evaluate_script_react` and flags the field in the playbook as `react_required: true` so future replays skip the naive fill.

### Knowledge base on disk
```
data/apply_knowledge/
  xing/
    paths/easy_apply_modal_v1.json
    dead_ends/job_expired_patterns.json
    unknowns/2026-04-01_job_12345.json   ← pending human review/promotion
```

---

## 4. Session Recording — Automatic Playbook Generation

**Principle:** The user never describes their actions. Recording is automatic, silent, and happens in the background while the user just does the apply normally. At the end they get a draft playbook to confirm, not to write.

### Priority order for recording

| Method | What it captures | Blind spots |
|--------|-----------------|-------------|
| **BrowserOS native session log** | All MCP tool calls made by the agent — already structured | Only agent-driven actions, not manual user clicks |
| **CDP event injection** | All in-page user interactions (click, input, change, submit, navigation) | OS-level dialogs (native file picker) |
| **OS-level `evdev`** | Every mouse move, click, keystroke at hardware level | Can't see what element was clicked without correlating with screenshot |
| **Periodic snapshot diff** | DOM state changes between snapshots | Low temporal resolution — misses fast sequences |

Best approach: **CDP primary + evdev for OS dialogs + periodic snapshots for correlation**. These three together cover 100% of what the user does.

### BrowserOS native session log

BrowserOS creates a session directory at `~/.browseros/sessions/<uuid>/` each time a conversation starts. While those directories are currently empty (no agent tool use in those sessions), when the agent *does* use tools, it may log them there. **This needs to be verified** — if BrowserOS already logs MCP `tools/call` calls per session, we get Level 2 (agent) recordings for free with no additional work.

Action: inspect `~/.browseros/sessions/<uuid>/` after a real agent session that uses browser tools.

### CDP event capture

CDP is available at `ws://127.0.0.1:9101`. We inject a listener at session start:

```python
class CDPRecorder:
    """Records user interactions inside BrowserOS via Chrome DevTools Protocol."""

    async def start(self, target_id: str):
        async with websockets.connect(f"ws://127.0.0.1:9101/devtools/page/{target_id}") as ws:
            # Enable domains
            await ws.send(json.dumps({"method": "Page.enable", "id": 1}))
            await ws.send(json.dumps({"method": "Runtime.enable", "id": 2}))

            # Inject in-page event listener — captures clicks, inputs, submits
            await ws.send(json.dumps({
                "method": "Runtime.evaluate",
                "params": {"expression": CAPTURE_SCRIPT, "returnByValue": True},
                "id": 3
            }))

            # Listen for navigation and console events (our listener posts via console.log)
            async for message in ws:
                event = json.loads(message)
                self._handle_event(event)
```

```javascript
// CAPTURE_SCRIPT — injected into the page
(function() {
  const log = (type, data) => console.log(JSON.stringify({__rec: true, type, data, ts: Date.now()}));

  document.addEventListener('click', e => {
    log('click', {
      tag: e.target.tagName,
      text: e.target.innerText?.trim().slice(0, 80),
      x: e.clientX, y: e.clientY,
      selector: getCssPath(e.target)  // best-effort stable selector
    });
  }, true);

  document.addEventListener('change', e => {
    log('change', {tag: e.target.tagName, name: e.target.name, value: e.target.value});
  }, true);

  document.addEventListener('submit', e => {
    log('submit', {action: e.target.action});
  }, true);
})();
```

Each raw CDP event includes coordinates. We correlate with the nearest snapshot (taken every ~2s during recording) to resolve the element text — the stable selector we need for replay.

### OS-level recording via `evdev`

For native OS dialogs (file picker, OS-level auth prompts) that are invisible to CDP:

```python
import evdev

def record_os_input(duration_seconds: int) -> list[RawEvent]:
    """Reads raw mouse + keyboard events from /dev/input/ during a recording window."""
    devices = [evdev.InputDevice(path) for path in evdev.list_devices()]
    # Filter to keyboard + mouse devices
    ...
```

`evdev` requires read access to `/dev/input/` devices (typically needs `input` group membership or `sudo`). This is a one-time setup. The raw events (absolute mouse coordinates, key codes) are correlated with screenshots to reconstruct what happened.

### The correlation pipeline

```
CDP events (click at x,y + element text)  ─┐
evdev events (mouse at x,y, key presses)  ─┤─→ EventCorrelator ─→ RawActionSequence
Periodic snapshots (element text + bbox)  ─┘

RawActionSequence ─→ PlaybookNormalizer ─→ PlaybookDraft (text-based selectors, {{variables}})

PlaybookDraft ─→ human confirms (yes/edit/discard) ─→ apply_knowledge/<source>/paths/
```

The normalizer does three things:
1. Replaces raw coordinates with `element_text` (from snapshot correlation)
2. Replaces literal profile values with `{{variables}}` (`"Juan Pablo"` → `"{{first_name}}"`)
3. Clusters navigation + interaction events into named steps

### What the human actually sees

Not a raw event log. A human-readable draft:

```
Step 1 — Click "Jetzt bewerben" on xing.com/jobs/...
Step 2 — Fill "Nombre" with {{first_name}}
Step 3 — Fill "Apellido" with {{last_name}}
Step 4 — Select "Gute Kenntnisse (B2)" for German level
Step 5 — Fill "Gehalt" with {{salary_expectation}}
Step 6 — Upload {{cv_path}} via file picker
Step 7 — Click "Weiter"
Step 8 — Click "Jetzt bewerben" (submit)

Confirm this playbook? [y/edit/discard]
```

The human reads it, confirms it's correct, done. If they edit, they edit the draft (which is already in the right format). They never type steps from scratch.

### What gets recorded from Level 2 (OpenBrowser agent)

When the OpenBrowser agent runs a session, it drives BrowserOS via MCP tool calls. Those calls are already structured — they are the playbook. We observe the `/mcp` endpoint traffic (or the session log if BrowserOS exposes it) and reconstruct the playbook directly, without needing CDP or evdev. The variable substitution pass still applies (`"Juan Pablo"` → `"{{first_name}}"`).

---

## 5. LangGraph Pipeline Integration

The apply feature is a node (or subgraph) in the LangGraph pipeline, downstream of document generation. It receives from upstream:

| Input | Source |
|-------|--------|
| `source`, `job_id` | State |
| `application_url`, `application_method` | Ingestion node (with caveats — see Gap 1) |
| `cv_path`, `letter_path` | Render node |
| Profile data (name, email, phone, linkedin, etc.) | `profile_loader` |
| **Portal questions + answers** | Upstream pipeline (see below) |
| Credential reference (portal, username) | Secrets store (see Gap 2) |

The node decides which level to invoke, executes, and writes artifacts to `data/jobs/<source>/<job_id>/nodes/apply/`.

### Portal questions contract

Portals ask questions beyond what a CV contains: salary expectation, earliest start date, language proficiency levels, work permit status, willingness to relocate, etc. The apply node does not guess — it receives a `portal_answers` dict from upstream. The upstream pipeline is responsible for having already asked the user (or derived from profile) the answers to these questions before the apply node runs.

The apply node's job with respect to questions is only:
1. Know which questions a given portal asks (from the playbook)
2. Map each question to a key in `portal_answers`
3. Escalate to HITL if a required key is missing

```python
# What the apply node receives from upstream
portal_answers = {
    "salary_expectation": 65000,
    "start_date": "2026-06-01",
    "german_level": "Gute Kenntnisse (B2)",
    "work_permit": "EU citizen",
}
```

This means the apply node has zero reasoning responsibility about the answers — only form execution.

---

## 5. Clean Slate Protocol

Every application run, regardless of level, must use an isolated browser tab:

```
start:  new_hidden_page() → get page_id → all actions use this page_id
end:    close_page(page_id) — whether success, failure, or HITL abort
```

**Why:** If a Level 3 run fails mid-form, the tab is left with half-filled fields, an open modal, or an in-progress session. Reusing it on the next attempt produces unpredictable behavior. Closing and opening a fresh hidden page costs ~1 MCP call and guarantees a clean start.

**Exception:** The `setup-session` command (manual login) intentionally reuses the visible active page — the user is interacting with it directly.

---

## 6. Stealth Strategy — Crawl4AI vs BrowserOS Mouse Control

These two tools are not in competition — they serve different parts of the pipeline.

| Concern | Tool | Why |
|---------|------|-----|
| Job discovery / scraping | Crawl4AI | Parallel processes, fast, no alert risk for read-only crawling |
| Form filling / applying | BrowserOS + OS-level mouse | Real Chromium, real input events, logged-in session, human-indistinguishable |

### Why BrowserOS mouse control is stealthier

BrowserOS runs a real Chromium browser (not headless) with a real user profile and browser history. When we call BrowserOS MCP tools like `click` and `fill`, they go through Chromium's native input pipeline. But the most undetectable approach is to drive the mouse and keyboard at the **OS level** using `xdotool` (Linux) or `pyautogui`:

```python
# Synthetic event (detectable by fingerprinting)
mcp_call("fill", {"element": 9648, "value": "Juan Pablo"})

# OS-level input (indistinguishable from human)
import subprocess
subprocess.run(["xdotool", "mousemove", str(x), str(y), "click", "1"])
subprocess.run(["xdotool", "type", "--clearmodifiers", "Juan Pablo"])
```

The browser receives a genuine `mousemove` + `click` event from the OS input queue. There is no Playwright CDP channel, no synthetic event injection, no detectable automation fingerprint.

**When to use which:**
- Standard forms on cooperative portals: BrowserOS MCP `fill`/`click` is sufficient and simpler
- Portals with active anti-automation detection (Workday, some Cloudflare setups): OS-level mouse via `xdotool`
- React/Vue controlled inputs: `evaluate_script` with React-compatible native value setter (confirmed working on XING)

### React controlled inputs

Many portals (XING confirmed) use React's controlled input pattern. Standard `fill` sets the DOM value but does not trigger React's `onChange`, so the form state doesn't update. Fix:

```python
# React-compatible setter via evaluate_script
script = """
const el = document.querySelector('{selector}');
const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
    window.HTMLInputElement.prototype, 'value').set;
nativeInputValueSetter.call(el, '{value}');
el.dispatchEvent(new Event('input', {{ bubbles: true }}));
"""
mcp_call("evaluate_script", {"expression": script, "page": page_id})
```

This is required for: XING salary field, XING date spinbuttons, and any portal where `fill` appears to succeed but the value doesn't stick.

---

## 7. OpenCV — Ultra-Stealth Mode Only

OpenCV is **not a general dependency**. It is an isolated, optional module for a specific scenario.

### The boundary

| Mode | Dependencies | Covers |
|------|-------------|--------|
| **Standard (Level 3 + Level 2)** | Pure Python + HTTP | 95%+ of portals. MCP `upload_file` handles OS file picker natively — no vision needed. `fill` + `evaluate_script_react` + `click` by text covers all standard form interactions. |
| **Ultra-Stealth** | `opencv-python` + `xdotool` | Portals with maximum anti-automation detection (specific DataDome configs) that detect MCP synthetic events and block them. Hardware-level mouse + keyboard driven by screen coordinates from OpenCV. |

### When Ultra-Stealth triggers

Only when a portal is **confirmed** to block MCP-level interactions. Evidence: snapshot shows challenge page after attempted fill/click, `observe` detects antibot pattern. Never pre-emptively — it's slower and heavier.

### What OpenCV does in Ultra-Stealth

- Screenshot → template match known challenge patterns (reCAPTCHA, DataDome, Cloudflare)
- Screenshot → find element by visual template when DOM is inaccessible
- Navigate OS-level menus (e.g. if `upload_file` MCP tool fails and the native file picker appears outside Chromium)
- Pixel diff to verify actions took effect when DOM is not readable

### Implementation

Isolated module `src/apply/ultra_stealth.py`. Not imported unless explicitly triggered. `opencv-python` stays out of `pyproject.toml` core dependencies — added as optional extra (`pip install postulator[stealth]`).

---

## 7. Credential Safety

A credential given to the wrong recipient is a fraud vector. The rule:

- Credentials are stored with explicit **domain binding**: `{ "domain": "xing.com", "username": "...", "password_ref": "..." }`.
- Before any credential is passed to BrowserOS or OpenBrowser, the current page URL is verified to match the bound domain.
- Passwords are never logged, never written to artifacts, never passed as plaintext through the LangGraph state.
- Browser profiles (`data/profiles/<portal>/`) store session cookies. This is the preferred mechanism — no credential handling in code after initial login.
- `data/profiles/` is already covered by `.gitignore` (`data/` is excluded).

---

## 8. Danger Detection

Before taking any potentially risky action:

| Danger | Detection signal | Response |
|--------|-----------------|----------|
| Clicking too early (DOM not ready) | Snapshot is empty or missing expected element | Wait + retry with backoff |
| Anti-bot / Cloudflare | Snapshot contains challenge keywords | NOTIFY + ABORT, escalate |
| reCAPTCHA | Snapshot contains `recaptcha` frame | PAUSE → human |
| Login wall | URL redirected to login page | PAUSE → human (or session setup) |
| 404 / expired job | URL matches dead-end patterns | SILENT ABORT |
| Unknown form field | key missing from `portal_answers` | PAUSE → human before submit |
| React input not sticking | Pixel diff shows field unchanged after fill | Retry with `evaluate_script` React setter |
| Duplicate submission | `apply_meta.json` already exists | ABORT with warning |

---

## 9. Findings from Existing Documents and Live Sessions

### From `browseros_apply_design.md`
- BrowserOS MCP at `http://127.0.0.1:9200/mcp` accepts direct tool calls (60 tools) without LLM. The `Accept: application/json, text/event-stream` header is mandatory or it returns 500.
- LinkedIn Easy Apply was dry-run end-to-end (5 steps, 0 tokens, ~15 MCP calls, ~20 seconds). Traces in `traces/linkedin_easy_apply/`.
- CDP is available at `ws://127.0.0.1:9101` for session recording.
- Snapshot diff (periodic snapshots during manual session → infer steps from diff) is simpler than CDP and sufficient for playbook generation.
- Remaining unknowns: CDP recorder validation, antibot pattern library, ATS external playbooks, multi-step file upload dialogs, BrowserOS session persistence across restarts.

### From `stage2_cross_portal_and_autoapply.md`
- Crawl4AI's `AdaptiveCrawler.digest()` can discover all open positions on a company portal automatically (information foraging, stops at saturation). This is the cross-portal discovery path.
- `AsyncUrlSeeder(source="sitemap")` is faster and zero-token when a sitemap is available.
- Form filling via Playwright hooks for file uploads; `js_code` for React/Vue SPAs where Playwright events fail to trigger framework state.
- Account creation is always HITL (one-time per domain). Session persistence via `BrowserConfig(user_data_dir=..., use_persistent_context=True)` — no credentials in code after that.
- Submission safety rules already defined: human approval gate on first submission to any new domain, dry-run mode, no duplicate submissions.

### From `application_routing_extraction.md`
- `application_method` and `application_url` are not reliably extractable at scrape time. Currently deferred.
- The plan is a later interpretation/enrichment step combining source-specific heuristics + LLM. This is **Gap 1** — the apply node cannot function without knowing how to apply to a job.

### From `crawl4ai_scraper_correction.md` + `crawl4ai_usage.md`
- The scraper itself needs hardening before the applying feature can rely on its output. The `application_url` field the apply node needs lives in scraper output.
- Seven-stage correction plan exists. Key for us: Stage 2 (job-scoped listing artifacts including `application_url`) and Stage 5 (XING listing/detail merge so `application_url` is reliable).
- Standards rule: no direct LiteLLM calls, no custom extraction outside Crawl4AI strategies.

### From `scraper_fragility.md`
- Four known fragility points in the scraper: module-level instantiation, naive language detection, StepStone losing listing metadata, XING using generated CSS class names.
- Items 3 and 4 directly affect the richness and reliability of `application_url` and `application_method` fields the apply node depends on.

### From `apply_01_models_and_cli.md` + live exploration
- `src/apply/` already has a working partial implementation: `smart_adapter.py`, XING and StepStone adapters, using Crawl4AI C4A-Script directly. Models exist: `FormSelectors`, `ApplyMeta`, `ApplicationRecord`.
- The C4A-Script approach is not necessarily wrong — Crawl4AI C4A-Script can drive a headless browser faster and with less overhead for simple forms. The question is whether Crawl4AI's synthetic events trigger anti-bot detection on specific portals.
- Decision required: keep Crawl4AI for portals that cooperate, escalate to BrowserOS OS-level input for portals with active fingerprinting. The models may need extension (not replacement) to support both execution backends.

### From live BrowserOS sessions (2026-04-01)
- **Session was via MCP directly** — never used the OpenBrowser agent or LLM. All calls were `tools/call` JSON-RPC.
- **BrowserOS `~/.browseros/sessions/`** are AI agent session directories. They are created when a session starts but remain empty unless the agent uses browser tools. Real browser state (cookies, login sessions) lives at `~/.config/browser-os/Default/`.
- **LinkedIn Easy Apply**: 5 steps, 0 tokens, ~15 MCP calls, ~20s. All fields pre-filled from LinkedIn profile. Playbook recorded at `traces/linkedin_easy_apply/playbook_linkedin_easy_apply_v1.json`.
- **XING apply modal** — 3 steps confirmed:
  - Step 1: Contact info (name, email — pre-filled)
  - Step 2: Employer questions (start date spinbutton, salary expectation, German language level dropdown) — these map to `portal_answers` keys
  - Step 3: Document upload (`upload_file`)
- **XING React inputs**: `fill` silently fails on salary and date fields. `evaluate_script` with React native input value setter works. This is the required approach for any React/Vue portal.
- **Date spinbuttons** (XING): HTML `<input type="number" role="spinbutton">` — needs click + React setter, not standard fill.
- **StepStone 403 on direct URL navigation**: StepStone returns 403 if you navigate directly to a job URL without a referrer from their search page. Must navigate to search page first, then click through.
- **StepStone Easy Apply filter**: Confirmed working — `am=INTERNAL` in URL activates the Easy Apply filter. Jobs show "Easy Apply" button (class `res-tq4b10`).
- **Bifurcation: "¿Descartar solicitud?"** (LinkedIn): Closing the apply modal triggers a confirmation dialog. The executor must handle this branch — it is not part of the happy path.

---

## 10. Gaps

### Gap 1 — Application routing is not reliable yet
`application_url` and `application_method` are not reliably produced by the current scraper. The apply node has no way to know whether to submit via email, inline portal form, or external ATS without this. **Dependency:** scraper correction plan Stages 2 and 5, plus the application routing enrichment step.

### Gap 2 — Credential storage is undefined
We know credentials must be domain-bound and never touch code or state. We have no implementation yet: no secrets store, no binding contract, no injection mechanism for the OpenBrowser agent or BrowserOS client.

### Gap 3 — OpenBrowser integration is unexplored
We know OpenBrowser's agent is good and we want to use it for Level 2. We have not documented its API, how to pass context to it (documents, profile, target URL), how to get its execution trace back, or how to trigger it from inside LangGraph.

### Gap 4 — Recording from Level 2 ~~(proxy)~~ → solved via output contract
**Solved. No proxy needed.** The OpenBrowser agent system prompt requires the agent to output the Ariadne JSON as its final message. The agent self-documents as it executes — every step it took, every element it interacted with (by text), every bifurcation it encountered. We parse the JSON on completion and store it as the new Level 3 path. The proxy architecture (documented in `browseros_interfaces.md` Section 9) remains as a fallback if the output contract proves unreliable.

### Gap 5 — `src/apply/` legacy transition
The existing `src/apply/` (Crawl4AI/C4A-Script) is superseded by the PlaybookExecutor/BrowserOS approach. **Transition plan:**
- `smart_adapter.py` and `*ApplyAdapter` classes become thin routers: receive `job_id` + `source`, load the Ariadne playbook for that source, invoke `PlaybookExecutor`. They no longer own execution logic.
- `FormSelectors` is replaced by the Pydantic playbook models.
- `ApplyMeta` and `ApplicationRecord` are kept — they're the artifact contract and don't change.
- C4A-Script execution is removed. Crawl4AI remains in the scraper, not the apply stack.

### Gap 9 — Pydantic playbook schema not defined
The JSON format is validated by example but not by code. The `PlaybookExecutor` will fail silently or crash on schema drift. **Must define before implementing the executor:** `Playbook`, `EntryPoint`, `KnownPath`, `Step`, `ObserveBlock`, `Action`, `Bifurcation`, `DeadEnd` as Pydantic v2 models. This resolves all ambiguous field types (timeouts, selector types, variable interpolation format) at design time.

### Gap 8 — Recording pipeline (simplified)
Recording from Level 2 is solved via agent output contract (no CDP/evdev needed). The only remaining work: JSON schema validation on the returned playbook draft, and a lightweight human confirmation step before storing to `apply_knowledge/`.

### Gap 6 — HITL channel for applying is not wired
The apply HITL is different from the match_skill HITL (which uses a Textual TUI and LangGraph interrupt). Apply HITL needs to pause mid-execution (inside a BrowserOS session), surface a screenshot + context to the operator, and resume with their input. The channel and interrupt mechanism are undefined.

### Gap 7 — Danger detection library is empty
We have a classification of dangers (anti-bot, CAPTCHA, wrong-recipient credential, etc.) but no implementation. No pattern library for known anti-bot signals, no snapshot analysis for CAPTCHA frames.

---

## 9. What We Can Get from Crawl4AI

| Capability | How it helps |
|-----------|-------------|
| `AdaptiveCrawler.digest()` | Cross-portal discovery: find all open positions on a company ATS portal automatically |
| `AsyncUrlSeeder(source="sitemap")` | Faster discovery when sitemap is available — zero tokens |
| `BrowserConfig(enable_stealth=True)` | Defeat fingerprinting on Cloudflare/DataDome portals |
| `BrowserConfig(headless=False)` | Required for some DataDome challenges that inspect rendering |
| `BrowserConfig(user_data_dir=..., use_persistent_context=True)` | Browser profile persistence — session reuse without credential handling in code |
| Playwright hooks (`on_page_context_created`) | File upload interactions (no JS equivalent) |
| `js_code` in `CrawlerRunConfig` | Form filling on React/Vue SPAs where Playwright events don't trigger framework state |
| `LLMExtractionStrategy` | Application routing enrichment step (determine `application_method` / `application_url` from raw ingest evidence) |
| `DomainFilter` + `URLPatternFilter` | Scope cross-portal discovery to job-like URLs only |

Crawl4AI's role in applying is primarily **discovery and session management**, not form execution. Form execution happens through BrowserOS MCP or OpenBrowser.

---

## 12. What We Can Get from OpenBrowser

| Capability | How it helps |
|-----------|-------------|
| LLM agent for form navigation | Level 2 execution — handles unknown forms, multi-step flows, unexpected modals without us writing playbook logic |
| Direct MCP tool calls (60 tools, 0 tokens) | Level 3 replay — `click`, `fill`, `upload_file`, `take_snapshot`, `navigate_page`, `save_screenshot` |
| CDP at `ws://127.0.0.1:9101` | Session recording — reconstruct playbook from user/agent actions |
| `take_snapshot` with interactive element IDs | Replay targeting — find elements by text within a session |
| `save_screenshot` | Automatic evidence before every HITL pause |
| Browser state persistence (cookies in `~/.config/browser-os/`) | Login session reuse between runs |

The key insight: **BrowserOS is our actuator for both Level 2 and Level 3**. The difference is who drives it — the OpenBrowser LLM agent (Level 2) or our PlaybookExecutor (Level 3).

---

## 13. Open Questions / Doubts

1. **OpenBrowser agent API**: How do we pass context (job URL, profile data, CV path) to the OpenBrowser agent programmatically? Is there an API for structured context injection, or does it only accept natural language prompts?

2. **Recording from Level 2**: If the OpenBrowser LLM agent drives BrowserOS, can we observe its MCP calls and reconstruct a playbook from them? Or do we need to run snapshot diffs in parallel during its execution?

3. **Credential injection into OpenBrowser**: When the agent needs to log in, how do we pass credentials safely? We cannot pass plaintext through a natural language prompt. Is there a structured context mechanism, or do we rely on the browser profile already being logged in?

4. **BrowserOS session persistence**: Do login cookies survive BrowserOS restarts (`~/.config/browser-os/Default/`)? The dry-run did not test this. If they don't, every run requires a re-login HITL.

5. **Playbook granularity**: Should a playbook branch cover the full apply flow from the job listing page, or only from the point the "Apply" button is clicked? Starting from the listing URL is more reproducible; starting from the modal is more reusable across discovery paths.

6. **ATS priority**: Greenhouse and Lever are clean (low bot protection, mostly static). Workday is the most common but hardest (heavy SPA + Cloudflare). Which do we target first for Level 3 playbooks?

7. **Form field mapper for unknown forms**: When the OpenBrowser agent encounters a field we've never seen, it may fill it incorrectly. Do we need a pre-submit review gate for every new field type, or do we trust the agent and review the `ApplicationRecord` artifact after the fact?

8. **`application_method: email` timing**: Email application is deferred, but some portals (especially German Mittelstand companies) primarily use email. Should the apply node detect this early and produce a structured "ready to send" artifact rather than silently doing nothing?

9. **Dry-run as default**: Should dry-run be opt-out (safe by default) or opt-in? Given the irreversibility of form submission, the argument for opt-out is strong — but it means every first run on a new portal requires an explicit flag to actually submit.

10. **CDP recorder complexity vs. snapshot diff**: CDP gives us a clean event stream but requires websocket plumbing and event interpretation. Snapshot diff is simpler and produces steps in the same format the PlaybookExecutor already uses. Is there a case where snapshot diff is insufficient?

11. **BrowserOS session log format**: Does `~/.browseros/sessions/<uuid>/` contain a log of MCP tool calls when the agent uses browser tools? If yes, Level 2 recording is already solved. If no, we build the CDP observer. This needs a single test run to answer.

12. **evdev access**: Is the user already in the `input` group, or does this need a one-time `sudo usermod -aG input jp`? Also: does `evdev` correctly separate mouse devices from touchpad on this machine?

13. **xdotool coordinate mapping**: When we use OS-level mouse control, we need to know where on screen to click. BrowserOS snapshot gives us element text but not screen coordinates. We need either: (a) `evaluate_script` to get `getBoundingClientRect()` and map to screen coordinates, or (b) OpenCV template matching on the screenshot. Which is more reliable?

12. **Crawl4AI vs BrowserOS backend selection**: Should the backend (Crawl4AI C4A-Script vs BrowserOS MCP vs xdotool) be selected per-portal in the playbook, or should it be a runtime decision based on detected anti-bot level? A static per-portal config is simpler but less adaptive.

13. **OpenCV dependency weight**: `opencv-python` is ~80MB. Is it acceptable as a core dependency, or should it be optional (installed only when vision features are needed)?

---

## 14. Proposed Implementation Order

The next steps are **concrete, unblocked, and sufficient to prove end-to-end Level 3**:

0. **Pydantic playbook models** — `Playbook`, `EntryPoint`, `KnownPath`, `Step`, `ObserveBlock`, `Action`, `Bifurcation`, `DeadEnd`. Define these first. They resolve all ambiguous field types, force explicit decisions on timeout/retry/selector formats, and give the PlaybookExecutor a typed interface to parse against. The Level 2 system prompt's JSON schema is generated from these models. **Do this before writing any executor code.**

1. **`BrowserOSClient` (Python)** — wrapper for `POST http://127.0.0.1:9200/mcp`. Methods: `initialize()` (capture `Mcp-Session-Id`), `new_hidden_page()`, `close_page(page_id)`, `take_snapshot(page_id)`, `click(element_id)`, `fill(element_id, value)`, `evaluate_script_react(selector, value)`, `navigate(url, page_id)`, `save_screenshot(path, page_id)`, `upload_file(element_id, file_path)`. Note: takes element IDs, not text — ID resolution is the executor's responsibility.

2. **`PlaybookExecutor` (Python)** — parses `Playbook` model, injects profile + `portal_answers` dict as `{{variables}}`, executes step by step. Per step: poll `observe` block (snapshot + verify `expected_elements` with timeout/retry), resolve `selector_text` → current element ID, execute `actions`, auto-fallback `fill` → `evaluate_script_react` on failure. Supported action types: `fill`, `evaluate_script_react`, `click`, `select_option`, `upload_file`, `navigate`.

3. **HITL interrupt** — when `observe` finds an unmapped bifurcation or `human_required` action: call `save_screenshot`, surface to terminal with context (`[c]ontinue / [s]kip / [a]bort`), record decision in execution trace. Terminal MVP first, Textual TUI later.

Then:

4. **Application routing enrichment** — reliable `application_method` + `application_url` from ingest (unblocks knowing where to apply).
5. **Credential store** — domain-bound secrets, required before any run needing login.
6. **Ariadne's Thread storage** — `apply_knowledge/` on disk, playbook schema validation, path promotion workflow.
7. **OpenCV `VisualVerifier`** — fill verification, CAPTCHA detection. Optional dependency.
8. **LangGraph apply node** — wires everything into the pipeline with proper state contracts.
9. **First real playbooks** — LinkedIn (dry-run already done), XING (traces exist), StepStone (search-first entry point required).
