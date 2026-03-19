# LangChain Runtime Migration Plan

## Purpose

Define a safe migration path from the current custom Gemini-specific AI runtime to a LangChain-based runtime, while preserving the existing LangGraph orchestration, deterministic review gates, and filesystem-centered artifact contracts.

This document focuses on migration logic and rationale, not implementation details.

## Executive Decision

The recommended path is:

- keep LangGraph as the workflow/orchestration layer
- migrate the LLM runtime layer to LangChain incrementally
- preserve the current prompt files and node boundaries
- preserve fail-closed validation and deterministic review semantics

This is intentionally not a full framework rewrite.

## Why This Migration Exists

The current LLM layer is tightly coupled to Gemini-specific behavior.

Current characteristics:

- a custom `LLMRuntime` wrapper is responsible for model invocation
- the runtime directly imports the Google Gemini SDK
- node logic refers to `PHD2_GEMINI_MODEL`
- structured output behavior depends on Gemini request semantics
- tests implicitly encode Gemini as the provider baseline

This creates several problems:

- provider portability is weak
- switching from Gemini to another model family such as Qwen is harder than it should be
- custom runtime maintenance cost will grow over time
- the current abstraction duplicates capabilities available in LangChain
- tracing, provider portability, and ecosystem alignment remain limited

## Why Not Rewrite Everything

The repository already has a working control plane based on LangGraph.

What already works and should not be destabilized unnecessarily:

- graph topology
- checkpointing and resume behavior
- thread identity rules
- interrupt-before review gates
- deterministic route transitions
- on-disk review and artifact contracts

The current weakness is not orchestration. The weakness is the AI/provider layer.

A full rewrite would mix two very different concerns:

- control-plane orchestration
- model-provider integration

Those should be migrated separately.

## Recommended Migration Principle

Migrate the provider layer, not the whole system at once.

More specifically:

1. Keep LangGraph.
2. Replace the custom model runtime with a provider-agnostic LangChain-backed runtime.
3. Preserve current prompts and node contracts during the migration.
4. Re-evaluate deeper LangChain adoption only after runtime parity is proven.

## Strategic Reasoning

### 1. LangGraph Is Already The Stable Part

The repo already depends on LangGraph for:

- state graph construction
- checkpoint persistence
- resume semantics
- review-gate interruption
- conditional routing

That means the system already has framework alignment on orchestration.

Replacing this now provides limited benefit and meaningful risk.

### 2. The Custom AI Layer Is The Actual Migration Target

The custom AI layer is currently responsible for:

- prompt loading/rendering
- provider-specific model invocation
- structured output validation behavior

This is where the current provider lock-in lives.

Migrating this layer gives the highest payoff:

- multi-provider flexibility
- easier model substitution
- less custom glue code
- better compatibility with tracing and evaluation tooling

### 3. Provider Migration Should Not Break Deterministic Governance

The repo depends on several strict guarantees:

- fail-closed node behavior
- explicit review routing
- stale-artifact protection
- minimal control-plane state
- disk-first artifact ownership

A LangChain migration is only acceptable if those guarantees remain intact.

That means LangChain should be used as an internal runtime mechanism, not as a reason to weaken the node contracts.

### 4. Prompts Are Already A Useful Stable Interface

The existing prompt discipline has value:

- node-local `system.md`
- node-local `user_template.md`
- explicit prompt rendering rules
- XML-tag validation conventions

There is no strong reason to rewrite prompt assets just because model invocation changes.

The prompt files should remain stable through the migration wherever possible.

### 5. Provider-Agnostic JSON Validation Is Safer Than Provider-Native Schema Features

The current runtime leans on Gemini-specific structured output features.

That is one source of lock-in.

The safer long-term approach is:

- request JSON output from the model
- parse and validate locally
- keep Pydantic or equivalent schema validation as the final gate

This reduces provider-specific assumptions and makes Qwen-class migration much easier.

## Non-Negotiable Constraints

The migration must preserve:

1. LangGraph checkpoint/resume behavior.
2. Existing review-gate routing semantics.
3. Fail-closed parsing and validation.
4. Filesystem-first artifact ownership.
5. Minimal `GraphState` control metadata design.
6. Node-local prompt discipline unless there is measured reason to change it.

## Target End State

The desired end state is:

- LangGraph remains the control-plane framework.
- LangChain backs the provider/model invocation layer.
- The runtime becomes provider-agnostic.
- The provider and model are chosen through configuration, not hardcoded Gemini naming.
- Node code no longer refers directly to Gemini-specific runtime assumptions.
- Structured outputs are validated locally and deterministically.

## Migration Shape

### Phase 1. Clarify The Runtime Boundary

Establish a clear conceptual boundary between:

- prompt preparation
- model invocation
- response parsing/validation
- node orchestration

This is necessary because the current implementation mixes “LLM runtime” with provider-specific Gemini semantics.

Outcome:

- a clearly defined runtime contract that nodes depend on
- no assumption that the runtime is Gemini-specific

### Phase 2. Introduce Provider-Agnostic Runtime Semantics

Define runtime behavior in provider-neutral terms:

- provider name
- model name
- request payload
- expected output mode
- local validation path
- runtime errors mapped to stable categories

