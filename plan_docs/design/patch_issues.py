import os

tasks_dir = "../tasks/"
issues = [
    "oop-01-scaffold.md",
    "oop-02-adapters.md",
    "oop-03-cognition.md",
    "oop-04-theseus.md",
    "oop-05-delphi.md",
    "oop-06-recorder.md",
    "oop-07-graph-wiring.md",
    "oop-08-cleanup.md"
]

LAWS = {
    "law-1": "- **Law 1 (No Blocking I/O):** All I/O in `ariadne/` MUST be `async/await`. No `open()`, `time.sleep()`, or `requests`.",
    "law-2": "- **Law 2 (One Browser Per Mission):** A single `async with executor` block must wrap the entire graph execution. Nodes must never open or close the browser themselves.",
    "law-3": "- **Law 3 (DOM Hostility):** All JS injection must use an isolated overlay. Do not mutate existing DOM nodes or event listeners.",
    "law-4": "- **Law 4 (Finite Routing):** All loops must have finite circuit breakers. Escalation through counters (heuristic_retries >= 2, agent_failures >= 3) to HITL is mandatory.",
    "dip": "- **DIP Enforcement:** `ariadne/` (domain layer) must never import from `motors/` (infrastructure layer). Infrastructure is injected via `config` or resolved through `MotorRegistry`."
}

PILLS = {
    "law-1": "- `plan_docs/context/law-1-async.md`",
    "law-2": "- `plan_docs/context/law-2-single-browser.md`",
    "law-3": "- `plan_docs/context/law-3-dom-hostility.md`",
    "law-4": "- `plan_docs/context/law-4-finite-routing.md`",
    "dip": "- `plan_docs/context/dip-enforcement.md`"
}

def patch_issue(filename):
    path = os.path.join(tasks_dir, filename)
    with open(path, "r") as f:
        content = f.read()

    # Determine which laws apply
    applied_laws = ["law-1", "dip"]
    if "02" in filename: applied_laws.append("law-2")
    if "04" in filename: applied_laws.append("law-3")
    if "05" in filename: applied_laws.append("law-4")
    if "07" in filename: applied_laws.append("law-4")

    # Extract sections
    lines = content.split("\n")
    title = lines[0]
    umbrella = ""
    explanation = ""
    reference = ""
    what_to_do = ""
    acceptance = ""
    pills = []
    
    current_section = None
    for line in lines[1:]:
        if line.startswith("**Umbrella:**"): umbrella = line
        elif line.startswith("**Explanation:**"): explanation = line.replace("**Explanation:**", "").strip()
        elif line.startswith("**Reference:**"): reference = line.replace("**Reference:**", "").strip()
        elif line.startswith("**What to create:**") or line.startswith("**What to do:**") or line.startswith("**Flow"):
            current_section = "steps"
            what_to_do += line + "\n"
        elif line.startswith("### Acceptance criteria"):
            current_section = "test"
        elif line.startswith("### 📦 Required Context Pills"):
            current_section = "pills"
        elif current_section == "steps":
            what_to_do += line + "\n"
        elif current_section == "test":
            acceptance += line + "\n"
        elif current_section == "pills":
            if line.strip().startswith("-"):
                pills.append(line.strip())

    # Build new content
    new_content = [title, "", umbrella, ""]
    
    # 1. What is wrong
    new_content.append("### 1. What is wrong")
    new_content.append(explanation if explanation else "Missing core OOP infrastructure.")
    new_content.append("")
    
    # 2. Reference
    new_content.append("### 2. Reference")
    new_content.append(reference if reference else "N/A")
    new_content.append("")
    
    # 3. Real fix
    new_content.append("### 3. Real fix")
    if "01" in filename: fix = "A new `src/automation/ariadne/core/` package with protocols and stubs."
    elif "02" in filename: fix = "Concrete `BrowserOSAdapter` and `Crawl4AIAdapter` implementing `BrowserAdapter`."
    elif "03" in filename: fix = "`Labyrinth` and `AriadneThread` classes with async persistence via `ariadne/io.py`."
    elif "04" in filename: fix = "Deterministic `Theseus` actor absorbing `observe` and `execute_deterministic` nodes."
    elif "05" in filename: fix = "Rescue `Delphi` actor absorbing `llm_rescue` and `hitl` nodes with circuit breakers."
    elif "06" in filename: fix = "Unified `Recorder` actor handling both active and passive trace assimilation."
    elif "07" in filename: fix = "Complete DI rewrite of `orchestrator.py` and `main.py` using new actors."
    elif "08" in filename: fix = "Removal of all legacy node modules and configuration-based mode switching."
    else: fix = "Refactor logic into OOP structure."
    new_content.append(fix)
    new_content.append("")
    
    # 4. Steps
    new_content.append("### 4. Steps")
    new_content.append(what_to_do.strip().replace("**What to create:**", "").replace("**What to do:**", "").strip())
    new_content.append("")
    
    # 5. Test command
    new_content.append("### 5. Test command")
    new_content.append(acceptance.strip())
    new_content.append("")
    
    # 6. Required Context Pills
    new_content.append("### 📦 Required Context Pills")
    for law in applied_laws:
        pill = PILLS[law]
        if pill not in pills:
            pills.append(pill)
    if filename == "oop-01-scaffold.md":
        # oop-01 already has some pills, keep them but ensure the required ones are there
        pass
    elif filename == "oop-02-adapters.md":
        pills.extend(["- `plan_docs/context/peripheral-adapter-contract.md`"])
    elif filename == "oop-03-cognition.md":
        pills.extend(["- `plan_docs/context/labyrinth-model.md`", "- `plan_docs/context/ariadne-thread-model.md`"])
    
    # Ensure ariadne-models.md is in most
    if "08" not in filename and "- `plan_docs/context/ariadne-models.md`" not in pills:
        pills.append("- `plan_docs/context/ariadne-models.md`")

    for pill in sorted(list(set(pills))):
        new_content.append(pill)
    new_content.append("")
    
    # 7. Non-Negotiable Constraints
    new_content.append("### 🚫 Non-Negotiable Constraints")
    for law in applied_laws:
        new_content.append(LAWS[law])
    new_content.append("")

    with open(path, "w") as f:
        f.write("\n".join(new_content))

for issue in issues:
    print(f"Patching {issue}...")
    patch_issue(issue)
