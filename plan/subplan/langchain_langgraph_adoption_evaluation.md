# LangChain + LangGraph Adoption Evaluation

Date: 2026-03-12

## Purpose

Evaluate, with explicit criteria and experiments, whether PhD 2.0 should move from custom AI plumbing to a LangChain-based runtime while preserving current LangGraph orchestration and deterministic HITL guarantees.

## Current State

What exists today:

1. Graph orchestration already uses LangGraph (`src/graph.py`).
2. Prompt rendering is custom (`src/ai/prompt_manager.py`) with strict Jinja + XML-tag validation.
3. Model runtime is custom Gemini wrapper (`src/ai/llm_runtime.py`) with strict Pydantic validation.

Main concern:

- We are carrying custom abstractions that may grow into framework debt if they diverge from ecosystem standards.

## Decision Options

## Option A - Keep Current Custom AI Layer

Description:

- Keep `PromptManager` + `LLMRuntime` as primary runtime API.

Pros:

1. Full control of fail-closed semantics.
2. Minimal migration risk.
3. No immediate refactor cost.

Cons:

1. Ongoing maintenance of custom adapters.
2. Fewer plug-and-play integrations (tracing, guardrails, model providers).

## Option B - Hybrid Adoption (Recommended Default)

Description:

- Keep LangGraph topology and deterministic node boundaries.
- Replace selective internals with LangChain components where beneficial (model wrappers, output parser utilities, tracing hooks).
- Preserve existing prompt files and review/data-plane contracts.

Pros:

1. Low-risk incremental migration.
2. Reduces custom runtime surface.
3. Keeps deterministic governance intact.

Cons:

1. Temporary mixed stack complexity.
2. Requires explicit adapter boundaries to avoid confusion.

## Option C - Full LangChain Runtime Rewrite

Description:

- Move prompts, model calls, and parsers to LangChain-native runnable abstractions across LLM nodes.

Pros:

1. Max ecosystem alignment.
2. Strong standardization potential.

Cons:

1. High migration risk.
2. Potential drift from current strict contracts and deterministic safeguards.
3. Larger test rewrite and operational retraining.

## Non-Negotiable Constraints

Any option must preserve:

1. Fail-closed behavior at every review gate.
2. Data-plane artifact contract ownership on disk.
3. Control-plane state minimalism (`GraphState` carries routing, not payloads).
4. Deterministic stale-hash validation and explicit `approve/request_regeneration/reject` routing.

## Evaluation Criteria

Score each option 1-5 across:

1. Deterministic safety compatibility.
2. Migration complexity.
3. Observability and debugging support.
4. Long-term maintainability.
5. Multi-model/provider portability.
6. Team cognitive load.

## Required Spikes (Before Decision)

## Spike 1 - Structured Output Reliability

Goal:

- Compare schema-valid output success rates between current `LLMRuntime` and LangChain-based Gemini invocation on `extract_understand` and `match`.

Measure:

- Validation pass rate, retries needed, and error clarity.

## Spike 2 - Prompt Discipline Compatibility

Goal:

- Verify if existing node-local prompt files (`system.md`, `user_template.md`) can remain unchanged under LangChain integration.

Measure:

- Zero required prompt-format rewrites for baseline nodes.

## Spike 3 - Failure Taxonomy Mapping

Goal:

- Map LangChain exceptions to existing `ErrorContext` categories without introducing ambiguous error classes.

Measure:

- Deterministic one-to-one error mapping table and test coverage.

## Spike 4 - Resume and HITL Integrity

Goal:

- Confirm no regression in `run_prep_match --resume` semantics when LLM layer is swapped behind adapters.

Measure:

- Same review-loop behavior and same stale-hash protections under resume.

## Decision Gate

Proceed to broader migration only if all are true:

1. No fail-closed regression in automated tests.
2. No additional ambiguity in review routing behavior.
3. At least neutral runtime reliability versus current custom layer.
4. Clear net reduction in custom maintenance burden.

## Recommended Path

1. Execute Option B (hybrid) first.
2. Re-evaluate Option C after deterministic parity migration is complete.
3. Freeze full-runtime rewrite unless spikes show clear, measured benefit.

## Deliverables from This Evaluation

1. Decision memo with option scorecard.
2. Spike result report with reproducible commands.
3. ADR (architecture decision record) for accepted path.
4. Incremental migration backlog (if Option B or C is approved).
