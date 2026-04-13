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
- [Ariadne Map Model (Full Schema)](../context/ariadne-map-model.md)
- [Ariadne Shared I/O Pattern](../context/ariadne-io-pattern.md)
- [Graph Recording Pattern](../context/recording-pattern.md)
- [Promotion Pattern (Recording -> Map)](../context/promotion-pattern.md)
- [Node Implementation Pattern](../context/node-pattern.md)

### 🚫 Non-Negotiable Constraints (Laws of Physics)

1. **Law 1 (No Blocking I/O):** All recording and promotion logic MUST be `async`.
2. **DIP Enforcement:** `promotion.py` MUST NOT import from `src/automation/motors/`.
3. **Law 2 (One Browser Per Mission):** Recording MUST capture events from a single browser session.

**Task 4.1: Live Recording Session**
1. Start a graph run with `record_graph: True` in config (already wired in CLI).
2. Navigate manually through XING or LinkedIn easy apply while the recorder listens.
3. Note the `thread_id` printed by the CLI.

```bash
python -m src.automation.main "easy_apply" --portal xing \
  url="https://xing.com/jobs/..." cv_path=./cv.pdf
# Note the thread_id from the output
```

**Task 4.2: Promote the Session**
Run `Recorder.promote()` on the recorded thread:

```python
from src.automation.ariadne.core.actors import Recorder
recorder = Recorder(labyrinth=..., thread=...)
await recorder.promote(thread_id="<thread_id_from_above>")
```

Inspect the resulting `Labyrinth` rooms and `AriadneThread` edges. If variables are templated (`{{email}}`, `{{profile.first_name}}`) and edges derive from deterministic events only, flip `status` from `draft` to `canonical`.

**Validation (real browser required):**

Run the promoted canonical map against the live portal in dry-run mode:

```bash
python -m src.automation.main "easy_apply" --portal xing \
  url="https://xing.com/jobs/..." cv_path=./cv.pdf dry_run=true
```

**Acceptance criteria:**
1. `raw_timeline.jsonl` contains events with `source: "deterministic"` and `source: "llm_agent"` correctly tagged.
2. Promoted `normalized_map.json` contains only edges derived from `"deterministic"` events.
3. All literal profile values in the map are replaced with `{{...}}` templates.
4. Dry-run replay against the live portal completes without HITL (proves the map is valid).
5. `MapRepository` refuses to load the map in a normal run until `status` is manually set to `"canonical"`.
