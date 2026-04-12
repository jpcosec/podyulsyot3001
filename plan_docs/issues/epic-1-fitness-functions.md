# EPIC 1: Architectural Fitness Functions (The Armor)

**Explanation:** Enforce architectural boundaries through automated tests. These guardrails prevent Dependency Inversion (DIP) violations and I/O leaks during the Ariadne 2.0 refactor.

**Tasks:**
1.  **Dependency Wall**: Write `pytest-archon` rules to block Ariadne (Domain) from importing Motors (Infrastructure) or direct network/disk libraries (requests, httpx).
2.  **Dumb Executors**: Write rules to ensure Executors do not import domain models (Maps/Tasks).
3.  **Clean Room Isolation**: Use `pyfakefs` to ensure Ariadne nodes cannot perform raw `open()` or `Path` disk reads, forcing the use of repositories.
4.  **Mode Blindness**: Implement a test ensuring the core normalization engine is "stupid" and returns nothing unless a Portal Mode configuration is injected.

**Success Criteria:**
- A dedicated `tests/architecture/` suite that fails (Red) if any legacy coupling or direct I/O is reintroduced.
- CI/CD build breaks on architectural drift.

**Depends on:** `epic-0-cleanup.md`
