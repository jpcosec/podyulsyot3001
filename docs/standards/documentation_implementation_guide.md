# 💻 Documentation Implementation Guide

This document covers the technical "How-To" for developers—how to implement our active documentation methodology directly in the codebase.

---

## 1. In-Code Comments & Structures

### 1.1 Module & Class Level Docstrings
- **Module Docstrings:** Should reside at the very top of each Python file. They act as executive summaries defining the primary capabilities of the module.
- **Class Docstrings:** Specifically for Abstract Base Classes (ABCs), the docstring must explicitly list all abstract methods that a subclass is required to implement, establishing a clear developer contract.

### 1.2 Dual-Purpose Pydantic Documentation
When defining data schemas (e.g., Pydantic Models for LLM parsing or API outputs), the `Field` descriptions are strict, dual-purpose instructions. They are built for humans to read, but they are also consumed by LLMs.

**Rule:** Ensure descriptions are semantic, provide examples, and—if dealing with multiple languages—supply dual-language examples directly in the prompt.
```python
# ✅ Example of a dual-purpose docstring:
responsibilities: List[str] = Field(
    ...,
    description="List of responsibilities or tasks ('Deine Aufgaben', 'Your Impact')"
)
```

### 1.3 Data Layer Conceptual Distinctions
Class-level comments should clearly delineate requirement boundaries:
- **MANDATORY (The Intersection):** Fields expected across all sources where failure to extract throws a validation error.
- **OPTIONAL (The Union):** Fields that augment or enrich the data payload but might naturally be absent.

---

## 2. Error Contracts & Constraints

### 2.1 Domain-Specific Custom Exceptions
Do not rely on catching generic `Exception` objects for flow control. Modules should explicitly define their failure modes at the top of the file using custom exception classes:
```python
class ToolDependencyError(Exception): pass
class ToolFailureError(Exception): pass
```
- **When to introduce:** Whenever a specific failure state requires a unique recovery path, fallback mechanism, or distinct user intervention.

### 2.2 Catching & Tracking Errors
- **Never swallow errors silently.** If you catch a generic `Exception` to trigger a fallback, you must either log it explicitly or wrap it in a domain-specific error using `from e` to preserve the original stack trace.
- **Observability Contract:** Any caught error that is evaluated must be logged using the explicit `[⚠️]` or `[❌]` tags before recovery is attempted, avoiding hidden failures.

### 2.3 Operational Constraints as `@property` Contracts
Abstract Base Classes should expose operational limits (e.g., API chunk limits, retry delays) as explicit `@property` attributes rather than hiding them deep in logic loops or generic config dicts.
```python
@property
def max_chunk_chars(self) -> int: return 4500
```
This ensures the physical boundaries of the module are self-documented directly on the interface.

---

## 3. Real-Time Observability Logs

Logs are treated as real-time documentation of the execution flow. They must utilize a consistent bracketed emoji pattern to instantly communicate the trace status logic.

**Standard Log Tags:**
- `logger.info("  [⏭️] ...")`: Idempotency tracking (items skipped because they are already processed).
- `logger.info("  [📦] ...")`: Cache hits, loading existing schemas or pre-computed data.
- `logger.info("  [🧠] ...")`: LLM thinking, dynamic generation, or semantic reasoning.
- `logger.info("  [⚡] ...")`: Fast execution, deterministic logic parsing.
- `logger.info("  [🤖] ...")`: Fallback mechanisms intervening (e.g., LLM Rescue after regex failure).
- `logger.info("  [✅] ...")`: Successful validation or process completion.
- `logger.warning("  [⚠️] ...")`: Expected errors or limitations handled (e.g. rate limits hit, triggering retry).
- `logger.error("  [❌] ...")`: Hard failures, validation errors, or bad requests that break the pipeline execution.
