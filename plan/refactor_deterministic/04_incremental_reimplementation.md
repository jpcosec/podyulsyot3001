# 04 - Incremental Reimplementation

## Sequence
1. Scrape + translate deterministic path.
2. Extraction redesign.
3. Matching redesign.
4. Review redesign with modern LangGraph/LangChain HITL.
5. Document generation redesign.
6. Render/package finalize.

## Rules
- Implement one node family at a time.
- Validate deterministic tests before next step.
- Update next-steps tracker after each completed step.

## Exit Criteria
- Every completed family has passing deterministic tests.
