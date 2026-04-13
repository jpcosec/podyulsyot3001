# Epic 4: Fábrica de Mapas (Grabación Colaborativa)

**Objective:** Stop writing portal maps by hand. Use the recording pipeline to auto-generate `draft` maps from a live browser session, then promote them to canonical.

**Priority:** MEDIUM — enables rapid onboarding of new portals. Does not block Epics 1–3.

**Contains:**
- [ ] `recording-promoter-guard.md` — add `source` tag to `GraphRecorder` events; filter LLM events from `AriadnePromoter` edge extraction; add `status="draft"` guard to `MapRepository`
- [ ] `map-concept-docs.md` — update `AGENTS.md` and `STANDARDS.md` to define maps as state graphs, not traces; close the epic with correct documentation
- [ ] **Task 4.1** — run a live recording session on XING or LinkedIn (see steps below)
- [ ] **Task 4.2** — run `AriadnePromoter` on the recorded session and verify the output map

### 📦 Required Context Pills
- [Ariadne Map Model (Full Schema)](../context/ariadne-map-model.md)
- [Graph Recording Pattern](../context/recording-pattern.md)
- [Promotion Pattern (Recording -> Map)](../context/promotion-pattern.md)
- [Node Implementation Pattern](../context/node-pattern.md)

### 🚫 Non-Negotiable Constraints (Laws of Physics)

1. **Law 1 (No Blocking I/O):** All recording and promotion logic MUST be `async`.
2. **DIP Enforcement:** `promotion.py` MUST NOT import from `src/automation/motors/`.
3. **Law 2 (One Browser Per Mission):** Recording MUST capture events from a single browser session.

**Note:** `promotion.py` does not exist yet.

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
Run `AriadnePromoter` on the recorded thread:

```python
from src.automation.ariadne.capabilities.promotion import AriadnePromoter
promoter = AriadnePromoter()
draft_map = promoter.promote_thread(thread_id="<thread_id_from_above>")
print(draft_map.model_dump_json(indent=2))
```

Review the output. If edges look correct and variables are substituted (`{{email}}`, `{{profile.first_name}}`), move the file to `src/automation/portals/xing/maps/easy_apply.json` and set `status="canonical"`.

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
