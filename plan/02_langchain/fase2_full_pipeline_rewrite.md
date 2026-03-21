# Fase 2 - Full Pipeline Rewrite

## Goal

Keep a parking document for a future end-to-end LangChain/LangGraph rewrite, but do not treat it as the current default plan.

## When this phase becomes reasonable

- Only after the hybrid adoption has proven reliable.
- Only if the remaining custom runtime still creates meaningful maintenance drag.
- Only if the benefits are measured, not assumed.

## Possible scope

- Broader LangChain-native prompt execution.
- Shared tracing and model-provider abstraction.
- Deeper runnable composition across LLM nodes.

## Risks

- Regressions in strict contracts.
- Operational retraining cost.
- Larger test and adapter rewrite than phase 1.

## Rule

Freeze this phase unless phase 1 produces strong evidence that a deeper rewrite is worth it.
