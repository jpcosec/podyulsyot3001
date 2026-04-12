# Implement: LLM Fallback in Default Mode

**Explanation:** According to the Ariadne 2.0 spec (`portals_and_modes.md`), the `DefaultMode` must use LLMs for normalization and interpretation when no portal-specific high-speed rules are available. Currently, it is a no-op stub. This results in poor data quality for unmapped portals.

**Reference:** 
- `src/automation/ariadne/modes/default.py`
- `plan_docs/ariadne/portals_and_modes.md`

**What to fix:** Implement `normalize_job`, `inspect_danger`, and `apply_local_heuristics` in `DefaultMode` using a lightweight LLM (e.g. Gemini 1.5 Flash) with structured output.

**How to do it:**
1.  Initialize a LangChain LLM in `DefaultMode`.
2.  Use Pydantic structured output to extract `JobPosting` data from raw payloads.
3.  Implement a visual/textual prompt for danger detection and heuristic patching.

**Depends on:** none
