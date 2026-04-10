# AGENTS.md — Unified Agent Context

This is the canonical agent entrypoint for this repository.
`CLAUDE.md` and `GEMINI.md` should be compatibility symlinks to this file so all agents read the same project guidance.

WARNING: if you opened `CLAUDE.md` or `GEMINI.md`, you are reading a symlinked compatibility path. The real source of truth is `AGENTS.md`. Edit `AGENTS.md` only.

## Project Orientation

This repository is a browser-automation worktree built around the Ariadne semantic layer.
Agents should orient first, then execute: understand the architecture, verify runtime prerequisites, follow the issue workflow, and only then make code or documentation changes.

- Read `README.md` first for repository shape and purpose.
- For code or documentation edits, follow `docs/standards/` instead of relying on local habits.
- Treat `src/automation/main.py` as the main CLI entrypoint for automation flows.
- Treat `plan_docs/issues/Index.md` as the execution queue once issue planning is active.

## Runtime Prerequisite

BrowserOS must be launched before using any BrowserOS-backed flow or validation.
Do not assume the runtime is already available.

```bash
/home/jp/BrowserOS.AppImage --no-sandbox
curl http://127.0.0.1:9000/mcp
```

- Launch BrowserOS before `apply`, BrowserOS-backed `scrape`, `browseros-check`, or BrowserOS recording/promotion work.
- Prefer `http://127.0.0.1:9000` as the stable local front door.
- Override with `BROWSEROS_BASE_URL`.
- Start BrowserOS-related work from `docs/reference/external_libs/browseros/readme.txt`.
- Setup workflow lives in `docs/automation/browseros_setup.md`.

## Common Commands

```bash
# Run all automation unit tests
python -m pytest tests/unit/automation/ -q

# Run a specific test file
python -m pytest tests/unit/automation/ariadne/test_session.py -v

# Run a focused module suite
python -m pytest tests/unit/automation/motors/crawl4ai/test_compiler.py -v

# Scrape jobs from a portal
python -m src.automation.main scrape --source <stepstone|xing|tuberlin> --limit <n>

# Scrape with visible collaborative recording
python -m src.automation.main scrape --interactive --visible --record --backend browseros --source <portal> --limit <n>

# Apply to a job (BrowserOS default motor)
python -m src.automation.main apply --source <xing|stepstone|linkedin> --job-id <id> --cv <path>

# Apply via Crawl4AI backend
python -m src.automation.main apply --backend crawl4ai --source <portal> --job-id <id> --cv <path>

# Dry-run apply (no submission)
python -m src.automation.main apply --source <portal> --job-id <id> --cv <path> --dry-run

# Set up a portal session (manual login in BrowserOS)
python -m src.automation.main apply --source xing --setup-session

# Verify BrowserOS runtime
python -m src.automation.main browseros-check

# Promote a recorded trace to a canonical map
python -m src.automation.main promote --trace-id <id> --portal <name>
```

## BrowserOS Runtime

BrowserOS is an external AppImage, not a Python service in this repo.

| Endpoint | Default |
| --- | --- |
| Base | `http://127.0.0.1:9000` |
| MCP | `http://127.0.0.1:9000/mcp` |
| Chat | `http://127.0.0.1:9000/chat` |

## Extraction Fallbacks

```bash
export AUTOMATION_EXTRACTION_FALLBACKS="browseros,llm"
```

- Fallback definition point is `src/automation/motors/crawl4ai/scrape_engine.py`.
- `browseros` uses BrowserOS rescue and does not require `GOOGLE_API_KEY`.
- `llm` uses the Gemini rescue path and does require `GOOGLE_API_KEY`.

## Architecture

The system uses the Ariadne Semantic Layer to decouple portal logic from execution engines.

### Data Flow

```text
Recording (OpenBrowser agent) -> AriadneSessionTrace
                                -> AriadneNormalizer.normalize()
                                -> AriadnePortalMap JSON
                                -> AriadneSession.run(motor, ...)
                                -> BrowserOSMotorProvider | C4AIMotorProvider
```

### Key Layers

**`src/automation/ariadne/`** — backend-neutral brain:
- `models.py`: core types including `AriadnePortalMap`, `AriadneState`, `AriadnePath`, `AriadneStep`, `AriadneTarget`, `AriadneIntent`, `JobPosting`, and `ApplyMeta`.
- `session.py`: top-level apply orchestrator.
- `navigator.py`: state-aware path traversal with recovery.
- `motor_protocol.py`: motor provider/session protocols.
- `danger_detection.py` and `danger_contracts.py`: pre-submit safety guards.
- `hitl.py`: pause/resume human-in-the-loop support.
- `recorder.py` and `trace_models.py`: raw session capture under `data/ariadne/recordings/`.
- `normalizer.py`: converts traces into canonical portal maps.
- `job_normalization.py`: canonical cleanup for scraped job data.

**`src/automation/portals/`** — portal maps and routing:
- `<portal>/maps/easy_apply.json`: canonical apply flow map.
- `<portal>/routing.py`: portal-specific routing wrapper.
- `src/automation/portals/routing.py`: shared route resolution.

