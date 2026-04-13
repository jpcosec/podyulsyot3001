# CLI Cleanup: Deleting Domain-Specific Logic

**Explanation:** Once the universal CLI is implemented and tested, delete the old, coupled code in `main.py` and cleanup any dead blocks.

**Reference:** `src/automation/main.py`

**Depends on:** `cli-engine-implementation.md`

**Status:** Not started.

### 📦 Required Context Pills
- [Universal CLI Pattern](../context/cli-universal-pattern.md)

### 🚫 Non-Negotiable Constraints
- **Zero-Coupling:** No domain-specific logic (e.g. `apply`, `scrape`) should remain in `main.py`.

**Real fix:**
1. Delete `_build_apply_state()`, `_build_scrape_state()`, `run_apply()`, `run_scrape()`.
2. Delete the dead code block at lines 382–396 (`_ensure_browseros` after `raise`).
3. Ensure no unused imports remain in `main.py`.

**Steps:**
1. Identify all domain-specific functions.
2. Delete them sequentially.
3. Run the universal CLI to verify nothing broke.

**Test command:**
`python -m src.automation.main "easy_apply" --portal linkedin url=https://example.com`
