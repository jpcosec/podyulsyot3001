# CV Generator Cleanup & Refactoring Plan

**Date**: 2026-03-02  
**Context**: After completing the 10-phase pipeline redesign, the `src/cv_generator/` module is partially migrated. This plan finalizes the cleanup.

---

## Problem Statement

After the pipeline redesign (phases 1-10), the step modules import from `src/cv_generator/`:
- `src/steps/matching.py` imports `MatchProposalPipeline`, `parse_reviewed_proposal` from `cv_generator.pipeline`
- `src/steps/cv_tailoring.py` imports `CVTailoringPipeline` from `cv_generator.pipeline`
- `src/steps/rendering.py` imports rendering functions from `cv_generator.__main__`
- Multiple files import `CVConfig` from `cv_generator.config`

While the CLI is now centralized and step-based, `cv_generator/` remains partly unmigrated:
- `__main__.py` (837 lines) — contains rendering logic, build functions, CLI code
- `pipeline.py` (1500+ lines) — contains orchestration classes still used by steps
- `config.py` — should move to `src/utils/config.py`
- Legacy files: `renderer.py`, `styles.py`, `compile`, `Code/`, `DHIK_filled/`, `Txt/`, `src/`, `.env`

---

## Objectives

1. ✅ Move `config.py` to `src/utils/config.py` (DONE — already copied)
2. Update all imports of CVConfig from `cv_generator` → `utils`
3. Delete legacy/dead code from cv_generator
4. Decide on pipeline orchestration classes: keep minimal or inline
5. Ensure all tests pass after refactoring

---

## Recommended Approach: "Minimal Keep"

**Philosophy**: Steps use cv_generator only for orchestration classes (MatchProposalPipeline, CVTailoringPipeline, parse_reviewed_proposal). Everything else moves/deletes.

### What Gets Deleted

```
src/cv_generator/renderer.py          # old table-based DOCX (use src/render/docx.py instead)
src/cv_generator/styles.py            # duplicate of src/render/styles.py
src/cv_generator/compile              # legacy shell script (use CLI)
src/cv_generator/Code/                # legacy data dir in code tree
src/cv_generator/DHIK_filled/         # legacy data dir
src/cv_generator/Txt/                 # legacy data dir
src/cv_generator/src/                 # legacy data dir
src/cv_generator/.env                 # should not be in code tree
src/cv_generator/__main__.py           # legacy CLI (all logic → steps, rendering still there for now)
```

### What Gets Moved

```
src/cv_generator/config.py            → src/utils/config.py
```

**Status**: ✅ DONE (file already copied, imports need updating)

### What Gets Kept

```
src/cv_generator/pipeline.py          # MatchProposalPipeline, CVTailoringPipeline
src/cv_generator/loaders/             # profile loading (still used)
src/cv_generator/model.py             # CV data model (still used)
src/cv_generator/__init__.py           # package init
src/cv_generator/ats.py               # (may already be in src/utils/ats.py from prior work)
```

**Rationale**: These are minimal utilities used by steps. Inlining them would duplicate code across steps and increase per-step complexity. Better to keep as a shared "orchestration" module.

---

## Files to Update Imports

**CVConfig moved from cv_generator.config → utils.config**

| File | Line | Old Import | New Import |
|------|------|-----------|-----------|
| `src/motivation_letter/service.py` | 11 | `from src.cv_generator.config import CVConfig` | `from src.utils.config import CVConfig` |
| `src/cli/pipeline.py` | 750 | `from src.cv_generator.config import CVConfig` | `from src.utils.config import CVConfig` |
| `src/cv_generator/pipeline.py` | 12 | `from src.cv_generator.config import CVConfig` | `from src.utils.config import CVConfig` |
| `src/cv_generator/__main__.py` | 21 | `from src.cv_generator.config import CVConfig` | `from src.utils.config import CVConfig` |
| `src/agent/tools.py` | 17 | `from src.cv_generator.config import CVConfig` | `from src.utils.config import CVConfig` |
| `src/agent/orchestrator.py` | 22 | `from src.cv_generator.config import CVConfig` | `from src.utils.config import CVConfig` |
| `tests/motivation_letter/test_service.py` | 5 | `from src.cv_generator.config import CVConfig` | `from src.utils.config import CVConfig` |

---

## Execution Plan

### Phase 1: Update Imports for CVConfig (7 files)

For each file listed above, replace:
```python
from src.cv_generator.config import CVConfig
```
with:
```python
from src.utils.config import CVConfig
```

