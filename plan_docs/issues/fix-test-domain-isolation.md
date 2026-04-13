# Fix: test_domain_isolation.py — Delete Dummy Classes

**Explanation:** The bottom half of the file tests dummy classes (`AriadneNode`, `NormalizationEngine`) that do not exist in production code. These tests pass trivially and prove nothing about the real system.

**Reference:** `tests/architecture/test_domain_isolation.py:31–130`

**Status:** Partially working. Lines 1–29 (`test_ariadne_domain_isolation`, `test_executors_are_dumb`) are correct and must be kept. Lines 31–130 are dead weight.

**What is wrong:**
- `AriadneNode` and `NormalizationEngine` are toy classes invented for the test. They have zero relation to `MapRepository`, `AriadneMode`, or any real production module.
- `test_ariadne_requires_map_repository` uses `pyfakefs` to test that a dummy `AriadneNode.run_raw()` raises `FileNotFoundError`. That's testing Python's file system, not our code.
- `test_normalization_blindness` tests a dummy dict-loop class. Not `JsonConfigMode`, not any real mode.

**Fix:**
Delete everything from line 31 to end of file. Keep only:

```python
import pytest
from pytest_archon import archrule

def test_ariadne_domain_isolation():
    (
        archrule("Ariadne Domain Isolation")
        .match("src.automation.ariadne*")
        .should_not_import("src.automation.motors*")
        .should_not_import("requests*")
        .should_not_import("httpx*")
        .check("src.automation")
    )

def test_executors_are_dumb():
    (
        archrule("Dumb Executors")
        .match("src.automation.motors*")
        .should_not_import("src.automation.ariadne.models*")
        .check("src.automation")
    )
```

**Don't:** Replace the dummy classes with other dummies. If you want to test `MapRepository` disk isolation, test the real `MapRepository` with `pyfakefs` in its own unit test under `tests/unit/`.

**Steps:**
1. Delete lines 31–130 from `test_domain_isolation.py`.
2. Run `python -m pytest tests/architecture/test_domain_isolation.py -v` — 2 tests must pass.
3. Confirm no import errors.

### 📦 Required Context Pills
- [DIP Enforcement](../context/dip-enforcement.md)
- [Registry Pattern (DIP-Compliant)](../context/registry-pattern.md)

### 🚫 Non-Negotiable Constraints
- **DIP Enforcement:** Domain layers (`ariadne`) MUST NOT import from infrastructure layers (`motors`). This is the primary invariant being tested.
- **Law 1 (No Blocking I/O):** Do not introduce sync I/O in the test file itself.
