# HITL Review Screens Redesign

**GitHub:** #5, #7  
**Design spec:** `docs/runtime/hitl_review_ui_design.md`  
**Parser (done):** `src/review_ui/document_parser.py`

## Goal

Replace the single-stage `ReviewScreen` with four stage-specific screens covering all
HITL checkpoints, fix the submit bug, and wire the routing in `app.py`.

## Constraints

- Do not modify `MatchBus` interface — screens call existing `load_current_review_surface`
  and `resume_with_review`.
- Do not modify the patch engine (`hitl_patch_engine.py`).
- Each screen is a self-contained `Screen` subclass under `src/review_ui/screens/`.
- Patch serialization rules are in the design spec — follow them exactly.

## Steps

1. **`MatchReviewScreen`** (`screens/match_review_screen.py`)
   - Master-detail layout: left `ListView` index, right detail panel
   - Tracks `_match_outcomes` per `requirement_id`
   - On submit: serializes each outcome to `GraphPatch(action=..., target_id=req_id)`,
     appends sentinel `GraphPatch(action=bulk_action, target_id="__review__")`,
     calls `bus.resume_with_review(action, patches=patches)`
   - Delete `ReviewScreen` once this is wired in

2. **`BlueprintReviewScreen`** (`screens/blueprint_review_screen.py`)
   - Master-detail: left section list, right section detail
   - Local copy of `sections` list; edits are applied in-place
   - `e` key opens `Input` modal for `section_intent`; `x` marks section dropped
   - On submit: one patch `GraphPatch(action="modify", target_id="sections", new_value=[...sections...])`
     plus sentinel

3. **`ContentReviewScreen`** (`screens/content_review_screen.py`)
   - Vim visual mode editor; see design spec for full state machine
   - Uses `parse_bundle()` from `document_parser.py` to load segments
   - Each tab (`cv`/`letter`/`email`) has its own `EditorMode` + `list[LineAnnotation]`
   - Annotation modals: `ModalScreen` subclasses for delete/replace/comment/insert
   - On submit: reconstructs modified markdown per doc from annotations + raw segment
     text, sends one `GraphPatch(action="modify", target_id="cv_full_md"|..., new_value=...)`
     per changed doc, plus sentinel

4. **`ProfileDiffScreen`** (`screens/profile_diff_screen.py`)
   - Read-only diff view; `ProfileUpdateRecord` items rendered with Rich markup
   - Binary approve/reject; sends `GraphPatch(action="approve"|"reject", target_id="__review__")`

5. **`app.py` routing**
   - After `load_current_review_surface`, route on `surface.stage`:
     `hitl_1_*` → `MatchReviewScreen`, `hitl_2_*` → `BlueprintReviewScreen`,
     `hitl_3_*` → `ContentReviewScreen`, `hitl_4_*` → `ProfileDiffScreen`
   - Same routing from `JobExplorerScreen` row selection

## Open questions

- None — design spec is complete.
