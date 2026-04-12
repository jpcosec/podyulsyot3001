# Implement: Promotion Engine

**Explanation:** Once a recording exists, it must be converted into a valid `AriadneMap` candidate. This is the "Promotion" phase. It involves deduplicating nodes, identifying bidirectional edges, and templating literals (like names) into `{{profile.first_name}}` placeholders.

**Reference:** 
- `plan_docs/ariadne/recording_and_promotion.md`
- `src/automation/ariadne/models.py`

**What to fix:** A utility that processes JSONL traces into production-ready `AriadneMap` JSON files.

**How to do it:**
1.  Implement the `AriadnePromoter` utility.
2.  Add logic to detect unique states based on their `presence_predicate`.
3.  Add logic to perform placeholder substitution on captured `fill` and `upload` actions.
4.  Generate the final `states` and `edges` graph structure.

**Depends on:** `plan_docs/issues/gaps/implement-graph-recorder-capability.md`
