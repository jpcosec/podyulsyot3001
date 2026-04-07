# Ariadne Semantic Layer — Documentation

## Overview
The **Ariadne Semantic Layer** is the backend-neutral source of truth for automation. It separates **what** the automation is trying to do (the mission and the states) from **how** it is done (the motors and tool calls).

## Key Concepts

### 1. Semantic State (`AriadneState`)
A "State" represents a logical room or phase in a portal (e.g., "Login Page", "Resume Upload Modal").
- **Presence Predicate**: Rules for how to identify this state (e.g., "Look for X, ensure Y is NOT there").
- **Components**: The semantic elements belonging to this state (e.g., "The 'Next' button").

### 2. The Mission (`AriadneTask`)
A "Task" defines the goal of the automation.
- **Goal**: The high-level objective (e.g., `submit_job_application`).
- **Boundaries**: Explicit definitions of Success States and Terminal Failure States.
- **Recovery**: Predicates for identifying blockers (e.g., Captchas) and their associated recovery plans.

### 3. Multi-Strategy Target (`AriadneTarget`)
A single object that holds all possible ways to find an element:
- **`css`**: Used by Crawl4AI and BrowserOS (Playwright).
- **`text`**: Used by BrowserOS (Fuzzy matching).
- **`image_template` / `ocr_text`**: Used by the Vision motor.

### 4. Deterministic Path (`AriadnePath`)
A linear "tape" through a task. It is a sequence of `AriadneSteps` that reference the semantic states. This is the primary input for replayers.

---

## The Unified Map
Every portal flow (e.g., LinkedIn Easy Apply) is defined in a single JSON map at `src/automation/portals/<portal>/maps/<flow>.json`.

This map contains:
1.  A registry of all possible **States**.
2.  The definition of the **Task**.
3.  The **Paths** (the sequences of steps).

---

## Motor Implementation

### OpenBrowser (The Explorer / Level 2 Agent)
OpenBrowser is the LLM agent framework built on top of BrowserOS. It acts as the **author** of the semantic `AriadnePath`. 
When the system encounters a new or broken flow, it runs an OpenBrowser agent to intelligently explore the page. As the agent clicks and types its way through the portal, the system acts as a recording proxy, intercepting its actions and normalizing them into the **Ariadne Common Language**. 
This *produces* a new, deterministic `AriadnePath` (the "semantic path" layer) that the deterministic motors (like Crawl4AI or BrowserOS CLI) can consume for all future runs.

### BrowserOS CLI (The Mapper)
The BrowserOS motor iterates through the steps of an `AriadnePath` and executes them one-by-one as direct tool calls. It uses the `text` field of the `AriadneTarget` for high resilience to DOM changes.

### Crawl4AI (The Compiler)
The Crawl4AI motor uses a motor-specific **Compiler** (located in `src/automation/motors/crawl4ai/compiler/`) to turn the backend-neutral `AriadnePath` into a robust, procedural **C4A-Script**.


The compilation pipeline:
`Ariadne Path` → `C4AI Intermediate Representation (IR)` → `C4A-Script String`