**`src/automation/motors/`** — execution backends:
- `browseros/`: MCP-driven execution with fuzzy text targeting and HITL support.
- `crawl4ai/`: compiles Ariadne paths into procedural scripts.
- `vision/` and `os_native_tools/`: stub providers for alternative interaction modes.

**`src/automation/`** root:
- `main.py`: CLI dispatcher for `scrape`, `apply`, `browseros-check`, and `promote`.
- `contracts.py`: shared execution payloads.
- `storage.py`: artifact and trace persistence.
- `credentials.py`: env-var-based credential resolution.

## Development Principles

1. Ariadne first: new portals and flows start as `AriadnePortalMap` JSON, not motor-specific code.
2. Backend neutrality: actions use `AriadneIntent`; targets carry both `css` and `text` when possible.
3. State-driven recovery: use `AriadneState` plus `presence_predicate` selectors so navigation can recover from drift.
4. Recording to promotion: record with the OpenBrowser agent, normalize with Ariadne, then promote into canonical maps.
5. Normalization ownership: semantic cleanup belongs in `src/automation/ariadne/job_normalization.py`, not in individual motors.
6. Multi-stage artifacts: scrape outputs flow through `raw.json`, `cleaned.json`, and `extracted.json` under `data/jobs/<source>/<job_id>/`.

## Standards First

When editing code or documentation, refer to `docs/standards/` before making changes.

- Code standards start at `docs/standards/code/basic.md` and use narrower guides there when relevant.
- Documentation and planning standards start at `docs/standards/docs/documentation_and_planning_guide.md`.
- Issue planning and execution rules live in `docs/standards/issue_guide.md`.
- `README.md` is the top-level human entrypoint; general docs belong under `docs/`; module-specific docs belong near the module they describe.
- Record every major change in `changelog.md`.

## Testing Guidelines

- Tests live in `tests/unit/automation/` mirroring `src/`.
- Use `pytest` naming conventions: `test_*.py` and `test_*` functions.
- Add regression coverage for behavior changes, especially portal maps, routing, normalization, and motor adapters.
- Integration tests live under `tests/integration/` and should gracefully skip when external runtime dependencies are unavailable.

## Issue And Design Cycle

- Every change is managed through `docs/standards/issue_guide.md`.
- Planning artifacts live under `plan_docs/issues/`.
- `plan_docs/issues/Index.md` is the issue entrypoint and active dependency index.
- The correct order of execution is: atomization of issues, contradiction checking, then prioritization via dependencies.
- During contradiction checking: if an issue is legacy, delete it; if issues contradict each other, resolve the contradiction or ask the user only when a real design decision is required.
- Never ask the user which issue to solve next; there is no usefulness in that. Follow dependency order from `plan_docs/issues/Index.md`.
- Do not ask the user for permission to continue to the next protocol-defined step. If the dependency order, issue workflow, and git-safety rules already determine the next action, just do it.
- Do not ask rhetorical progress questions such as whether to continue, whether to take the next cleanup step, or whether to make the required snapshot commit.
- Once an issue is resolved, remove it from `plan_docs/issues/Index.md` and delete the issue file.

## Documentation Lifecycle

- `docs/superpowers/` is not a permanent home; move any still-relevant material there into `plan_docs/`.
- `plan_docs/archive/` is transitional only: absorb any still-relevant content into canonical docs or code-adjacent documentation, then delete the archive file.
- `future_docs/` is backlog space for ideas that may later be promoted into `plan_docs/` and implemented.
- `session-ses_*.md` files are old conversation traces; absorb anything useful into canonical docs/issues and delete the trace when it no longer adds value.
- When a feature tracked in `plan_docs/` is fully implemented, make sure the implementation and documentation have absorbed the needed knowledge, then delete the finished planning artifact.

## Git Hygiene

- Never edit anything while the git tree is dirty.
- First make a commit with the existing untracked or unstaged work, then edit on top of that clean state.
- Do this automatically; do not ask the user whether to make the snapshot commit just to satisfy git cleanliness.
- Do not overwrite or discard user work to create cleanliness.

## Key References

- `README.md`
- `docs/automation/ariadne_semantics.md`
- `docs/automation/ariadne_capabilities.md`
- `docs/automation/browseros_setup.md`
- `docs/reference/external_libs/browseros/readme.txt`
- `docs/automation/architecture.md`

## Troubleshooting

- `BrowserOS unreachable`: launch `/home/jp/BrowserOS.AppImage --no-sandbox` and verify `http://127.0.0.1:9000/mcp`.
- `RuntimeError: already submitted`: inspect or remove the relevant `apply_meta.json` in the job artifact directory if you intentionally need a fresh run.
- `Compilation errors`: inspect `src/automation/motors/crawl4ai/compiler/` and the relevant portal map JSON.
- `Motor failures`: inspect logs under `logs/` and preserved job artifacts under `data/jobs/`.
