# Translator CLI Preprocessing: Remaining Cleanup After Graph Move

**Why deferred:** The major translation move landed, but some older planning assumptions targeted removed graph paths and still need cleanup rather than new feature work.
**Last reviewed:** 2026-04-03

## Problem / Motivation

Translation pre-processing now happens in the CLI path, but the older planning material also bundled unrelated graph-path cleanup that no longer maps cleanly to the current codebase.

This leaves follow-up cleanup items such as:

- removing stale docs that reference deleted graph paths
- confirming there are no remaining silent failure patterns in the current pipeline path
- keeping translator/runtime responsibilities clear after the shift to CLI preprocessing

## Proposed Direction

- treat remaining work as cleanup issues, not as continuation of the old plan document
- create targeted issue docs per real unresolved problem if new concrete failures are found

## Related code

- `src/cli/main.py`
- `src/core/tools/translator/main.py`
