---
type: decision
domain: ariadne
source: src/automation/ariadne/config.py
---

# Pill: Gemini Flash Default LLM

## Decision
Ariadne 2.0 uses `gemini-flash-1.5` as its default reasoning engine for the Interpreter and Rescue nodes.

## Rationale
- **Speed:** Sub-second response times are critical for real-time automation.
- **Cost:** Significantly cheaper than Pro/GPT-4 for repetitive map resolution.
- **Multimodal:** Natively handles screenshots with 1M+ context window.

## Trade-offs
- Less reasoning capability than `gemini-pro`.
- Occasional hallucinations in complex mission resolution (mitigated by `with_structured_output`).

## Do not reverse unless
A faster, cheaper multimodal model with `with_structured_output` support becomes available.
