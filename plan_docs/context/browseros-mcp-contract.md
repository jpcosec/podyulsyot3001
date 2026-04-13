---
type: decision
domain: scraping
source: plan_docs/design/browseros-adapter-lifecycle.md:5
---

# Pill: BrowserOS MCP Contract

## Decision
BrowserOS remains the canonical rescue interface, but its lifecycle is owned by the BrowserOS adapter itself. The adapter exposes MCP-backed `Sensor`/`Motor` behavior plus `is_healthy()` and async context management.

## Rationale
This keeps `main.py` thin, centralizes startup and health probing, and lets the fast path fail cleanly when the physical browser layer is down.

## Trade-offs
- Adapter implementations become heavier because they own process and network lifecycle.
- Health checks must still respect async runtime rules.

## Do not reverse unless
BrowserOS MCP is replaced or adapter lifecycle ownership moves to another dedicated infrastructure boundary.
