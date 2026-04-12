# ADR: BrowserOS MCP Is The Canonical Scrape Rescue Contract

## Status
Accepted

## Context

The repository originally tracked an issue for BrowserOS agent/schema generation fallback and another for BrowserOS runtime reachability inconsistencies. Since then, the scrape rescue path was implemented through BrowserOS MCP, not BrowserOS `/chat`, and the repo startup/runtime contract was aligned around `http://127.0.0.1:9000`.

BrowserOS `/chat` remains relevant for Level 2 agent capture, but scrape rescue no longer depends on it. Requiring `/chat` health for the basic runtime check created a false blocker for scrape rescue even when MCP was healthy.

## Decision

- Treat BrowserOS MCP at `http://127.0.0.1:9000/mcp` as the canonical required runtime contract for this repository's deterministic BrowserOS integration and scrape rescue path.
- Treat BrowserOS `/chat` as optional for this repository's basic runtime health checks.
- Close the old runtime-mismatch issue and the old schema-generation fallback issue as obsolete under the current architecture.

## Consequences

- `browseros-check` must succeed when MCP is healthy even if `/chat` is unavailable.
- BrowserOS startup docs must describe MCP as required and `/chat` as optional/agent-specific.
- If future work needs selector/schema synthesis from BrowserOS, it should be tracked as a new issue matching the current MCP-first architecture rather than reviving the obsolete schema-generation issue.
