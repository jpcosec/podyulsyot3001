# Documentation Debt — Unified Automation

Opened: 2026-04-07
Scope: `src/automation/` and associated docs after the AriadneSession orchestrator refactor.

---

## 1. Changelog not updated

`changelog.md` has no entry for the AriadneSession refactor (`feat/unified-automation`).

- [ ] Add `[2026-04-07] — AriadneSession Orchestrator` entry covering:
  - Added `AriadneSession` orchestrator and `MotorProvider`/`MotorSession` protocols
  - Refactored `Crawl4AIApplyProvider` → `C4AIMotorProvider` + `C4AIMotorSession`
  - Refactored `BrowserOSApplyProvider` → `BrowserOSMotorProvider` + `BrowserOSMotorSession`
  - Deleted `registry.py`; inlined motor selection into `main.py`
  - Moved portal map tests out of `motors/` → `tests/unit/automation/portals/`
  - Added AST-based layer boundary guardrail test
  - Fixed pre-existing `navigate()` argument order bug in `BrowserOSReplayer`

---

## 2. `docs/automation/architecture.md` — Stale component map

The component map does not reflect the current architecture.

- [ ] Add `AriadneSession` row: orchestrates the apply loop, loads maps, dispatches to motor — `src/automation/ariadne/session.py`
- [ ] Add `Motor Protocol` row: `MotorProvider` / `MotorSession` contracts between Ariadne and motors — `src/automation/ariadne/motor_protocol.py`
- [ ] Remove any implicit reference to `registry.py` (deleted)
- [ ] Update the architecture narrative to reflect CLI → AriadneSession → MotorProvider → execution

---

## 3. `src/automation/README.md` — Stale "How to Add / Extend"

Step 2 says *"add an adapter in `src/automation/motors/crawl4ai/portals/`"* — that is the old pattern.

- [ ] Replace with the correct pattern:
  1. Create a JSON map in `src/automation/portals/<portal>/maps/easy_apply.json`
  2. Instantiate `AriadneSession(portal_name)` in the CLI
  3. Pick a motor (`C4AIMotorProvider` or `BrowserOSMotorProvider`) and pass it to `session.run(motor, ...)`
- [ ] Add `AriadneSession` to the architecture bullet list

---

## 4. Missing module READMEs

Required by `docs/standards/docs/documentation_and_planning_guide.md`. Each module directory needs a `README.md` with the mandatory sections (🏗️ Architecture, ⚙️ Configuration, 🚀 CLI/Usage, 📝 Data Contract, 🛠️ How to Add/Extend, 💻 How to Use, 🚑 Troubleshooting).

- [ ] `src/automation/ariadne/README.md` — explain the domain layer: models, navigator, session, motor protocol; link to each file
- [ ] `src/automation/motors/README.md` — explain the adapter layer: what a MotorProvider/MotorSession is, how to add a new motor

---

## 5. Inline docstrings — new classes lack full coverage

New classes added in the AriadneSession refactor have module-level and class-level docstrings but some methods lack structured args/return docstrings per the quality checklist.

- [ ] `AriadneSession.run()` — add structured Args/Returns/Raises docstring (currently present but not structured)
- [ ] `C4AIMotorSession.observe()` — args/returns documented; verify complete
- [ ] `C4AIMotorSession.execute_step()` — add Args docstring
- [ ] `BrowserOSMotorSession.observe()` — add Args/Returns
- [ ] `BrowserOSMotorSession.execute_step()` — add Args
- [ ] `BrowserOSReplayer.execute_single_step()` — add Returns (currently `None` but note the `fields_filled` accumulator side-effect)

---

## 6. Known stubs to track

These are functional gaps documented inline with TODOs but should be tracked here:

- [ ] `AriadneSession._build_context` — profile is hardcoded; `--profile-json` CLI flag is parsed but not wired. When `AriadneSession.run()` accepts a `profile` dict, remove the TODO in `main.py` and `session.py`.
- [ ] `BrowserOSReplayer.execute_single_step` — `letter_path` is accepted but not routed to `_execute_action`. Wire it when `UPLOAD_LETTER` intent is defined.
