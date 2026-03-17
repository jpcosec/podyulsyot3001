# AI Module

Current role: LLM boundary and prompt rendering.

## Contains

- `llm_runtime.py`: Gemini runtime wrapper
- `prompt_manager.py`: Jinja-based prompt rendering and validation

## Current status

- LangChain migration is not implemented yet.
- Current implementation still uses custom runtime/prompt manager stack.

## Testing

- Run AI-related tests under `tests/` that cover node logic using AI calls.
