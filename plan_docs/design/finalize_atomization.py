import os

tasks_dir = "../tasks/"

LAWS = {
    "law-1": "- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.",
    "law-2": "- **Law 2 (One Browser Per Mission):** A single `async with executor` block must wrap the entire graph execution. Nodes must never open or close the browser themselves.",
    "law-3": "- **Law 3 (DOM Hostility):** All JS injection must use an isolated overlay. Do not mutate existing DOM nodes or event listeners.",
    "law-4": "- **Law 4 (Finite Routing):** All loops must have finite circuit breakers. Escalation through counters (heuristic_retries >= 2, agent_failures >= 3) to HITL is mandatory.",
    "dip": "- **DIP Enforcement:** `ariadne/` (domain layer) must never import from `motors/` (infrastructure layer). Infrastructure is injected via `config` or resolved through `MotorRegistry`."
}

PILLS = {
    "law-1": "[Law 1 - No Blocking I/O](../context/law-1-async.md)",
    "law-2": "[Law 2 - One Browser Per Mission](../context/law-2-single-browser.md)",
    "law-3": "[Law 3 - DOM Hostility](../context/law-3-dom-hostility.md)",
    "law-4": "[Law 4 - Finite Routing](../context/law-4-finite-routing.md)",
    "dip": "[DIP Enforcement](../context/dip-enforcement.md)",
    "models": "[Ariadne State & Models](../context/ariadne-models.md)",
    "thread": "[Ariadne Thread Model](../context/ariadne-thread-model.md)",
    "labyrinth": "[Labyrinth Model](../context/labyrinth-model.md)",
    "io": "[Ariadne Shared I/O Pattern](../context/ariadne-io-pattern.md)",
    "recording": "[Graph Recording Pattern](../context/recording-pattern.md)",
    "promotion": "[Promotion Pattern (Recording -> Map)](../context/promotion-pattern.md)",
    "som": "[Set-of-Mark (SoM) Pattern](../context/som-pattern.md)",
    "structured": "[Structured Output Pattern (VLM/LLM)](../context/structured-output-pattern.md)",
    "gemini": "[Gemini Flash Default LLM](../context/gemini-flash-default.md)",
    "danger": "[Danger Signal & Short-Circuit Pattern](../context/danger-signal-pattern.md)",
    "error": "[Error Contract](../context/error-contract.md)",
    "node": "[Node Implementation Pattern](../context/node-pattern.md)",
    "peripheral": "[Peripheral Adapter Contract](../context/peripheral-adapter-contract.md)",
    "sensor": "[Sensor Contract](../context/sensor-contract.md)",
    "motor": "[Motor Contract](../context/motor-contract.md)",
    "smoke": "[Smoke Test Pattern (Corneta)](../context/smoke-test-pattern.md)",
    "async-test": "[Async Test Pattern (LangGraph)](../context/async-test-pattern.md)",
    "langgraph": "[Ariadne LangGraph](../context/ariadne-langgraph.md)"
}

def update_issue(filename, updates):
    path = os.path.join(tasks_dir, filename)
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return
    with open(path, "r") as f:
        content = f.read()

    # Apply updates
    new_content = updates(content)
    
    with open(path, "w") as f:
        f.write(new_content)

def generic_patch(content, laws_list, pills_list, numbering=True):
    lines = content.split("\n")
    title = lines[0]
    rest = "\n".join(lines[1:])
    
    # Remove existing Pills and Constraints if any
    if "### 📦 Required Context Pills" in rest:
        rest = rest.split("### 📦 Required Context Pills")[0]
    elif "### Required Context Pills" in rest:
        rest = rest.split("### Required Context Pills")[0]
    
    if "### 🚫 Non-Negotiable Constraints" in rest:
        rest = rest.split("### 🚫 Non-Negotiable Constraints")[0]
    elif "### Laws of Physics" in rest:
        rest = rest.split("### Laws of Physics")[0]
        
    rest = rest.strip()
    
    if numbering:
        # Try to enforce 1. Explanation, 2. Reference, 3. Real fix, 4. Steps, 5. Test command
        # This is hard to do genericly without knowing the sections, 
        # but most Phase 0.5 already have them or something close.
        pass

    new_content = [title, "", rest, ""]
    new_content.append("### 📦 Required Context Pills")
    for p in sorted(pills_list):
        new_content.append(f"- {PILLS[p]}")
    new_content.append("")
    new_content.append("### 🚫 Non-Negotiable Constraints")
    for l in sorted(laws_list):
        new_content.append(LAWS[l])
    new_content.append("")
    
    return "\n".join(new_content)

# 1. oop-02-adapters.md
def patch_02(content):
    content = content.replace("### 1. What is wrong", "### 1. Explanation")
    return generic_patch(content, ["law-1", "law-2", "dip"], ["models", "dip", "law-1", "law-2", "peripheral", "sensor", "motor"])

update_issue("oop-02-adapters.md", patch_02)

# 2. oop-03-cognition.md
def patch_03(content):
    content = content.replace("### 1. What is wrong", "### 1. Explanation")
    return generic_patch(content, ["law-1", "dip"], ["models", "thread", "dip", "labyrinth", "law-1", "io"])

