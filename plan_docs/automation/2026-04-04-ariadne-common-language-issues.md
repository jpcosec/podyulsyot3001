# Ariadne Common Language — Open Issues Before Phase 2

Date: 2026-04-04

## Context

Ariadne is intended to work in a backend-neutral "common language" that deterministic
translators compile into backend-specific representations (Crawl4AI C4A-Scripts,
BrowserOS tool calls, OpenCV commands, etc.).

This document captures conceptual and logic issues that must be resolved before
writing any contract code in Phase 2. Addressing these in writing first prevents
the translators from being shaped by the first backend implemented and becoming
coupled to it.

---

## Issue 1 — Target resolution semantics differ fundamentally across backends

### Problem

Each backend resolves action targets in a different way:

- **Crawl4AI** — CSS selectors (`#submit-btn`, `.form input[type=email]`)
- **BrowserOS** — fuzzy text matching (`"Upload CV"`, `"Submit Application"`)
- **Vision motor (OpenCV/OCR)** — image templates, bounding boxes, OCR text regions
  (observation only — the vision motor looks but does not act; it may pair with
  `os_native_tools` or feed coordinates to other backends)

A single `selector_text` field (as in the current `PlaybookAction`) cannot satisfy
all three. The current model is BrowserOS-shaped and will produce an impedance
mismatch the moment Crawl4AI or vision translators are implemented.

### Decision needed

Define a multi-strategy `AriadneTarget` descriptor that carries all resolution
strategies. Each backend uses the field it understands and fails loudly if its
required field is absent.

Proposed shape:

```python
class AriadneTarget(BaseModel):
    css: str | None = None            # crawl4ai
    text: str | None = None           # browseros (fuzzy match)
    image_template: str | None = None # opencv / vision
    ocr_text: str | None = None       # vision fallback
    region: dict | None = None        # vision bounding box hint
```

Portal definitions supply the full descriptor. Translators pick their field.
This is fully deterministic — no runtime inference.

### Gotcha — Target precedence within a single backend

Some backends understand multiple target strategies. For example, BrowserOS can use
both CSS (via Playwright) and fuzzy text (via its snapshot engine). When multiple
fields are populated, the translator must apply a defined precedence order, not
pick arbitrarily. Proposed default:

1. CSS — most deterministic
2. Text — fuzzy match fallback
3. OCR text — vision fallback
4. Image template — visual matching

Each motor's translator should document which fields it supports and in what order.

---

## Issue 2 — Crawl4AI translator is a compiler, not a mapper

### Problem

BrowserOS executes individual tool calls in a step loop. Crawl4AI executes
whole-phase C4A-Scripts — an entire modal-open or form-fill sequence is one
script string. The common language is naturally step-based (matching BrowserOS).

This means the Crawl4AI translator must **compile a list of AriadneSteps into a
single C4A-Script string**, not map steps one-to-one. Conditional steps and
fallbacks become `IF/THEN` blocks in C4A-Script.

### Decision needed

- Explicitly designate the Crawl4AI translator as a step compiler.
- Define the compilation rules: which step types produce which C4A-Script
  constructs, including fallback `IF/ELSE` and observe guard blocks.
- Determine phase boundaries: which steps get compiled into the same `arun()`
  call vs. separate calls (navigate/open, fill, submit are currently three
  separate `arun()` calls in `smart_adapter.py`).

---

## Issue 3 — Backend-specific action tools leak into the common language

### Problem

`evaluate_script_react` in `ActionTool` is a React-specific input workaround
(set native value + dispatch React synthetic event). It exposes the implementation
detail of a specific backend rather than expressing intent.

More generally, any action tool named after a backend mechanism (`evaluate_script_*`,
`take_snapshot`) does not belong in the common language.

### Decision needed

Replace backend-named tools with **intent vocabulary**:

| Current backend tool | Common language intent |
|---|---|
| `evaluate_script_react` | `fill_react_controlled` |
| `take_snapshot` | `observe` |
| `upload_file` | `upload` |

Each translator is responsible for knowing how to execute the intent on its backend.
The common language must never reference how a specific backend achieves an action.

---

## Issue 4 — Recording normalization direction is unresolved

### Problem

BrowserOS agent sessions produce BrowserOS-flavored recordings. Two options exist:

