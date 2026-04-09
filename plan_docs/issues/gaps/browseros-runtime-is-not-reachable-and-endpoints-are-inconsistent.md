# BrowserOS Runtime Is Not Reachable And Endpoints Are Inconsistent

**Explanation:** The BrowserOS-based fallback cannot be implemented or validated until the local BrowserOS runtime is reachable. The repository currently has an endpoint/config mismatch:
1. `docs/automation/browseros_setup.md` documents BrowserOS on port `9200`.
2. `src/automation/motors/browseros/runtime.py` resolves the runtime front door to `http://127.0.0.1:9000`, with MCP at `/mcp` and chat at `/chat`.
3. Live checks from this environment return connection refused for both `127.0.0.1:9000` and `localhost:9200`.

Until the runtime contract is clarified and the service is actually reachable, issue 3 cannot be validated on real BrowserOS sessions.

**Reference:**
- `docs/automation/browseros_setup.md`
- `src/automation/motors/browseros/runtime.py`
- `src/automation/motors/browseros/cli/client.py`

**What to fix:** Define one canonical BrowserOS runtime contract for this repo, make the docs and code agree on it, and verify that the local runtime is reachable at the expected MCP endpoint before any BrowserOS fallback work proceeds.

**How to do it:**
1. Decide whether the canonical BrowserOS front door is `:9000` or `:9200`.
2. Update docs and runtime resolution so they agree.
3. Add a simple repo-level verification step that checks `/health`, `/mcp`, and `/chat` on the canonical base URL.
4. Confirm a real `BrowserOSClient.initialize()` succeeds from this repo.

**Depends on:** none
