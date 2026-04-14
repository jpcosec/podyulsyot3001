# Task: Delphi full LLM implementation

## Explanation
`DelphiNode` is a stub. It increments the circuit breaker counter and appends an error, but performs no actual LLM reasoning. The cold path — triggered when Theseus cannot identify a room or the Thread has no step — is completely non-functional.

## Reference
- `src/automation/langgraph/nodes/delphi.py` — current stub, `MAX_FAILURES = 5`
- `docs/automation/architecture.md` — cold path description, Delphi responsibilities
- BrowserOS MCP endpoint: `http://localhost:9100` (Delphi connects here for visual reasoning)
- Port map in `plan_docs/design/browseros-adapter-lifecycle.md`

## What to fix
Implement the Delphi cold path:
1. Receive `snapshot` (HTML + optional screenshot) from `AriadneState`
2. Build a prompt that includes: raw HTML, screenshot (if available), known `current_room_id` (if any), and `labyrinth.known_dead_ends()`
3. Call LLM via BrowserOS MCP (port 9100) or directly via `google-generativeai`
4. Parse response: extract proposed `MotorCommand` to execute
5. Execute via `Motor.act()` and return updated state patches
6. Increment `agent_failures` on any failure; trigger HITL path when `agent_failures >= MAX_FAILURES`

## How to do it
- Inject `Motor` and `Labyrinth` into `DelphiNode` constructor (same pattern as `TheseusNode`)
- Inject an `LLMClient` protocol (define in `contracts/`) or use the BrowserOS MCP tool call directly
- Keep prompt construction in a private helper (`_build_prompt`) to stay under the 10-line function limit
- The HITL path for now can be a special error string in `state["errors"]` that the router can detect

## Depends on
- Task 01 (`is_mission_complete`) — routing must be in place so Delphi exits correctly on success
- BrowserOS running at port 9100
