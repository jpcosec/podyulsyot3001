# 🔧 Basic Code Standards

Universal rules that apply to every module regardless of type. Specialized standards (`llm_langgraph_components.md`, `ingestion_layer.md`, `deterministic_tools.md`) extend these — they do not replace them.

---

## 1. Module Structure

Every module is a self-contained package under `src/<module>/` with a single clear responsibility. Cross-module dependencies go through public contracts (`contracts.py`), never by importing internal implementation files.

Each module exposes its public surface through `__init__.py`. Consumers should not need to import from deep internal paths.

---

## 2. Layer Separation

Regardless of module type, separate these concerns into distinct files:

| File | Owns |
|---|---|
| `contracts.py` | All Pydantic input/output models. The schema boundary. |
| `storage.py` | All file I/O, artifact paths, persistence logic. No business logic. |
| `main.py` | CLI entry point only. No business logic. Delegates to graph/coordinator. |

Additional layers (prompt, graph, coordinator) depend on module type — see the specialized guides.

The rule: **no file does two things.** If a function in `graph.py` is also writing to disk, that write belongs in `storage.py`.

---

## 3. Error Contracts

Define domain-specific exceptions at the top of the file. Never use bare `Exception` for flow control.

```python
class ToolDependencyError(Exception): pass
class ToolFailureError(Exception): pass
```

Never swallow errors silently. If catching a broad exception to trigger a fallback, log with `LogTag.WARN` first, then re-raise with `from e` to preserve the stack trace.

Expose operational limits (chunk sizes, retry budgets, rate limits) as `@property` on ABCs — not buried in loops or config dicts.

---

## 4. Observability

Import `LogTag` from `src/shared/log_tags.py`. Never write emoji tag strings by hand.

```python
from src.shared.log_tags import LogTag

logger.info(f"{LogTag.LLM} Generating match proposal for {job_id}")
logger.warning(f"{LogTag.WARN} Rate limit hit, retrying in {delay}s")
logger.error(f"{LogTag.FAIL} Validation failed: {err}")
```

`LogTag.LLM` is only used on paths that invoke an LLM. `LogTag.FAST` on deterministic paths. Misusing the tags degrades the execution trace.

---

## 5. Pydantic Field Descriptions

`Field(description=...)` is dual-purpose: read by humans and consumed by LLMs. Write it accordingly — semantic, specific, with examples for ambiguous values.

```python
responsibilities: list[str] = Field(
    description="Job responsibilities ('Deine Aufgaben', 'Your Impact'). Extract as short action phrases."
)
```

Mark MANDATORY vs OPTIONAL fields in class-level comments. For LLM-consumed schemas, keep descriptions accurate — stale descriptions cause silent extraction errors.

---

## 6. Docstrings

Every public class, method, and function has a structured docstring: purpose, args, return value. ABCs list all abstract methods in the class docstring.

Module-level docstring at the top of every file: one paragraph, executive summary of what the module does and its role in the system.

---

## 7. CLI Entry Points

Every module that can be run standalone has a `main.py` with a `_build_parser()` function. Arguments are defined there — not duplicated in READMEs.

`main()` accepts an optional `argv: list[str] | None = None` parameter for testability. Returns an integer exit code.

```python
def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    ...
    return 0
```
