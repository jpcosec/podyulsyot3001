# Epic 4: Fábrica de Mapas (Grabación Colaborativa)

**Umbrella:** depends on `ariadne-oop-skeleton.md`.

**Objective:** Stop writing portal maps by hand. `Recorder` observes `Theseus`/`Delphi` traces (and passive Chrome DevTools exports) and promotes them into `Labyrinth` rooms + `AriadneThread` edges. Canonical status requires human review.

**Priority:** MEDIUM — enables rapid onboarding of new portals. Does not block Epics 1–3.

**Contains:**
- [ ] `recording-promoter-guard.md` — `Recorder` tags events with `source` and filters LLM events out of canonical edges; `Labyrinth.load_from_db` refuses `status=draft` by default
- [ ] `ariadne-io-layer-and-tests.md` — `Recorder`/`Labyrinth`/`AriadneThread` persistence routes through `src/automation/ariadne/io.py`
- [ ] `map-concept-docs.md` — document the `Labyrinth` (topology) + `AriadneThread` (mission path) split
- [ ] **Task 4.1** — live recording session on XING or LinkedIn
- [ ] **Task 4.2** — run `Recorder.promote()` on the thread and verify the generated `Labyrinth`/`AriadneThread`

### 📦 Required Context Pills
- [DIP Enforcement](../context/dip-enforcement.md)
- [Ariadne Shared I/O Pattern](../context/ariadne-io-pattern.md)
- [Law 1 - No Blocking I/O](../context/law-1-async.md)
- [Law 2 - One Browser Per Mission](../context/law-2-single-browser.md)
- [Ariadne State & Models](../context/ariadne-models.md)
- [Node Implementation Pattern](../context/node-pattern.md)
- [Promotion Pattern (Recording -> Map)](../context/promotion-pattern.md)
- [Graph Recording Pattern](../context/recording-pattern.md)

### 🚫 Non-Negotiable Constraints
- **DIP Enforcement:** `ariadne/` (domain layer) must never import from `motors/` (infrastructure layer). Infrastructure is injected via `config` or resolved through `MotorRegistry`.
- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.
- **Law 2 (One Browser Per Mission):** A single `async with executor` block must wrap the entire graph execution. Nodes must never open or close the browser themselves.
