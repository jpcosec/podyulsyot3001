# generate_documents_v2: module-level `_DATA_MANAGER` singleton in `profile_loader.py`

**Why deferred:** The current behaviour works when the process runs from the project root, which is the normal case. The fix is low-risk but touches the public API of `load_profile_kg` and `load_section_mapping`.
**Last reviewed:** 2026-03-31

## Problem

`src/core/ai/generate_documents_v2/profile_loader.py` line 15 instantiates a `DataManager` at import time:

```python
_DATA_MANAGER = DataManager()
```

`DataManager()` with no arguments resolves its root from `os.getcwd()` at the moment of import. This creates two problems:

1. **Import-time side effect:** The path is frozen when the module is first imported, not when the function is called. Tests that change directory or use `tmp_path` after import get the wrong root.
2. **Inconsistency:** Every other use of `DataManager` in this codebase passes an explicit root. The profile loader is the only module that relies on implicit CWD resolution.

The `DataManager` here adds no real value — `load_profile_kg` and `load_section_mapping` both receive a full `Path` as their argument. The only use of `_DATA_MANAGER` is to call `read_json_path(path)`, which is equivalent to `json.loads(path.read_text(encoding="utf-8"))`.

## Proposed Direction

Remove `_DATA_MANAGER` entirely. Replace all `_DATA_MANAGER.read_json_path(p)` calls with `json.loads(p.read_text(encoding="utf-8"))` directly, as the original plan specified. No interface change required.

## Linked TODOs

- `src/core/ai/generate_documents_v2/profile_loader.py:15` — `# TODO(future): module-level singleton locks path at import time — see future_docs/issues/generate_documents_v2_profile_loader_singleton.md`
