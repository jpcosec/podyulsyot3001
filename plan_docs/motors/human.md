# Human Motor — Placeholder

Date: 2026-04-05
Status: design-only, no code exists

## What this motor is

A person sitting at the browser, manually navigating, clicking, typing, deciding.
The human is a motor like any other — they act on pages. The same recording pipeline
(watch → record → process → update path) that the BrowserOS Agent motor uses can
attach to a human session to capture what they do and produce Ariadne paths.

The human motor is the original source of truth: every Ariadne path starts as
something a human did first.

## Why it's a separate motor

- The BrowserOS Agent motor uses the OpenBrowser LLM to decide and act. The human
  motor has no LLM — the human decides and acts.
- The BrowserOS CLI motor replays a known path deterministically. The human motor
  has no playbook — the human explores freely.
- The human motor can do things no other motor can: solve CAPTCHAs, interpret
  ambiguous UI, make judgment calls about unexpected form fields, log in to portals.

The human motor is not "BrowserOS with a human fallback." It's the human as the
primary actor, with the system watching and learning.

## Use cases

- **First path recording**: no Ariadne path exists for a portal. A human walks
  through the flow manually while the recording pipeline captures it.
- **Path correction**: an existing Ariadne path is broken (portal changed). A
  human re-walks the flow so the recording pipeline can produce an updated path.
- **Edge case handling**: the apply flow hit a branch point that no motor can
  handle (CAPTCHA, 2FA, unusual form). A human steps in, resolves it, and the
  recording captures the resolution.
- **Quality verification**: a human walks through a flow to visually verify that
  the deterministic replay is doing the right thing, comparing what they see to
  what the Ariadne path expects.

## What the human does vs what the system does

| Concern | Human | System |
|---|---|---|
| Navigate pages | Yes — clicks, types, decides | No — watches only |
| Solve CAPTCHAs / 2FA | Yes | No |
| Fill form fields | Yes | No |
| Decide which path to take | Yes | No |
| Capture raw events | No | Yes — CDP events, snapshots, screenshots |
| Correlate events into steps | No | Yes — same pipeline as agent motor |
| Normalize to common language | No | Yes — same normalization as agent motor |
| Annotate steps | Optionally (tags, notes) | Automatically (timestamps, element IDs) |
| Update Ariadne path | No | Yes — stores normalized path as draft |

## Recording pipeline (shared with BrowserOS Agent motor)

The recording pipeline is the same regardless of whether the actor is a human or
an LLM agent. The only difference is the event source.

### Event sources for human sessions

**CDP (Chrome DevTools Protocol, port 9101):**
- In-page capture script logs click, change, submit events via `console.log()`
- Events arrive through `Runtime.consoleAPICalled`
- `Page.frameNavigated` tracks navigation and triggers script re-injection
- `Network.requestWillBeSent` captures form submissions

**MCP snapshots (port 9200):**
- Periodic `take_snapshot` calls to capture element state
- Screenshots at key moments (navigation, form fill, submit)
- Correlates CDP events with snapshot elements for text-based identification

**Human annotations (optional):**
- Human can flag steps during recording ("this is the submit button",
  "this field is always different per job", "dead end here")
- Annotations become metadata on the normalized AriadneStep

### Pipeline stages

1. **Watch** — capture CDP events + periodic snapshots during human session
2. **Record** — log raw events with timestamps and element correlation
3. **Process** — normalize raw events into AriadneStep common language
   (same normalization rules as BrowserOS Agent motor)
4. **Update** — store normalized path in Ariadne as draft, ready for
   verification by a deterministic motor

## What needs to be documented before implementation

### Session control

- [ ] How does the human signal "start recording"?
  - CLI command? (`automation human record --source linkedin`)
  - Button in a TUI?
  - The system opens BrowserOS and says "go"?

- [ ] How does the human signal "stop recording"?
  - Press Enter in terminal? (current pattern for `setup_session`)
  - Close the browser page?
  - Explicit CLI command?

- [ ] How does the human signal step boundaries?
  - Automatically inferred from navigation + time gaps?
  - Human presses a key to mark "this is a new step"?
  - Both (auto-detect with manual override)?

### Annotation interface

- [ ] Can the human add notes to steps during recording?
- [ ] Can the human tag steps with ariadne_tag names?
- [ ] Can the human mark a step as `human_required` (meaning "this step will
  always need a human, even during replay")?
- [ ] Can the human mark bifurcation points ("sometimes this goes left,
  sometimes right")?
- [ ] What is the UI for annotation? Terminal? TUI overlay? Post-recording review?

### Portal authentication

- [ ] Human sessions use BrowserOS's persistent browser profile (cookies in
  `~/.config/browser-os/Default/`). The human logs in if needed — that's part
  of what they do.
- [ ] Should login steps be recorded as part of the path or excluded?
  (Probably excluded — login is a prerequisite, not part of the apply flow.)

### Handoff to/from other motors

- [ ] Can a human session hand off to a deterministic motor mid-flow?
  ("I've gotten past the CAPTCHA, now let the BrowserOS CLI take over.")
- [ ] Can a deterministic motor hand off to a human mid-flow?
  ("The form has an unexpected field, human please handle this step.")
- [ ] How is mid-flow handoff represented in the recording pipeline?

### Verification of human recordings

- [ ] After a human records a path, how is it verified?
  - Replay via BrowserOS CLI against the same portal
  - If replay succeeds → promote from draft to verified
  - If replay fails → flag differences for human review

## Relationship to other motors

- **BrowserOS Agent motor**: both produce Ariadne paths via the same recording
  pipeline. The agent uses an LLM to act; the human uses their brain. The system's
  capture and normalization is identical.
- **BrowserOS CLI motor**: consumes the paths that human (and agent) motors produce.
  Also used to verify human recordings via replay.
- **Vision motor**: could provide real-time feedback to the human during recording
  ("I can see the Submit button at these coordinates") but this is a future concern.
- **OS Native Tools motor**: if the human is acting via OS native input (not browser
  clicks), the recording pipeline would need OS-level event capture instead of CDP.
  This is a future concern.

## Implementation dependencies

- CDP WebSocket client (captures page events during human sessions)
- MCP snapshot client (periodic element state capture)
- Ariadne common-language models (defines normalized output)
- Ariadne `recorder.py` and `storage.py` (receives and stores draft paths)
- Session control interface (start/stop/annotate — even a minimal CLI version)

## Open questions

1. Is the annotation interface needed for v1, or is auto-inference from CDP events
   sufficient for initial path recording?
2. Should human recordings go through a post-recording review step (human sees
   the normalized steps and corrects them) before storing as draft?
3. How do we distinguish intentional human pauses (reading the page, thinking)
   from unintentional delays (distracted, stepped away)? Does it matter for the
   normalized path?
4. Can the human motor and BrowserOS Agent motor run simultaneously on the same
   session? (Human does some steps, agent does others, recording captures both.)
