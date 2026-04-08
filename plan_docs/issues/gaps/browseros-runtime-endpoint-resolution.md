# BrowserOS Runtime Endpoint Resolution

**Explanation:** BrowserOS integration still relies on implicit runtime assumptions about which local ports are stable, which endpoint should be used for MCP, and which endpoint should back Level 2 agent capture. Without a single resolution strategy, live behavior can drift across machines or BrowserOS restarts.

**Reference:** `src/automation/motors/browseros/cli/client.py`, `src/automation/motors/browseros/agent/openbrowser.py`, `docs/reference/external_libs/browseros/overview.md`, `docs/reference/external_libs/browseros/deep_findings.md`

**What to fix:** Introduce one canonical BrowserOS runtime configuration policy for this project, including MCP base URL, Level 2 chat base URL, fallback/discovery rules, and error handling for port rotation or provider misconfiguration.

**How to do it:** 1. Add a shared BrowserOS runtime config resolver used by both CLI and agent code. 2. Encode the priority order for `9000` vs discovered backend ports and document it in code. 3. Add explicit handling for startup failure, port rotation, missing provider config, and rate limiting. 4. Add tests for endpoint resolution and fallback behavior.

**Depends on:** none
