# Core Module

Current role: deterministic runtime and contracts.

## Contains

- Graph state and control-plane types
- Deterministic tools (scraping, translation, rendering helpers)
- Round management and deterministic review support

## Current status

- Core I/O centralization (`src/core/io/`) is not implemented yet.
- Existing code still uses inline path construction in several node flows.

## Testing

- Run core tests under `tests/core/`.
