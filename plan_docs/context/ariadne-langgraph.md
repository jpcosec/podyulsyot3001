---
type: decision
domain: architecture
source: docs/adrs/2026-04-12-ariadne-2-0-total-purge.md
---

# Pill: LangGraph Flight Controller

## Decision
Ariadne 2.0 uses LangGraph as its primary "flight controller" for browser automation. The execution flow is a cyclic graph, not a linear script.

## Rationale
Linear scripts break on dynamic SPA portals. LangGraph allows for "observe-execute-evaluate" loops with first-class state persistence (`AsyncSqliteSaver`) and human-in-the-loop breakpoints.

## Trade-offs
- **Complexity:** Higher learning curve than simple Playwright scripts.
- **Overhead:** State persistence adds disk I/O (mitigated by `async`).

## Do not reverse unless
The project moves away from multi-step, cyclic automation (e.g. simple single-page scraping only).
