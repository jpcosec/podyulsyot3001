# Map Concept: Document That Maps Are State Graphs, Not Traces

**Explanation:** AGENTS.md, README.md, and any onboarding docs must clearly state that an `AriadneMap` is a directed state graph evaluated against a mission — not a linear playbook or recorded trace.

**Reference:** `AGENTS.md`, `README.md`, `STANDARDS.md`

**Status:** Partially wrong. AGENTS.md describes Ariadne's cascade correctly but doesn't explicitly define what a "map" is. New contributors (and agents) arriving from the CLI docs may assume `--portal linkedin` means "play back the linkedin recording".

**Why it matters:** This mental model leak caused the CLI to be designed with `apply` vs `scrape` as separate commands, when both are just the same graph run with different `mission_id`s on the same map. If agents or developers misunderstand this, they'll keep recreating domain-specific wrappers.

**Real fix:**
Add a short "What is a Map?" section to `AGENTS.md` (and/or `STANDARDS.md`) explaining:
- A map is a `StateGraph` defined in JSON: nodes are page states, edges are transitions with intent/target/mission_id.
- The `instruction` (or `mission_id`) selects which edges are eligible — it doesn't pick a different map file.
- Scraping and applying are the same graph execution with different `mission_id` values.
- Maps are authored via the Recording/Promotion pipeline, not written by hand.

**Don't:** Document the map as a "script" or "playbook" — these words imply linearity.

**Steps:**
1. Add "What is a Map?" section to `AGENTS.md`.
2. Optionally add a one-paragraph note in `STANDARDS.md` under the architecture section.
