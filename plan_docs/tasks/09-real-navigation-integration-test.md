# Task 09: Real navigation integration test — live BrowserOS session with persisted output

## Explanation
All prior tests are unit tests with mocks or fake data. This task runs the actual LangGraph
loop against a live BrowserOS instance, navigates a real site (emol.com), and verifies that
real files are written to `data/portals/`.

The goal: after the run, the user can open and inspect:
- `data/portals/emol.com/labyrinth.json` — rooms discovered from real URLs
- `data/portals/emol.com/threads/{mission_id}.json` — transitions recorded from real actions

## What to do
1. Start BrowserOS (already running at port 9101/9200)
2. Run the graph via `main.py` or a one-off script against emol.com
3. Let Observe derive `domain = "emol.com"` from the live URL
4. Let Delphi navigate a few pages (Theseus fast-path will be empty on first run)
5. Let Recorder persist Labyrinth + Thread to disk after each step
6. Print the paths of written files and their contents at the end

## Success criteria
- `data/portals/emol.com/labyrinth.json` exists and contains at least one room
- `data/portals/emol.com/threads/*.json` exists and contains at least one transition
- Both files are valid JSON readable by `Labyrinth.load()` and `AriadneThread.load()`

## Depends on
- Task 06 (domain-aware PortalRegistry) ✓
- Task 07 (LLM schema discovery — so extraction works without pre-defined schema)
- Task 08 (session resume — optional but nice for follow-up runs)
- BrowserOS running at localhost:9101/9200