update_issue("oop-03-cognition.md", patch_03)

# 3. oop-04-theseus.md
def patch_04(content):
    content = content.replace("### 1. What is wrong", "### 1. Explanation")
    return generic_patch(content, ["law-1", "law-3", "dip"], ["models", "dip", "law-1", "law-3", "danger", "labyrinth"])

update_issue("oop-04-theseus.md", patch_04)

# 4. oop-05-delphi.md
def patch_05(content):
    content = content.replace("### 1. What is wrong", "### 1. Explanation")
    return generic_patch(content, ["law-1", "law-4", "dip"], ["models", "dip", "law-1", "law-4", "structured", "gemini"])

update_issue("oop-05-delphi.md", patch_05)

# 5. oop-06-recorder.md
def patch_06(content):
    content = content.replace("### 1. What is wrong", "### 1. Explanation")
    return generic_patch(content, ["law-1", "dip"], ["models", "dip", "law-1", "io", "recording", "promotion"])

update_issue("oop-06-recorder.md", patch_06)

# 6. oop-07-graph-wiring.md
def patch_07(content):
    content = content.replace("### 1. What is wrong", "### 1. Explanation")
    return generic_patch(content, ["law-1", "law-4", "dip"], ["models", "dip", "law-1", "law-4", "langgraph"])

update_issue("oop-07-graph-wiring.md", patch_07)

# 7. oop-08-cleanup.md
def patch_08(content):
    content = content.replace("### 1. What is wrong", "### 1. Explanation")
    return generic_patch(content, ["law-1", "dip"], ["dip", "law-1"])

update_issue("oop-08-cleanup.md", patch_08)

# 8. interpreter-node.md
def patch_interpreter(content):
    # Standardize sections
    content = content.replace("**Explanation:**", "### 1. Explanation\n")
    content = content.replace("**Reference:**", "### 2. Reference\n")
    content = content.replace("**What to fix:**", "### 3. Real fix\n")
    # Acceptance criteria -> 5. Test command
    content = content.replace("### Acceptance criteria", "### 5. Test command")
    
    # Add a fake "Steps" if missing
    if "### 4. Steps" not in content:
        content = content.replace("### 5. Test command", "### 4. Steps\n1. Implement `Interpreter` actor.\n2. Add fast-path mission matching.\n3. Add slow-path VLM mapping.\n4. Wire into `build_graph()`.\n\n### 5. Test command")

    return generic_patch(content, ["law-1", "law-4", "dip"], ["structured", "models", "gemini", "thread", "labyrinth", "law-1", "law-4", "dip"])

update_issue("interpreter-node.md", patch_interpreter)

# 9. 404-danger-signal.md
def patch_404(content):
    content = content.replace("**Explanation:**", "### 1. Explanation\n")
    content = content.replace("**Reference:**", "### 2. Reference\n")
    content = content.replace("**Real fix:**", "### 3. Real fix\n")
    
    # Define how 404 is detected in SnapshotResult
    content = content.replace("check `SnapshotResult` for HTTP error signals", 
                              "check `SnapshotResult.metadata` or `SnapshotResult.page_title` for HTTP error signals (e.g., '404', 'Not Found', or status code if available in the adapter's perception)")

    # Add sections if missing
    if "### 4. Steps" not in content:
        content = content.replace("### 📦 Required Context Pills", "### 4. Steps\n1. Update `Theseus` to check `SnapshotResult` for 404 patterns.\n2. Add `http_error` to `danger_type`.\n3. Update graph routing to short-circuit 404s to HITL.\n\n### 5. Test command\nRun a mission against a known 404 URL and assert it hits HITL immediately.\n\n### 📦 Required Context Pills")

    return generic_patch(content, ["law-1", "law-4"], ["danger", "error", "models", "law-1", "law-4"])

update_issue("404-danger-signal.md", patch_404)

# 10. epic-2-smoke-and-calibration.md
def patch_epic2(content):
    # Ensure Law 2 check
    if "The new CLI's executor is always wrapped in `async with` — browser opens once, closes once." not in content:
        content += "\n6. The new CLI's executor is always wrapped in `async with` — browser opens once, closes once (Law 2)."
    
    # Add standard sections
    if "### 1. Explanation" not in content:
        content = content.replace("**Objective:**", "### 1. Explanation\n")
        content = content.replace("**Priority:**", "### 2. Reference\n`plan_docs/design/design_spec.md`\n\n### 3. Real fix\n")
        content = content.replace("**Contains:**", "### 4. Steps\n")
        content = content.replace("**Task 2.1:", "#### Task 2.1:")
        content = content.replace("**Task 2.2:", "#### Task 2.2:")
        content = content.replace("### Acceptance criteria", "### 5. Test command")

    return generic_patch(content, ["law-1", "law-2", "law-4"], ["smoke", "async-test", "law-1", "law-2", "law-4"])

update_issue("epic-2-smoke-and-calibration.md", patch_epic2)

