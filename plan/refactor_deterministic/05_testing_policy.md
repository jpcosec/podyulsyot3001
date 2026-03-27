# 05 - Testing Policy

## Policy
- Keep and run deterministic tests only.
- Remove or rewrite tests tied to removed nondeterministic legacy behavior.
- Add new deterministic tests only for newly implemented rebuild steps.

## Fixtures
- Use `data/Archived/` as behavior reference fixtures.

## Gate
- No step advances unless deterministic tests are green.
