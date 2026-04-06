Postulator 3000 - Browser Automation Worktree

This worktree is intentionally scoped down to one issue: the browser automation pipeline.

What belongs here:
- `src/apply/` and its provider adapters, BrowserOS integration, playbooks, and related models
- `src/scraper/` only where it supports application-routing or browser-automation inputs
- focused planning/docs under `plan_docs/automation/`

What does not belong here:
- the old unified operator control plane
- unrelated LangGraph pipelines, render flows, translator flows, or review UI work
- broad repo-wide refactors that are not required for browser automation

Current intent:
- keep this worktree small and issue-focused
- use it to iterate on automated application flows and their supporting docs
- treat missing modules from the main repo as intentionally out of scope unless this issue directly needs them

If a change is needed outside the browser automation pipeline, document it as context or follow-up work instead of rebuilding unrelated parts inside this worktree.
