# Contracts

Date: 2026-04-05
Status: design-only (current contracts exist in `src/apply/models.py`, `src/scraper/models.py`,
`src/apply/browseros_models.py`)

## What this folder covers

Contracts are the typed interfaces between system components. Every boundary
where data crosses from one concern to another should have a defined contract.

| Document | Boundary |
|---|---|
| [ariadne.md](ariadne.md) | Ariadne common language ↔ everything else |
| [motor_crawl4ai.md](motor_crawl4ai.md) | Ariadne translator → Crawl4AI executor |
| [motor_browseros_cli.md](motor_browseros_cli.md) | Ariadne translator → BrowserOS CLI executor |
| [motor_browseros_agent.md](motor_browseros_agent.md) | BrowserOS Agent session → recording pipeline |
| [browseros_level2_trace.md](browseros_level2_trace.md) | BrowserOS `/chat` SSE stream → BrowserOS Level 2 trace |
| [motor_human.md](motor_human.md) | Human session → recording pipeline |
| [motor_vision.md](motor_vision.md) | Vision resolver ↔ other motors/translators |
| [motor_os_native.md](motor_os_native.md) | OS native executor ← coordinates + intents |
| [portals.md](portals.md) | Portal definitions → motors and Ariadne |
| [recording.md](recording.md) | Recording pipeline internal contracts |
| [shared.md](shared.md) | Cross-boundary contracts (execution results, job data) |

## Principles

1. **Contracts are Pydantic models.** Validation happens at boundaries, not inside components.
2. **Motors never see each other's contracts.** They see Ariadne common language (via translators)
   or shared contracts. Never import from another motor.
3. **Portals provide data, motors consume it.** A portal never imports motor code.
4. **Ariadne errors are the only errors above the motor layer.** See `plan_docs/ariadne/error_taxonomy.md`.
