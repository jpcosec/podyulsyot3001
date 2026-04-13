# Recording/Promotion: Guard Against LLM Events in Map Edges

**Explanation:** `AriadnePromoter` must only generate map edges from deterministic execution events. LLM rescue agent turns must be skipped or flagged as `"draft_hint"` — never promoted as canonical edges.

**Reference:** `src/automation/ariadne/capabilities/recording.py`, `src/automation/ariadne/capabilities/promotion.py`

**Status:** Needs verification. The pipeline exists but it's unclear whether agent events are filtered during edge extraction.

**Why it matters:** If an LLM agent turn (e.g., "I clicked the button because I guessed the selector") gets promoted as a deterministic edge, the next run will try to replay an LLM guess as a scripted action. This creates fragile maps that fail silently on any portal variation.

**Real fix:**
1. `GraphRecorder` must tag every event with `source: "deterministic" | "heuristic" | "llm_agent"`.
2. `AriadnePromoter.promote_thread()` must only build `AriadneEdge` objects from events with `source == "deterministic"`.
3. LLM agent events can be stored as `"observations"` in the draft map for human review, but must not become executable edges.
4. Add a guard: if `status == "draft"`, the `MapRepository` must refuse to load the map in production runs unless `--allow-draft` flag is passed.

**Don't:** Promote any LLM-generated action as a deterministic edge without human review.

**Steps:**
1. Add `source` field to `GraphRecorder` event schema.
2. Update `AriadnePromoter` to filter on `source == "deterministic"`.
3. Add `status` guard to `MapRepository.get_map()`.
4. Test: record a session with mixed deterministic + LLM events, assert promoted map contains only deterministic edges.
