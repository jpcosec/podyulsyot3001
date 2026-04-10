# ♊ Gemini CLI Methodology

This document defines the mandatory project-specific methodology for interaction between the human operator and the Gemini CLI agent. It ensures all autonomous work is grounded, documented, and follows the project's internal standards.

---

## 1. Contextual Grounding (The Audit)

Before starting any task, the agent must establish a "source of truth."

- **Read Docs First:** Use `list_directory` and `read_file` on `docs/standards/` to understand the rules for the target area (e.g., `feature_creation_methodology.md`, `basic.md`).
- **Map Current State:** Use `grep_search` and `glob` to find existing implementations, patterns, and tests.
- **Dependency Audit:** Identify affected files and modules.

## 2. Planning & Documentation

All complex features, refactors, or multi-step bug fixes must be planned before code is touched.

- **Ephemeral Plans:** Create or update a plan in `plan_docs/` (e.g., `plan_docs/issues/gaps/<task_name>.md`).
- **Indexed Issues:** Update `plan_docs/issues/Index.md` to reflect current priorities and roadmap.
- **Design Specs:** For UI or architectural changes, create a specification in `docs/runtime/` first.

## 3. Orthogonal Implementation

Implementation must follow the "No file does two things" rule.

- **Contracts:** Define Pydantic models in `contracts.py` or `contracts/` first.
- **Storage:** Isolate all file I/O into `storage.py` or use the `DataManager`/`WorkspaceManager`.
- **Logic:** Keep business logic in nodes, coordinators, or dedicated engine modules.
- **CLI/UI:** Keep `main.py` and `app.py` as thin entry points/routers only.

## 4. Test-Driven Verification

The agent is responsible for the quality of its own output.

- **Unit Tests:** Every new logic module or parser (e.g., `document_parser.py`) must have a corresponding test file (e.g., `tests/unit/review_ui/test_document_parser.py`).
- **Regression Testing:** Run existing test suites (`python -m pytest tests/unit -q`) to ensure no side effects.
- **Standards Check:** Ensure code follows the `LogTag` conventions and uses the project's logging bootstrap.

## 5. Persistence & Deferral

- **Changelog:** Every significant change must be recorded in `changelog.md`.
- **Future Docs:** If a task reveals a deferred gap or a long-term problem, document it in `future_docs/` instead of leaving a `TODO` comment or a half-finished implementation.
- **Clean Up:** Delete ephemeral plans from `plan_docs/` once the work is fully committed and verified.

---

## ⚖️ Operational Guardrails

1. **Ask for Confirmation:** If a request is ambiguous or implies a major architectural change not already covered by a design doc, ask the user before proceeding.
2. **Mimic Style:** Rigorously adhere to the existing project conventions for naming, imports, and docstrings found in `docs/standards/code/basic.md`.
3. **No Silent Failures:** Never swallow errors. Log with `LogTag.FAIL` or `LogTag.WARN` and re-raise.
