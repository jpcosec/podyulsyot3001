# BrowserOS Agent Motor

**Status: Planned / Conceptual Stub**

This motor is intended to provide agent-driven BrowserOS automation, where an
LLM or policy agent chooses actions at runtime instead of following a fixed
replay path.

## Potential Use Cases

- Recovering from portal drift when a deterministic path no longer matches.
- Exploring unknown apply flows and drafting new Ariadne paths.
- Escalating complex multi-step routing decisions to an agentic browser worker.

## Protocol Compliance

This package currently provides a `BrowserOSAgentMotorProvider` and
`BrowserOSAgentMotorSession` that satisfy the Ariadne motor protocol, but all
execution methods intentionally raise `NotImplementedError`.
