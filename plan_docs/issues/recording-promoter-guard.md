# Recorder: Guard Against LLM Events in Canonical Edges

**Umbrella:** depends on `ariadne-oop-skeleton.md`.

**Explanation:** `Recorder.promote()` must only generate canonical `AriadneThread` edges from deterministic `Theseus`/`Motor` events. `Delphi` turns must be stored as observations but never promoted as canonical edges without human review.

**Reference:** `src/automation/ariadne/core/actors.py` (`Recorder`), `src/automation/ariadne/core/cognition.py` (`Labyrinth`, `AriadneThread`)

**Status:** Needs verification. The pipeline exists but it's unclear whether agent events are filtered during edge extraction.

**Why it matters:** If an LLM agent turn (e.g., "I clicked the button because I guessed the selector") gets promoted as a deterministic edge, the next run will try to replay an LLM guess as a scripted action. This creates fragile maps that fail silently on any portal variation.

**Real fix:**
1. `Recorder.__call__` tags every event with `source: "deterministic" | "heuristic" | "llm_agent"`.
2. `Recorder.promote()` only builds canonical `AriadneThread` edges from events with `source == "deterministic"`.
3. LLM agent events are stored as observations on `Labyrinth` rooms for human review, but never become executable edges.
4. `Labyrinth.load_from_db()` refuses to load a `status="draft"` snapshot in production runs unless `--allow-draft` is passed.

**Don't:** Promote any LLM-generated action as a deterministic edge without human review.

**Steps:**
1. Add `source` field to `GraphRecorder` event schema.
2. Update `AriadnePromoter` to filter on `source == "deterministic"`.
3. Add `status` guard to `MapRepository.get_map()`.
4. Test: record a session with mixed deterministic + LLM events, assert promoted map contains only deterministic edges.
