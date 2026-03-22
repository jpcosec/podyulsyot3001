# Implementation Status

Tracks which features are fully implemented vs. planned vs. partially working.

## Status Definitions

| Status | Meaning |
|--------|---------|
| `implemented` | Code exists and works in production |
| `partial` | Code exists but has gaps or bypasses |
| `planned` | Design exists in `plan/`, no code yet |
| `blocked` | Planned but depends on external blocker |

---

## Pipeline Stages

| Stage | Status | Notes |
|-------|--------|-------|
| 1. Scrape | `implemented` | |
| 2. Translate | `implemented` | |
| 3. Extract | `partial` | Returns spans but doesn't pause for HITL gate |
| 4. Match | `implemented` | Full HITL gate via RoundManager |
| 5.1 Strategy | `blocked` | Nodes exist but bypassed (`PREP_MATCH_LINEAR_EDGES`) |
| 5.2 Drafting | `partial` | Generates `.md` but jumps to render without review |
| 6. Render | `implemented` | |
| 7. Package | `implemented` | |
| 8. Feedback Loop | `planned` | Aggregator not built; UI uses workaround |

---

## Features

| Feature | Status | Notes |
|---------|--------|-------|
| Local-First DB | `implemented` | `data/jobs/<source>/<job_id>/` |
| ReviewNode Schema | `implemented` | Schema defined, UI uses workaround |
| Evidence Tree | `partial` | Exists at job level, global aggregation `planned` |
| Document Delta | `planned` | Schema defined, implementation `blocked` by Strategy |
| HITL Gates | `partial` | Only Match gate fully active |
| Race Condition Protection | `planned` | No locking mechanism implemented |

---

## UI Components

| Component | Status | Notes |
|-----------|--------|-------|
| Portfolio Dashboard | `implemented` | |
| Data Explorer | `implemented` | |
| Scrape Diagnostics | `implemented` | |
| Extract/Tag UI | `implemented` | Without gate pause |
| Match Graph Canvas | `implemented` | |
| Strategy Form | `planned` | UI placeholder exists |
| Document Editor | `implemented` | Without force-render |
| Feedback Panel | `planned` | Generic review panel not built |

---

## Known Gaps (Workarounds in Place)

| Gap | Workaround | Risk |
|-----|------------|------|
| No Strategy gate | UI saves to `nodes/strategy/delta.json` manually | Data may be overwritten by future backend activation |
| No Drafting gate | UI overwrites `nodes/drafting/*.md` before render | Race condition if LangGraph runs simultaneously |
| No global Feedback Loop | UI writes `nodes/review/` for future aggregator | No immediate learning benefit |

---

## ⚠️ Critical Warning

**DO NOT USE UI as Backend Orchestrator**

The methodology says:
> "UI is a visualization layer, never primary business logic"

Current reality forces UI to:
- Stop user visually when backend doesn't pause
- Overwrite generated files
- Trigger manual render

**This violates decoupling principles. Backend must implement proper gates before production.**

Until then:
- Document all workarounds explicitly
- Add `--skip-workaround` flag when backend is fixed
- Plan migration to remove workarounds in next sprint
