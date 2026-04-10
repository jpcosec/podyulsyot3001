# Plan: Textual UI Demo Navigation Testing

## Context

The Postulator HITL Review UI is a multi-screen Textual application with:
- Demo launcher (menu)
- 4 review screens (Match, Blueprint, Content, Profile)
- Explorer screen (job browser)

This plan maps all possible navigation paths and establishes comprehensive test coverage.

## Core Testing Infrastructure

### textual-web (Central Component)

`textual-web` is the bridge that enables browser-based testing of Textual apps:

```bash
# Install
pip install textual-web

# Run alongside the app
textual-web --config textual_web.toml
```

**Configuration** (`textual_web.toml`):
```toml
[app.MatchReviewApp]
command = "python -m src.cli.main demo"
slug = "review-ui"
port = 8765
```

This exposes the TUI at `http://localhost:8765/review-ui/`, enabling:
- **TestSprite MCP** to run Playwright-based E2E tests
- Manual visual testing in a browser
- Screenshot comparison for visual regression

### TestSprite Integration

Using `testsprite_testsprite_*` MCP tools:

1. **Requirements**:
   - textual-web server running
   - App launched via demo or review command
   - TestSprite MCP configured

2. **Workflow**:
   - Generate test plan via `testsprite_testsprite_generate_code_and_execute`
   - Review AI-generated test cases
   - Execute in cloud sandbox
   - Get self-healing Playwright code

3. **Configuration**:
   ```
   Web application starting URL: http://localhost:8765/review-ui/
   ```

---

## Full Navigation Map

### Demo Launcher (`DemoLauncher`)

```
[START] DemoLauncher
    │
    ├── btn_1 → MatchReviewScreen (hitl_1)
    ├── btn_2 → BlueprintReviewScreen (hitl_2)
    ├── btn_3 → ContentReviewScreen (hitl_3)
    ├── btn_4 → ProfileDiffScreen (hitl_4)
    └── btn_quit → [EXIT]
```

### MatchReviewScreen (HITL 1)

```
[ENTRY: Direct or from Explorer]
    │
    ├── [Keyboard Navigation]
    │   ├── j → cursor_down (next match)
    │   ├── k → cursor_up (prev match)
    │   │
    ├── [Single Item Actions]
    │   ├── y → approve_selected
    │   ├── n → reject_selected
    │   ├── space → toggle_selected
    │   │
    ├── [Bulk Actions]
    │   ├── a → approve_all
    │   ├── r → reject_all
    │   │
    ├── [List Selection]
    │   └── [ENTER on list item] → _on_item_selected → _update_detail
    │   │
    ├── [Submit]
    │   ├── s → submit → _do_submit → resume_with_review
    │   │       └── [SUCCESS] → action_quit_screen
    │   │
    │   └── [Button: Submit] → same as s
    │   │
    └── [Back]
        └── q → action_quit_screen → [POP or EXIT]
```

### BlueprintReviewScreen (HITL 2)

```
[ENTRY]
    │
    ├── [Keyboard Navigation]
    │   ├── j → cursor_down
    │   ├── k → cursor_up
    │   │
    ├── [Section Actions]
    │   ├── e → action_edit_intent → IntentEditModal
    │   │                              ├── [SAVE] → dismiss → update section
    │   │                              └── [CANCEL] → dismiss → no change
    │   │
    │   └── x → action_toggle_drop → toggle section dropped state
    │   │
    ├── [Submit]
    │   ├── s → submit → _do_submit
    │   └── [Button: Submit] → same
    │   │
    └── [Back]
        └── q → action_quit_screen
```

### ContentReviewScreen (HITL 3) - Vim Mode