**Tools**: Use `mcp__plugin_serena_serena__replace_content` with regex mode.

### Phase 2: Delete Legacy Files/Directories

```bash
rm src/cv_generator/renderer.py
rm src/cv_generator/styles.py
rm src/cv_generator/compile
rm -rf src/cv_generator/Code/
rm -rf src/cv_generator/DHIK_filled/
rm -rf src/cv_generator/Txt/
rm -rf src/cv_generator/src/
rm -f src/cv_generator/.env
```

**Keep**: `pipeline.py`, `loaders/`, `model.py`, `__init__.py`, `ats.py` (if still there), `__main__.py` (for now, can refactor later)

### Phase 3: Update config.py in utils if it has internal cv_generator imports

Read `src/utils/config.py` and check if it imports from `src.cv_generator` anywhere. If so, update those imports.

### Phase 4: Verify No Broken Imports

Search for remaining imports from deleted/moved modules:
```
from src.cv_generator.renderer import
from src.cv_generator.styles import
from src.cv_generator.config import  (should all be gone after Phase 1)
```

If found, fix them.

### Phase 5: Run Test Suite

```bash
cd /home/jp/phd/.worktrees/pipeline-redesign
pytest tests/ -v
```

Expected: All tests pass (or only pre-existing failures remain related to missing API keys, etc.)

### Phase 6: Create Commits

**Commit 1**: Update imports for CVConfig migration
```
refactor: update imports — CVConfig moved from cv_generator.config to utils.config
```

**Commit 2**: Delete legacy files from cv_generator
```
chore: delete legacy files from cv_generator — renderer.py, styles.py, compile, legacy data dirs
```

**Commit 3** (if needed): Fix any remaining issues
```
fix: address import/dependency issues after cv_generator cleanup
```

---

## Context for Agent

**Worktree location**: `/home/jp/phd/.worktrees/pipeline-redesign`

**Key insight**: The steps module still imports orchestration classes (MatchProposalPipeline, CVTailoringPipeline, parse_reviewed_proposal) from `cv_generator.pipeline`. This is **intentional** — these are shared pipeline orchestration utilities that should stay in one place rather than being duplicated across step modules.

**Why not inline?**
- `MatchProposalPipeline` and `CVTailoringPipeline` are 300+ lines each with complex LLM logic
- Would duplicate code if inlined into both matching and cv_tailoring steps
- `parse_reviewed_proposal()` is a parsing utility used by both matching and email_draft steps
- Better architectural pattern: steps call lightweight orchestration classes, which stay in `cv_generator.pipeline`

**Why delete __main__.py later?**
- Currently contains rendering orchestration (build_cv, render_docx, render_latex, etc.)
- Can stay for now since `src/steps/rendering.py` may use it
- Can be fully inlined/deleted after rendering step is fully autonomous
- Focus on CVConfig migration and legacy cleanup first

---

## Testing Strategy

**Before refactoring:**
- Note the current test pass/fail count

**After Phase 1 (CVConfig imports):**
- Run tests to verify import change doesn't break anything

**After Phase 2 (Delete legacy):**
- Run tests to verify deleted files weren't imported anywhere
- Search codebase for references to deleted modules
- If found, either fix imports or mark as expected failures

**Final:**
- All tests should pass (except pre-existing failures: API key, etc.)
- `git log --oneline` should show clean, logical commits

---

## Agent Instructions

1. **Start in worktree**: `/home/jp/phd/.worktrees/pipeline-redesign`
2. **Use Serena tools** for all file operations (read, search, replace, delete)
3. **Execute phases in order** — don't skip
4. **After each phase**, run `pytest tests/ -v --tb=short` to catch issues early
5. **If tests fail**, investigate and fix before moving to next phase
6. **Create commits after each phase** using git
7. **Report final status** with test results and any issues encountered

---

## Success Criteria

- ✅ All CVConfig imports updated (7 files)
- ✅ All legacy files deleted
- ✅ No broken imports in codebase
- ✅ Test suite passes (or only pre-existing failures remain)
- ✅ `src/cv_generator/` reduced to core orchestration classes only
- ✅ Two clean commits documenting the changes

---

## Notes

- **config.py already moved** to `src/utils/config.py` — just needs imports updated
- **__main__.py can be cleaned up later** — focus on dead code deletion first
- **All steps should still work** after this refactoring — they only lose cv_generator imports and gain utils imports
- **No new functionality** — this is pure cleanup/reorganization

