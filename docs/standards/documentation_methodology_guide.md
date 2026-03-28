# 📚 Documentation Methodology Guide

This document outlines the high-level philosophy, structural expectations, and overarching methodology for documenting components across the entire repository. 

> [!IMPORTANT]
> The overriding philosophy of our documentation strategy is that **documentation is active, not passive**. It serves humans, guides LLM agents, and enforces visual structure in both code and real-time execution.

---

## 1. The Active Documentation Philosophy

Documentation in this workspace is not just "text that explains code." It actively participates in the system:
1. **As LLM Prompts:** Docstrings and schema descriptions are parsed and fed to LLM extraction or reasoning components.
2. **As Operational Contracts:** Errors and constraints must be explicitly surfaced as properties and custom exceptions, defining physical boundaries for subsystems.
3. **As Visual Traces:** Logging acts as a real-time documented trail of execution via standardized emoji markers.

## 2. README Structural Conventions

There must be **at least one general, top-level `README.md`** at the root of the repository to orient developers and agents. Additionally, every major component, module, or pipeline must contain its own `README.md` that adheres to a strict structural methodology. 

### 2.1 Emoji-Driven Visual Hierarchy
Emojis are mandatory structural markers. They provide immediate visual scanning for both the developer and external reviewers.
- Use large standard emojis for top-level headers (e.g., `## 🏗️ Architecture & Features`, `## 🚑 Troubleshooting`).
- Maintain a consistent mapping between the emoji intent and the content.

### 2.2 Standard README Sections
`README.md` files must contain the following core sections as a minimum baseline:
- **Architecture & Features:** High-level overview of *how* the system works and its primary design traits.
- **Configuration (`⚙️`):** Required environment variables, keys, and setup instructions inside markdown code blocks.
- **CLI / Usage (`🚀`):** Detailed markdown tables listing arguments, defaults, descriptions, or integration APIs.
- **The Data Contract (`📝`):** Explicit definition of inputs/outputs, payloads, and state representations.
- **How to Add/Extend (`🛠️`):** A strict, numbered, algorithmic guide for adding new modules, classes, or providers.
- **How to Use (`💻`):** Clear, copy-pasteable code examples, quickstarts, or step-by-step usage instructions.
- **Troubleshooting (`🚑`):** Common errors mapped in a "Symptom -> Diagnosis -> Solution" format.

## 3. Inline Documentation & Comments

Code must be comprehensively documented at the source level. Clear indications and inline comments (e.g., PyDocs, JavaDocs, JSDocs) are strictly required:
- **Public Interfaces:** Every class, function, and method must have a structured docstring defining its purpose, arguments, and return values.
- **Complex Logic:** Any non-obvious business rules, algorithms, or intentional workarounds must be explained with inline comments.
- **LLM Priming:** As noted in our philosophy, docstrings are often parsed and fed directly to LLM context windows. Keep descriptions accurate to ensure correct extraction.

## 4. Documentation Maintenance Lifecycle

Documentation must never be allowed to drift from the implementation. It is maintained simultaneously with the code.
- **When adding new mechanisms (e.g., fallbacks, retries):** The logging observability trace must be updated.
- **When editing Pydantic schemas:** The `description` field must be refined so the LLM continues extracting/acting on it correctly.
- **When creating a new architectural pattern:** The `## 🏗️ Architecture` and `## 🛠️ How to Add` sections in the component's README must be immediately updated.
