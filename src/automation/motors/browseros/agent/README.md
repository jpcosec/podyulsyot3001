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

Deterministic candidate promotion into a draft replay path now lives in
`src/automation/motors/browseros/agent/promoter.py`.

Failed Level 2 discovery attempts now persist both:

- the raw BrowserOS `/chat` trace
- normalized Level 2 step candidates

for later promotion into Ariadne paths.

## Potential Use Cases

- Recovering from portal drift when a deterministic path no longer matches.
- Exploring unknown apply flows and drafting new Ariadne paths.
- Escalating complex multi-step routing decisions to an agentic browser worker.

## Protocol Compliance

This package currently provides:

- a Level 2 `/chat` trace capture client in `openbrowser.py`
- a partially wired `BrowserOSAgentMotorProvider` and `BrowserOSAgentMotorSession`
  that can delegate Level 2 capture/discovery into the working client
  but still do not implement deterministic `execute_step()` motor behavior

That means BrowserOS Level 2 capture and draft-path promotion are implemented,
but full motor-session execution through the conceptual provider is not finished yet.

## Reference Docs

- `docs/reference/external_libs/browseros/readme.txt`
- `docs/reference/external_libs/browseros/graph_and_hitl.md`
- `docs/reference/external_libs/browseros/deep_findings.md`
- `docs/reference/external_libs/browseros/recording_for_ariadne.md`
