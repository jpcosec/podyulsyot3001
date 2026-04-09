# Review UI Bugs and Refactors

**GitHub:** #3, #4, #6, #8, #9

## Goal

Address the smaller bugs, dead code, and misalignments in the `review_ui` and its connection to the LangGraph API.

## Constraints

- Changes must be compatible with the upcoming `hitl_review_screens` redesign.
- Maintain existing `LogTag` and logging conventions.

## Items

1. **`explorer_screen.py` bugs**
   - [ ] **#3 Action refresh fix:** Change `action_refresh` from `async def` to `def` (to match `thread=True`).
   - [ ] **#3 Safe widget access:** Use `self.app.call_from_thread` when touching `self.query_one("#loading").display = True` inside the worker.
   - [ ] **#4 Import fix:** Add `from typing import Dict` to `explorer_screen.py`.

2. **`review_screen.py` and `app.py` cleanup (#6)**
   - [ ] Remove `status_widget = card.query_one(...).previous_sibling` in `_set_match_outcome`.
   - [ ] Remove `except Exception: self.call_later(do_render)` infinite retry loop in `_render_matches` and replace with proper error handling.
   - [ ] Remove unnecessary `compose` override in `MatchReviewApp` (`app.py`).

3. **`hitl_3_content_style` routing (#8)**
   - [ ] Identify where `style_regen` outcome is handled in `graph.py` or equivalent and ensure it routes back to a generation node instead of `END`.

4. **`bus.py` refactor (#9)**
   - [ ] Audit `_REVIEW_STAGE_MAP` and remove legacy aliases like `stage_2_semantic_bridge` if they are no longer in use, or clearly mark them as legacy.
   - [ ] Reuse `self.client` in `MatchBus` methods instead of re-instantiating `LangGraphAPIClient`.
   - [ ] Use a single `asyncio.run()` or shared loop for API calls instead of `asyncio.new_event_loop()` per call.

5. **`README.md` update**
   - [ ] Update keybindings documentation to match actual code (`a` for approve, `q` for quit).

## Steps

1. Fix `explorer_screen.py` imports and `action_refresh`.
2. Clean up `review_screen.py` and `app.py`.
3. Audit and refactor `bus.py`.
4. Update `README.md`.
5. Verify `style_regen` routing in the graph.
6. Run unit tests in `tests/unit/review_ui/`.
