# Git Hooks (PhD 2.0)

Automated enforcement of the Zero-Tolerance Policy at the git level.

---

## Overview

| Hook | Purpose | Blocks |
|------|---------|--------|
| `commit-msg` | Validates commit message format | Invalid format, missing TestSprite evidence |
| `pre-push` | Runs tests before push | Failed tests, type errors, linting issues |

---

## Installation

```bash
bash docs/seed/practices/scripts/setup_hooks.sh
```

Or manually:
```bash
cp docs/seed/practices/scripts/hooks/* .git/hooks/
chmod +x .git/hooks/commit-msg .git/hooks/pre-push
```

---

## commit-msg Hook

**Validates:**
1. Message follows format: `<type>(<domain>): <description> (<spec-id>)`
2. Contains TestSprite evidence: `TestSprite: Passed` or `TestSprite: ID-123`

**Valid examples:**
```bash
feat(ui): implement strategy form (spec-123)
fix(pipeline): correct span offset calculation (hotfix-456)
docs(core): update contract schema documentation
```

**Invalid — blocks commit:**
```bash
fix: corrected bug                 # Missing (spec-id)
feat(ui): new feature              # Missing (spec-id)
feat(ui): implement form (spec)    # spec-id format wrong
```

---

## pre-push Hook

**Runs:**
1. `pytest src/core/tests/` — Core unit tests
2. `npm run typecheck` — TypeScript validation
3. `npm run lint` — Linting

**If any fail → push blocked**

---

## GitHub Branch Protection (Recommended)

For complete enforcement, configure in GitHub Settings > Branches:

### Required Settings

| Setting | Value | Reason |
|---------|-------|--------|
| Require PR before merging | ✓ | Prevents direct pushes |
| Required approvals | 1+ | Human meta-review (Phase 6) |
| Require status checks | ✓ | CI must pass |
| Do not allow bypassers | ✓ | Even admins must follow rules |

### Required Status Checks

- `pytest` — Core tests
- `typecheck` — TypeScript validation
- `lint` — Code quality
- `testsprite-e2e` — E2E tests (if configured in CI)

---

## CI/CD Integration

Add to your CI pipeline (GitHub Actions example):

```yaml
# .github/workflows/validate.yml
name: PhD 2.0 Validation
on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      
      - name: Install deps
        run: pip install pytest pytest-cov
      
      - name: Run Core tests
        run: pytest src/core/tests/
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
      - name: Install deps
        run: cd apps/review-workbench && npm ci
      
      - name: Type check
        run: cd apps/review-workbench && npm run typecheck
      
      - name: Lint
        run: cd apps/review-workbench && npm run lint
```
