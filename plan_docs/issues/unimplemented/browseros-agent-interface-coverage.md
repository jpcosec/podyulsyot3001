# BrowserOS Agent Interface Coverage

## Explanation

The BrowserOS motor currently uses only a narrow subset of the documented BrowserOS interfaces, and the natural-language agent path is not actually wired to a working BrowserOS integration. The code assumes a `/chat` HTTP endpoint that is not available on the live BrowserOS instance.

## Reference in src

- `src/automation/motors/browseros/cli/client.py`
- `src/automation/motors/browseros/cli/replayer.py`
- `src/automation/motors/browseros/agent/openbrowser.py`
- `src/automation/motors/browseros/agent/provider.py`
- `src/automation/ariadne/session.py`
- `docs/reference/external_libs/browseros/readme.txt`

## What to fix

Implement a real BrowserOS agent communication layer and close the highest-value gaps between the documented BrowserOS interfaces and the interfaces we actually use.

## How to do it

1. Replace the broken `/chat` assumption with a documented/verified BrowserOS integration path:
   - MCP-driven BrowserOS UI agent interaction, or
   - BrowserOS graph/agent SDK integration if that path becomes stable.
2. Add a live-tested natural-language prompt flow that can send instructions to the BrowserOS agent, wait for progress, and capture proof artifacts.
3. Expand the BrowserOS MCP client coverage for the missing high-value tools needed by real sessions, especially:
   - `press_key`, `clear`, `focus`, `take_enhanced_snapshot`, `get_dom`, `get_page_content`, `handle_dialog`
4. Audit request schemas against the live BrowserOS version so wrappers like `fill` match the current MCP contract.
5. Add unit and live smoke tests that prove the agent path works end-to-end.
6. Reconcile implementation assumptions with the deeper BrowserOS findings now documented for:
    - `/chat` streaming schema
    - `/chat` tool-call SSE events
    - MCP Session-Id limitations
    - `~/.browseros/sessions/` behavior
    - graph execution behavior
    - extension port `9300`

## Does it depend on another issue?

Yes — `plan_docs/issues/unimplemented/browseros-live-session-validation.md` for broader live validation after the communication layer is in place.