```
[ENTRY]
    │
    ├── [Tab Navigation]
    │   ├── [Click tab] → switch tab pane
    │   └── [Editor per tab: CV, Letter, Email]
    │   │
    ├── [Normal Mode Keys]
    │   ├── j → cursor_down
    │   ├── k → cursor_up
    │   ├── v → enter VISUAL mode
    │   ├── d → delete selected segments
    │   ├── c → replace selected segments → AnnotationModal
    │   │
    ├── [Visual Mode Keys]
    │   ├── j/k → extend selection
    │   ├── escape → exit VISUAL → NORMAL
    │   ├── d → delete selection
    │   ├── c → replace selection → AnnotationModal
    │   │
    ├── [AnnotationModal]
    │   ├── [SAVE] → dismiss → save annotation
    │   └── [CANCEL] → dismiss → discard
    │   │
    ├── [Submit]
    │   ├── s → submit
    │   └── [Button] → same
    │   │
    └── [Back]
        └── q → action_quit_screen
```

### ProfileDiffScreen (HITL 4)

```
[ENTRY]
    │
    ├── [Display Only]
    │   └── Shows diff of proposed profile changes
    │   │
    ├── [Actions]
    │   ├── a → action_approve → _do_submit("approve")
    │   ├── r → action_reject → _do_submit("reject")
    │   │
    ├── [Buttons]
    │   ├── [Approve & Persist] → action_approve
    │   └── [Reject] → action_reject
    │   │
    └── [Back]
        └── q → action_quit_screen
```

### ExplorerScreen (Job Browser)

```
[ENTRY: When no source/job-id specified]
    │
    ├── [Refresh]
    │   ├── r → action_refresh → @work → _bus.client.list_jobs
    │   ├── [Click Refresh] → same
    │   └── [Click any button] → action_refresh
    │   │
    ├── [Filtering]
    │   ├── f → action_focus_filter → focus Input
    │   ├── 1 → action_filter_all
    │   ├── 2 → action_filter_pending
    │   ├── 3 → action_filter_completed
    │   ├── 4 → action_filter_failed
    │   ├── [Type in filter] → _on_filter_changed → _apply_filter
    │   │
    ├── [Status Buttons]
    │   ├── [All] → _on_all_pressed
    │   ├── [Pending] → _on_pending_pressed
    │   ├── [Completed] → _on_completed_pressed
    │   └── [Failed] → _on_failed_pressed
    │   │
    ├── [Row Selection]
    │   └── [ENTER on row] → _on_row_selected
    │                      ├── [has_review_pending] → _push_stage_screen
    │                      └── [else] → notify (no review needed)
    │   │
    └── [Quit]
        └── q → action_quit_screen → [EXIT]
```

---

## Test Matrix

### Demo Flow Tests

| ID | From | Action | To | Assertions |
|----|------|--------|----|------------|
| DF-01 | DemoLauncher | click btn_1 | MatchReviewScreen | correct stage |
| DF-02 | DemoLauncher | click btn_2 | BlueprintReviewScreen | correct stage |
| DF-03 | DemoLauncher | click btn_3 | ContentReviewScreen | correct stage |
| DF-04 | DemoLauncher | click btn_4 | ProfileDiffScreen | correct stage |
| DF-05 | DemoLauncher | click btn_quit | EXIT | app.exit() called |

### MatchReviewScreen Tests

| ID | Action | Assertions |
|----|--------|------------|
| MR-01 | j key | cursor moves down |
| MR-02 | k key | cursor moves up |
| MR-03 | y key | item approved, auto-advance |
| MR-04 | n key | item rejected, auto-advance |
| MR-05 | space key | item toggled |
| MR-06 | a key | all items approved |
| MR-07 | r key | all items rejected |
| MR-08 | s key | submit called |
| MR-09 | q key | screen popped |
| MR-10 | submit success | returns to previous screen |
| MR-11 | submit failure | error displayed, button re-enabled |

### BlueprintReviewScreen Tests

| ID | Action | Assertions |
|----|--------|------------|
| BP-01 | j/k keys | cursor moves |
| BP-02 | e key | modal opens |
| BP-03 | modal save | intent updated |
| BP-04 | modal cancel | intent unchanged |
| BP-05 | x key | section dropped/restored |
| BP-06 | s key | submit called |