The key shift is conceptual:

- runtime behavior should describe what the node needs
- not how Gemini happens to provide it

Outcome:

- a stable runtime contract that can be implemented by multiple providers

### Phase 3. Preserve Prompt Assets While Swapping Invocation Mechanics

Retain the current prompt structure:

- `system.md`
- `user_template.md`
- node-local prompt ownership

The migration should avoid rewriting prompts unless a concrete incompatibility is discovered.

Outcome:

- the migration remains operationally narrow
- prompt churn does not contaminate provider migration

### Phase 4. Replace Gemini-Native Structured Output Dependence

Move toward a provider-neutral structured-output strategy:

- ask the model for JSON
- perform deterministic local validation afterward

This matters because provider-native schema enforcement is not guaranteed to behave the same across Gemini, Qwen, OpenAI-compatible models, or local serving stacks.

Outcome:

- structured output reliability is governed by local validation
- portability improves substantially

### Phase 5. Migrate One LLM Node First

Do not migrate all LLM nodes simultaneously.

Use one node as the proving ground for:

- provider-neutral invocation
- prompt compatibility
- output validation behavior
- error mapping
- test parity

The first migrated node should be chosen for narrow scope and high observability.

Outcome:

- a low-risk experimental slice
- evidence for whether the migration strategy is working

### Phase 6. Compare Reliability Against Current Runtime

For the migrated node, compare:

- schema validation pass rate
- error clarity
- output consistency
- operational complexity
- retry burden if any

Migration should proceed only if the new path is at least neutral, and ideally better.

Outcome:

- decision based on measured runtime behavior, not framework preference

### Phase 7. Expand To Remaining LLM Nodes

Only after one-node parity is established should the migration expand to:

- extraction
- matching
- document generation
- later review-assist or synthesis nodes

Each node should keep:

- the same input contract
- the same output contract
- the same artifact expectations

Outcome:

- provider/runtime migration without destabilizing workflow behavior

### Phase 8. Remove Gemini-Specific Configuration Naming

Replace Gemini-specific configuration concepts with generic runtime configuration.

Examples of what should change conceptually:

- provider selection becomes explicit
- model naming becomes provider-neutral
- provider-specific credentials are separated from generic runtime config

Outcome:

- configuration reflects actual architecture instead of current provider history

### Phase 9. Add Optional LangChain Ecosystem Features Only After Parity

After runtime parity is established, consider optional LangChain benefits such as:

- tracing
- evaluations
- provider adapters
- structured middleware hooks

These should be added only after the core migration is stable.

Outcome:

- ecosystem benefits without confusing the primary migration goal

## Why This Is Better Than “LangChain Only”

A blanket “LangChain only” direction is too vague and risks collapsing distinct concerns into one migration.

What it gets wrong:

- it treats orchestration and model invocation as the same problem
- it invites unnecessary prompt rewrites
- it increases the chance of regressions in resume and review behavior
- it creates migration churn where the current system is already stable

What the recommended approach gets right:

- it targets the real source of provider lock-in
- it preserves the working control plane
- it narrows the migration blast radius
- it makes provider switching easier without rewriting the project’s governance model

## Why This Is Better For Qwen Support

Qwen support becomes easier if the system stops depending on Gemini-native request semantics.

A provider-agnostic LangChain-backed runtime helps because:

- the invocation layer becomes configurable
- the model name stops implying the provider
- the same node can target different backends
- local JSON validation can stay constant even if providers differ

The key advantage is not “LangChain magic.” The key advantage is that LangChain gives a common provider-facing abstraction while local validation preserves deterministic control.

## Risks

### Risk 1. Hidden Gemini Assumptions In Tests

Current tests encode Gemini naming and assumptions.

Mitigation:

- shift tests toward contract behavior and output validation rather than provider identity

### Risk 2. LangChain Abstraction Leakage

If LangChain primitives leak directly into node logic, the node layer may become harder to reason about.

Mitigation:

- keep LangChain behind a narrow internal runtime boundary

### Risk 3. Structured Output Reliability Regression

Provider-neutral JSON generation may initially be less strict than Gemini-native schema support.

Mitigation:

- rely on deterministic local validation
- compare one-node parity before full rollout

### Risk 4. Migration Scope Expansion

A runtime migration can easily turn into a broader architecture rewrite.

Mitigation:

- explicitly exclude orchestration rewrites from the migration scope
- preserve node contracts and artifact contracts during the transition

## Acceptance Criteria

The migration should be considered successful when:

- LangGraph orchestration remains stable and unchanged in its essential behavior
- the LLM runtime is no longer Gemini-specific
- provider selection is configuration-driven
- at least one non-Gemini provider can be supported through the same runtime contract
- node prompt files remain usable without broad rewrites
- node output validation remains fail-closed
- tests assert runtime behavior rather than Gemini-specific naming

## End State Summary

The desired architecture is:

- LangGraph for workflow control
- LangChain for provider/model integration
- local deterministic validation for structured outputs
- filesystem-first artifact ownership unchanged
- provider flexibility improved without sacrificing review governance

This path is recommended because it addresses the real source of rigidity in the current system while preserving the parts of the system that already work well.
