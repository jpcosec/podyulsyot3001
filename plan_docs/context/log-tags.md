---
type: pattern
domain: architecture
source: src/shared/log_tags.py:1
---

# Pill: Log Tags & Observability

## Pattern
Standardize logs using specific tags to distinguish between deterministic code, LLM reasoning, and human interaction.

## Tag Set
- `[🧠]` **LLM reasoning** (e.g. `[🧠] Resolved 'busca' to 'discovery'`)
- `[⚡]` **Deterministic path** (e.g. `[⚡] Map match for 'easy_apply'`)
- `[🤖]` **Fallback active** (e.g. `[🤖] Cascade level 3: Heuristics failed`)
- `[✅]` **Success/Success state**
- `[⚠️]` **Handled error**
- `[❌]` **Hard failure/Pipeline break**
- `[📍]` **State Pointer** (e.g. `[📍] Current state: job_search`)
- `[🚀]` **Entry Point** (System start)
- `[📦]` **Artifact/Result**

## Implementation
```python
# Use direct print for simplicity in nodes or structured logs if shared utility exists
print(f"[🧠] LLM Resolved intent: {resolution.id}")
print(f"[⚡] Deterministic match for: {instruction}")
```

## When to use
Use in every node and CLI function to maintain consistent execution logs.

## Verify
Verify logs are readable by running a simple mission and checking output.