# 11. theseus-adapter-health-guard.md
def patch_health(content):
    content = content.replace("**Explanation:**", "### 1. Explanation\n")
    content = content.replace("**Reference:**", "### 2. Reference\n")
    content = content.replace("**What to do:**", "### 3. Real fix\n")
    content = content.replace("### Acceptance criteria", "### 5. Test command")
    if "### 4. Steps" not in content:
        content = content.replace("### 5. Test command", "### 4. Steps\n1. Add `is_healthy` call to `Theseus`.\n2. Return `FatalError` if unhealthy.\n3. Wire routing to end mission on `FatalError`.\n\n### 5. Test command")
    
    return generic_patch(content, ["law-1"], ["law-1", "peripheral", "error"])

update_issue("theseus-adapter-health-guard.md", patch_health)

# 12. zero-shot-error-typing.md
def patch_zero_shot(content):
    content = content.replace("**Explanation:**", "### 1. Explanation\n")
    content = content.replace("**Reference:**", "### 2. Reference\n")
    content = content.replace("**Real fix:**", "### 3. Real fix\n")
    if "### 4. Steps" not in content:
        content = content.replace("### 📦 Required Context Pills", "### 4. Steps\n1. Define `MapNotFoundError`.\n2. Raise it in `Labyrinth.load_from_db`.\n3. Catch it in `Interpreter` and set mission to 'explore'.\n\n### 5. Test command\n`python -m pytest tests/unit/automation/ariadne/test_exceptions.py`\n\n### 📦 Required Context Pills")

    return generic_patch(content, ["law-1", "dip"], ["error", "models", "node", "law-1", "dip"])

update_issue("zero-shot-error-typing.md", patch_zero_shot)

# 13. recording-promoter-guard.md
def patch_recorder_guard(content):
    content = content.replace("**Explanation:**", "### 1. Explanation\n")
    content = content.replace("**Reference:**", "### 2. Reference\n")
    content = content.replace("**Real fix:**", "### 3. Real fix\n")
    content = content.replace("**Steps:**", "### 4. Steps\n")
    if "### 5. Test command" not in content:
        content = content.replace("### 📦 Required Context Pills", "### 5. Test command\nRecord mixed session and assert promoted map only has deterministic edges.\n\n### 📦 Required Context Pills")
    
    return generic_patch(content, ["law-1"], ["models", "thread", "labyrinth", "recording", "promotion", "law-1"])

update_issue("recording-promoter-guard.md", patch_recorder_guard)

# 14. ariadne-io-layer-and-tests.md
def patch_io_layer(content):
    content = content.replace("**Explanation:**", "### 1. Explanation\n")
    content = content.replace("**Reference:**", "### 2. Reference\n")
    content = content.replace("**What to fix:**", "### 3. Real fix\n")
    content = content.replace("**How to do it:**", "### 4. Steps\n")
    content = content.replace("### Test command", "### 5. Test command")
    
    return generic_patch(content, ["law-1"], ["law-1", "io", "recording", "promotion"])

update_issue("ariadne-io-layer-and-tests.md", patch_io_layer)

# 15. som-hint-injection.md
update_issue("som-hint-injection.md", lambda c: generic_patch(c, ["law-1", "law-3"], ["som", "law-3", "node", "models", "law-1"]))

# 16. som-agent-prompt-update.md
update_issue("som-agent-prompt-update.md", lambda c: generic_patch(c, ["law-1", "law-4"], ["som", "models", "node", "law-1", "law-4"]))

# 17. hint-failure-fallback.md
def patch_hint_fallback(content):
    content = content.replace("**Explanation:**", "### 1. Explanation\n")
    content = content.replace("**Reference:**", "### 2. Reference\n")
    content = content.replace("**Real fix:**", "### 3. Real fix\n")
    content = content.replace("**Steps:**", "### 4. Steps\n")
    if "### 5. Test command" not in content:
        content += "\n### 5. Test command\nSimulate CSP block and assert agent switches to DOM mode.\n"
    return generic_patch(content, ["law-1", "law-4"], ["som", "models", "node", "law-1", "law-4"])

update_issue("hint-failure-fallback.md", patch_hint_fallback)

# 18. epic-3-agent-hints.md
update_issue("epic-3-agent-hints.md", lambda c: generic_patch(c, ["law-1", "law-3", "law-4"], ["som", "law-3", "node", "law-1", "law-4"]))

# 19. epic-4-map-factory.md
update_issue("epic-4-map-factory.md", lambda c: generic_patch(c, ["law-1", "law-2", "dip"], ["models", "io", "recording", "promotion", "node", "law-1", "law-2", "dip"]))

# 20. map-concept-docs.md
def patch_map_docs(content):
    if "### 1. Explanation" not in content:
        content = content.replace("**Explanation:**", "### 1. Explanation\n")
        content += "\n### 2. Reference\n`ariadne-oop-architecture.md`\n\n### 3. Real fix\nDocument the split.\n\n### 4. Steps\n1. Write documentation.\n\n### 5. Test command\nN/A\n"
    return generic_patch(content, ["law-1", "dip"], ["thread", "labyrinth", "models", "law-1", "dip"])

update_issue("map-concept-docs.md", patch_map_docs)

