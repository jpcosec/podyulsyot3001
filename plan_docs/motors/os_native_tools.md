# OS Native Tools Motor — Placeholder

Date: 2026-04-05
Status: design-only, no code exists

## What this motor should do

Act on the OS level — physical mouse clicks, keyboard input, coordinate-based
interaction. This is the "hands" motor: it executes actions that browser-level
automation cannot (or should not) perform.

Use cases:

- Click at absolute screen coordinates (when DOM element IDs are unreliable or absent)
- Type via OS input events (bypasses JS input interception / bot detection)
- Drag and drop across non-standard UI components
- Interact with native OS dialogs (file pickers, auth prompts)
- Ultra-stealth input that mimics human timing and movement patterns

## Relationship to other motors

- **Vision motor looks, OS native acts.** Vision produces coordinates and presence
  confirmations; OS native consumes them for physical interaction. Neither depends
  on the other — OS native can receive coordinates from any source.
- **Escalation path, not default.** The normal flow uses Crawl4AI or BrowserOS.
  OS native is invoked when those fail or when stealth requirements demand it.
- **Ariadne steps translate to OS native commands.** The common-language translator
  compiles `AriadneAction` intents into native input calls, same as any other motor.

## What needs to be documented before implementation

### Interaction primitives

What atomic actions does this motor expose?

- [ ] `click(x, y)` — single click at screen coordinates
- [ ] `double_click(x, y)`
- [ ] `right_click(x, y)`
- [ ] `type_text(text)` — keystroke-by-keystroke with human-like timing
- [ ] `press_key(key)` — single key press (Enter, Tab, Escape, etc.)
- [ ] `key_combo(keys)` — modifier combinations (Ctrl+A, Ctrl+V)
- [ ] `drag(from_x, from_y, to_x, to_y)`
- [ ] `scroll(x, y, amount)`
- [ ] `move_mouse(x, y)` — move without clicking (for hover-dependent UIs)
- [ ] `wait_idle(timeout)` — wait for input queue to drain

### Coordinate source contract

How does this motor receive target coordinates?

- From vision motor (image template match → bounding box center)
- From BrowserOS snapshot (element ID → JS bounding rect → screen coordinates)
- From Ariadne step (hardcoded coordinates for known-stable layouts)
- From manual specification (operator provides coordinates)

Define which sources are supported and the resolution order.

### Timing and humanization

- [ ] Keystroke delay model (fixed, random uniform, gaussian?)
- [ ] Mouse movement model (linear, bezier curve, jitter?)
- [ ] Inter-action delay policy
- [ ] Should these be configurable per step or per motor instance?

### Platform support

- [ ] Linux (X11 / Wayland) — which input API? (`xdotool`, `ydotool`, `evdev`, `uinput`?)
- [ ] Is cross-platform support a goal or Linux-only?

### Stealth characteristics

- [ ] What makes this motor "stealthier" than BrowserOS `click`/`fill`?
- [ ] Does it bypass specific bot detection vectors? Which ones?
- [ ] Are there known detection methods it does NOT bypass?

### Safety and opt-in

- [ ] How is OS native explicitly opted into? (CLI flag, Ariadne step annotation, motor selector?)
- [ ] What prevents accidental OS native execution in automated/CI contexts?
- [ ] Is there a dry-run mode that logs intended actions without executing?

### Backend contract for Ariadne translation

What does the translator need to compile from common language?

- `AriadneTarget` with coordinates or with vision hint → resolve to `(x, y)`
- `AriadneAction` intent `click` → `os_native.click(x, y)`
- `AriadneAction` intent `fill` → `os_native.type_text(value)` (preceded by click to focus)
- `AriadneAction` intent `upload` → unclear: OS file dialog interaction? Screenshot + vision?
- `AriadneAction` intent `observe` → not this motor's job (delegate to vision or BrowserOS)

### Error taxonomy mapping

- `TargetNotFound` — coordinates could not be resolved from any source
- `ObservationFailed` — not applicable (this motor doesn't observe)
- `ReplayAborted` — operator stopped execution

## Implementation dependencies

- Ariadne common-language models (must exist first)
- Ariadne error taxonomy (must exist first)
- Coordinate source contract (define before building the translator)
- At least one coordinate provider working (vision motor or BrowserOS bounding rect export)

## Open questions

1. Should this motor own screen capture for its own feedback loop, or always
   delegate observation to the vision motor?
2. Is `xdotool` sufficient for X11, or do we need lower-level `evdev`/`uinput`
   for stealth against advanced bot detection?
3. How does this motor handle multi-monitor setups and DPI scaling?
4. Should humanization parameters be part of the motor config or part of the
   Ariadne step model?