### ContentReviewScreen Tests

| ID | Action | Assertions |
|----|--------|------------|
| CR-01 | tab switch | correct pane shown |
| CR-02 | j/k in NORMAL | cursor moves |
| CR-03 | v key | enters VISUAL mode |
| CR-04 | escape in VISUAL | returns to NORMAL |
| CR-05 | d in VISUAL | delete annotation created |
| CR-06 | c in VISUAL | modal opens |
| CR-07 | s key | submit with patches |
| CR-08 | submit success | screen popped |

### ProfileDiffScreen Tests

| ID | Action | Assertions |
|----|--------|------------|
| PD-01 | a key | approve action |
| PD-02 | r key | reject action |
| PD-03 | approve success | screen popped |
| PD-04 | reject success | screen popped |

### ExplorerScreen Tests

| ID | Action | Assertions |
|----|--------|------------|
| EX-01 | mount | table initialized, refresh started |
| EX-02 | r key | refresh triggered |
| EX-03 | filter input | filter applied |
| EX-04 | 1-4 keys | status filter changed |
| EX-05 | row enter (pending) | pushes review screen |
| EX-06 | row enter (completed) | notify message shown |
| EX-07 | q key | app exits |

### Error State Tests

| ID | Scenario | Assertions |
|----|---------|------------|
| ER-01 | API unavailable | error notification shown |
| ER-02 | No jobs returned | empty table, no crash |
| ER-03 | Submit failure | error in status log, button re-enabled |
| ER-04 | Load failure | error notification, no crash |

### Thread Safety Tests

| ID | Scenario | Assertions |
|----|---------|------------|
| TS-01 | Worker exception | error caught, UI updated safely |
| TS-02 | Multiple rapid submits | handled sequentially |
| TS-03 | Screen popped during worker | no crash |

---

## Implementation Order

### Phase 1: textual-web Infrastructure
1. **Add textual-web dependency** to `requirements.txt`
2. **Create `textual_web.toml`** configuration file
3. **Add startup script** `scripts/run_textual_web.sh`

### Phase 2: pytest-textual Unit Tests
4. **Create `tests/unit/review_ui/test_explorer_screen.py`**
5. **Create `tests/unit/review_ui/test_navigation.py`**
6. **Create `tests/unit/review_ui/test_error_states.py`**
7. **Extend `test_demo_interactions.py`** with missing cases

### Phase 3: TestSprite Integration
8. **Update `AGENTS.md`** with textual-web + TestSprite instructions
9. **Document test execution workflow** in `src/review_ui/README.md`

---

## Files to Create/Modify

### New Files
- `textual_web.toml` - textual-web configuration
- `scripts/run_textual_web.sh` - startup helper
- `tests/unit/review_ui/test_explorer_screen.py`
- `tests/unit/review_ui/test_navigation.py`
- `tests/unit/review_ui/test_error_states.py`

### Modify
- `requirements.txt` - add textual-web
- `tests/unit/review_ui/test_demo_interactions.py` - extend coverage
- `src/review_ui/README.md` - add testing section
- `docs/reference/external_libs/textual.md` - expand textual-web section

---

## Execution Commands

### pytest-textual (Unit/Integration)
```bash
# Run all review UI tests
python -m pytest tests/unit/review_ui/ -v

# Run specific test file
python -m pytest tests/unit/review_ui/test_explorer_screen.py -v

# Run with coverage
python -m pytest tests/unit/review_ui/ --cov=src/review_ui
```

### textual-web + TestSprite (E2E)
```bash
# Terminal 1: Start textual-web
./scripts/run_textual_web.sh

# Terminal 2: Use TestSprite MCP
# In IDE, use testsprite_testsprite_* tools pointing to:
# http://localhost:8765/review-ui/
```

---

## Success Criteria

- All 50+ pytest-textual test cases passing
- textual-web configuration working
- TestSprite able to connect and generate tests
- Zero uncovered critical paths
- Thread safety verified
- Error states gracefully handled
