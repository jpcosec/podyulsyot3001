# 🏗️ Feature Creation & Refactor Methodology

This standard defines the mandatory five-step methodology for designing and implementing complex features or structural refactors. It ensures that every change is grounded in a deep understanding of the current state and results in a decoupled, maintainable architecture.

---

## 1. Baseline & Inventory (The Audit)

**Definition:** Establishing a "source of truth" and a baseline for comparison before touching code.

### Requirements:
- **Map the Current State:** Identify every file, module, and data artifact involved in the change.
- **Dependency Audit:** Trace how data flows into and out of the affected area.
- **Test Baseline:** Run all existing tests in the target area. If tests are missing or broken, fix them or write "capture tests" to document current behavior.
- **Issue Inventory:** List known bugs, "fragility" points, and technical debt in the current implementation.

**Goal:** To ensure no existing responsibility is lost and to have a baseline to prove the new implementation is correct.

---

## 2. Orthogonalize Dimensions (Conceptual Decoupling)

**Definition:** Identifying the independent axes of the feature and drawing "hard boundaries" between them.

### Requirements:
- **Separate Concerns:** Identify the distinct dimensions of the problem. Typical dimensions include:
    - **Mechanisms (The "How"):** Execution engines, third-party libraries, transport layers.
    - **Domain Knowledge (The "Where/Who"):** Site-specific logic, source definitions, portal-level intent.
    - **State & Knowledge (The "What"):** Playbooks, schemas, traces, persistent history.
    - **Orchestration (The "When"):** The high-level workflow or graph that coordinates the other dimensions.
- **Enforce Boundaries:** Define a rule that Dimensions must remain decoupled. A change in "The How" (e.g., switching a library) should never require a change in "The Where" (site-specific logic).

**Goal:** To create a system where independent parts can evolve at different speeds without side effects.

---

## 3. Architecture (The Structural Frame)

**Definition:** Translating the conceptual dimensions into a physical directory and module hierarchy.

### Requirements:
- **Map Dimensions to Folders:** Create a directory structure that reflects the orthogonalized dimensions.
- **Establish Legal Ownership:** Define exactly what type of logic is allowed in each directory.
- **Create Scaffolding:** Build the package root and the primary sub-packages (e.g., `motors/`, `portals/`, `ariadne/`).
- **Define Entrypoints:** Establish the main CLI or API surface that orchestrates the internal modules.

**Goal:** To eliminate ambiguity about where a piece of code belongs and to prevent "logic leakage" between layers.

---

## 4. Specifications (The Formal Contracts)

**Definition:** Defining the Pydantic models, Abstract Base Classes (ABCs), and Protocols that act as the system's internal API.

### Requirements:
- **Data Contracts:** Use Pydantic V2 models to define every data structure that passes between dimensions.
- **Interfaces:** Use ABCs or Protocols to define the "Motor" or "Provider" interfaces. 
- **Validation:** Ensure the specs handle validation and normalization (e.g., converting relative dates to ISO-8601).
- **Documentation:** The Spec *is* the documentation. Field descriptions and type hints are the authoritative source of truth.

**Goal:** To create a "lingua franca" that allows different modules to work together safely without knowing each other's internal details.

---

## 5. Tactical Plan (Execution Slices)

**Definition:** The incremental, step-by-step checklist for implementation or migration.

### Requirements:
- **Work in Slices:** Break the implementation into small, testable units (e.g., "Portal selectors first," then "Engine implementation," then "CLI wiring").
- **Maintain Stability:** Each slice should ideally leave the codebase in a valid state (even if the feature is incomplete).
- **Test-Driven:** Write tests for the new contracts and interfaces *before* or alongside the implementation.
- **The "Final Cut":** For refactors, the final step is the removal of legacy code and the comprehensive update of documentation and imports.

**Goal:** To minimize the "Broken Window" period and ensure that every step of the execution is verified.

---

## ⚖️ When to Use This Methodology

This methodology is **mandatory** for:
1. Any new top-level package or major subsystem.
2. Any refactor that changes the ownership or location of core logic.
3. Any feature that integrates multiple execution backends or third-party services.

For small, localized bug fixes or minor enhancements within an existing architecture, a simpler `plan_docs/` entry is sufficient.
