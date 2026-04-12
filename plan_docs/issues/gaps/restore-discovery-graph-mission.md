# Restore: Discovery Graph Mission

**Explanation:** The `scrape` subcommand is currently a stub. To restore job discovery, we need to implement a **Discovery Mission** in the Ariadne graph. This involves re-creating the "Search & Extract" maps for LinkedIn and StepStone.

**Reference:** 
- `src/automation/main.py`
- `plan_docs/ariadne/architecture_and_graph.md`

**What to fix:** Functional `scrape` command that uses the Ariadne graph to navigate search results and extract job listings.

**How to do it:**
1.  Create `src/automation/portals/<portal>/maps/search.json` using the new Graph format.
2.  Update the `scrape` subcommand in `main.py` to initialize the mission with `mission_id='discovery'`.
3.  Implement extraction edges that capture job metadata into the `session_memory`.

**Depends on:** `plan_docs/issues/gaps/implement-mission-driven-pathfinding.md`