**Option A — Normalize on capture**: convert BrowserOS recordings to common
language immediately when Ariadne stores them. All backends can replay from the
same artifact. Requires a BrowserOS→common translator (inverse direction).

**Option B — Translate at replay time**: store raw BrowserOS recordings in Ariadne,
translate to each backend's format when a replay is requested. Simpler capture
path but each stored artifact remains backend-coupled.

### Decision needed

Choose one option before implementing Ariadne's `recorder.py` and `storage.py`.

Recommendation: **Option A**. Ariadne's value as a backend-neutral source of truth
is only realized if its stored artifacts are in common language. Storing raw
BrowserOS artifacts makes Ariadne a BrowserOS archive, not a neutral map.

Consequence: the BrowserOS agent motor must include a normalization step that
converts its raw session output to common language before handing it to Ariadne.

---

## Issue 5 — Fallback semantics belong in the common language

### Problem

`PlaybookAction.fallback` is a BrowserOS-specific field today. It represents
"if the primary target is not found, try this alternative target/action." This
is a general replay concern, not a BrowserOS concern.

### Decision needed

Move fallback semantics into the common `AriadneAction` model. Translators render
fallbacks in their own terms:

- **BrowserOS**: try alternative text match
- **Crawl4AI**: compile to `IF/ELSE` in C4A-Script
- **Vision motor**: try alternative image template or OCR region
- **OS native tools**: try alternative coordinates (likely fed by vision motor fallback)

---

## Issue 6 — No backend-neutral error taxonomy

### Problem

`BrowserOSObserveError` and `PortalStructureChangedError` are defined in
backend-specific files. The operator CLI and TUI need to react to execution
failures without knowing which backend ran.

### Decision needed

Define a common error taxonomy at the Ariadne level before implementing any
translator:

| Error class | Meaning |
|---|---|
| `ObservationFailed` | Expected elements not present at a step |
| `TargetNotFound` | Specific target element could not be resolved |
| `PortalStructureChanged` | Mandatory structural element absent (drift signal) |
| `ReplayAborted` | Operator or dry-run guard stopped execution |
| `TranslationError` | Common-language step could not be compiled to backend form |

All backend errors must be caught and re-raised as one of these classes.
Higher layers (CLI, TUI) only catch Ariadne errors.

---

## Issue 7 — Vision motor target descriptors must be reserved now

### Problem

The vision motor (OpenCV/OCR) is a separate motor from `os_native_tools`. Vision
looks; os_native acts. They can pair together but neither depends on the other.

The plan defers both to later phases. However, if portals are authored now without
vision target fields, retrofitting `image_template` and `region` hints later will
require reopening every portal definition.

### Decision needed

Reserve vision fields in `AriadneTarget` now (Issue 1 covers this). The vision
translator can be a stub that raises `NotImplementedError`, but the target
descriptor must be complete from the first portal authored.

---

## Issue 8 — `human_required` and `dry_run_stop` must be explicit in the common step model

### Problem

Both fields currently live in `PlaybookStep` (BrowserOS model). They are
cross-backend concerns: any backend replay loop must handle human gates and
dry-run stop points the same way.

### Decision needed

Confirm that both fields belong in the common `AriadneStep` model, not in any
backend-specific step model. Their semantics must be defined at the Ariadne level:

- `human_required`: execution pauses and requests operator confirmation before
  the step's actions run, regardless of backend.
- `dry_run_stop`: execution halts here and returns `ReplayStatus.dry_run` without
  executing actions on this step or any subsequent step.

---

## Recommended resolution order

1. **Issue 1** (target descriptor) — blocks all portal authoring
2. **Issue 6** (error taxonomy) — blocks translator implementation
3. **Issue 3** (intent vocabulary) — defines the common action set
4. **Issues 5 and 8** (fallback + human/dry-run in common model) — complete the step model
5. **Issue 4** (recording direction) — blocks `recorder.py` and `storage.py`
6. **Issue 2** (Crawl4AI compiler) — blocks Crawl4AI translator implementation
7. **Issue 7** (vision fields) — must be done before first portal is authored

Issues 1–5 and 8 should be resolved together as a single "common step model" design
session, producing a draft `ariadne/models.py` skeleton for review before any
translator or portal code is written.
