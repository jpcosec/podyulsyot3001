# BrowserOS Agent Motor

**Status: Partial implementation**

This motor is intended to provide agent-driven BrowserOS automation, where an
LLM or policy agent chooses actions at runtime instead of following a fixed
replay path.

The direct BrowserOS `/chat` Level 2 trace client now exists in
`src/automation/motors/browseros/agent/openbrowser.py`, but the Ariadne motor
provider/session integration is still intentionally incomplete.

The first normalization pass from BrowserOS Level 2 tool events into Ariadne-
oriented step candidates now lives in
`src/automation/motors/browseros/agent/normalizer.py`.

## Potential Use Cases

- Recovering from portal drift when a deterministic path no longer matches.
- Exploring unknown apply flows and drafting new Ariadne paths.
- Escalating complex multi-step routing decisions to an agentic browser worker.

## Protocol Compliance

This package currently provides:

- a Level 2 `/chat` trace capture client in `openbrowser.py`
- a conceptual `BrowserOSAgentMotorProvider` and `BrowserOSAgentMotorSession`
  that still raise `NotImplementedError`

That means BrowserOS Level 2 capture is partially implemented, but promotion
into Ariadne paths and full motor-session execution are not finished yet.

## Reference Docs

- `docs/reference/external_libs/browseros/readme.txt`
- `docs/reference/external_libs/browseros/graph_and_hitl.md`
- `docs/reference/external_libs/browseros/deep_findings.md`
- `docs/reference/external_libs/browseros/recording_for_ariadne.md`
