# Review UI Wiring

**Why deferred:** The TUI exists and works in isolation but its integration contract with `match_skill` is undocumented and unverified end-to-end.
**Last reviewed:** 2026-03-29

## Problem / Motivation

`src/review_ui/` is a full Textual TUI module (`app.py`, `bus.py`, `screens/`, `widgets/`) with no runtime documentation and no coverage in `docs/runtime/`. The `MatchBus` in `bus.py` is the critical wiring point — it connects the TUI to the paused LangGraph thread and the `MatchArtifactStore` — but its contract (what state it expects, what `Command` it sends back, what disk layout it assumes) is not documented anywhere. It is unclear whether the TUI is fully wired to the current graph structure or carries assumptions from an earlier iteration.

## Proposed Direction

- Document `MatchBus` contract: what it loads, what resume `Command` shape it emits, and what artifact paths it reads.
- Verify end-to-end: `run_match_skill` → graph pauses → `review_tui` launches → TUI loads review surface → decision → graph resumes.
- Add a module doc at `src/review_ui/README.md` covering the interaction model.
- Add an integration test covering the TUI→graph resume path (can use `InMemorySaver` and a mock `MatchBus`).

## Linked TODOs

- `src/review_ui/bus.py` — `# TODO(future): document MatchBus contract and verify against current graph state — see future_docs/issues/review_ui_wiring.md`
- `src/review_ui/app.py` — `# TODO(future): verify TUI wiring against current match_skill graph structure — see future_docs/issues/review_ui_wiring.md`
