# Phase 2: Implement Core Nodes (ingest → match → keywords → review)

## Context for subagent

You are continuing the LangGraph pipeline migration at `/home/jp/phd`. Phase 0 created the graph skeleton with stub nodes. Phase 1 extracted parsers and agents into `src/graph/parsers/` and `src/graph/agents/`. Now you replace the stubs for the first four nodes with real implementations.

This is the most critical phase — it implements the match-review loop with `interrupt()`, which is the core UX innovation of the migration. It also integrates the review quality improvements (per-requirement directives, LLM-first claims, edited claim carry-forward).

**Read before starting:**
- `docs/plans/2026-03-03-langgraph-pipeline/00-overview.md` — full migration overview
- `src/graph/state.py` — `ApplicationState` TypedDict (from Phase 0)
- `src/graph/parsers/proposal_parser.py` — `parse_reviewed_proposal` (from Phase 1)
- `src/graph/parsers/claim_builder.py` — `build_claim_text`, `_valid_evidence_ids` (from Phase 1)
- `src/graph/agents/base.py` — `AgentRunner` (from Phase 1)
- `src/graph/agents/matcher.py` — `run_matcher` (from Phase 1)
- `src/steps/ingestion.py` — existing ingest logic to wrap
- `src/steps/matching.py` — existing match + approve logic (being replaced)
- `src/utils/state.py` — `JobState` for path resolution
- `src/utils/comments.py` — `extract_comments_from_files`, `append_to_comment_log`
- `src/scraper/scrape_single_url.py` — `run_for_url`
- `src/scraper/generate_populated_tracker.py` — `regenerate_job_markdown`

## Objectives

1. Implement `ingest` node — wraps existing scraper, populates state
2. Implement `match` node — calls matcher agent with per-requirement revision directives, writes improved proposal
3. Implement `keywords` node — pure keyword extraction (split from matching)
4. Implement `review_gate` node — `interrupt()` to pause, parse edited proposal on resume, route forward or loop back
5. Wire the conditional edge: edited claims → loop to match, else → continue to motivate
6. All with proper comment extraction and artifact persistence

## What to do

### 1. Implement `src/graph/nodes/ingest.py`

```python
def ingest(state: ApplicationState) -> dict:
    """Scrape job posting and produce raw artifacts."""
```

- Create `JobState(state["job_id"], state["source"])`
- If `raw/raw.html` doesn't exist, error (URL handling stays in CLI for now)
- Call `regenerate_job_markdown()` from `src/scraper/generate_populated_tracker`
- Read `raw/extracted.json` and return `{"job_posting": extracted_dict}`
- Extract and log comments from `job.md`
- Write to disk: `raw/raw.html`, `raw/source_text.md`, `raw/extracted.json`, `job.md` (same as current `src/steps/ingestion.py`)

### 2. Implement `src/graph/nodes/match.py`

This is the most complex node. It replaces both `src/steps/matching.py::run()` and parts of `MatchProposalPipeline`.

```python
def match(state: ApplicationState) -> dict:
    """Generate match proposal from job + profile."""
```

**First run (review_round == 0):**
- Create `JobState`, load job posting and profile
- Call `run_matcher(runner, context)` from `src/graph/agents/matcher.py`
- Write `planning/match_proposal.md` using `write_proposal()` (see below)
- Return `{"evidence_items": [...], "requirement_mappings": [...], "proposal_path": str}`

**Regeneration (review_round > 0, reviewed_claims exist):**
- Archive existing proposal as `match_proposal.round{N}.md`
- Build **per-requirement revision directives** (THE KEY QUALITY FIX):

```python
def build_revision_directives(reviewed_claims: list[dict], comments: list[dict]) -> str:
    """Build structured per-requirement directives instead of a JSON dump."""
    lines = ["REVISION DIRECTIVES:\n"]
    for claim in reviewed_claims:
        req_id = claim["req_id"]
        decision = claim["decision"]
        notes = claim.get("notes", "")
        edited = claim.get("edited_claim", "")

        lines.append(f"### {req_id}: {decision.upper()}")
        if decision == "approved":
            lines.append(f"  Keep unchanged. Prior claim: {claim['claim_text']}")
        elif decision == "rejected":
            lines.append(f"  REMOVE this requirement from the proposal.")
        elif decision == "edited":
            if edited:
                lines.append(f"  User rewrote claim to: {edited}")
            if notes:
                # Strip <!-- --> delimiters from notes
                clean_notes = notes.replace("<!--", "").replace("-->", "").strip()
                lines.append(f"  User feedback: {clean_notes}")
            lines.append(f"  Regenerate evidence and claim incorporating the above feedback.")
        lines.append("")
    return "\n".join(lines)
```

This replaces the current `_build_matcher_input` which dumps the entire previous proposal + all comments as raw JSON. The new version gives the LLM clear, per-requirement instructions.

- Call `run_matcher(runner, context + revision_directives)`
- Invalidate `planning/reviewed_mapping.json` (delete if exists)
- Write new `planning/match_proposal.md` using `build_claim_text()` (LLM claims preferred)
- Return updated state

**Writing the proposal (`write_proposal` helper):**
- Use `build_claim_text(requirement_text, evidence_lines, llm_claim, edited_claim)` from `claim_builder.py`
- For approved claims: preserve prior claim text (same as current behavior)
- For edited/new claims: use `build_claim_text` priority chain
- For rejected claims: skip entirely (same as current behavior)

### 3. Implement `src/graph/nodes/keywords.py`

```python
def extract_keywords(state: ApplicationState) -> dict:
    """Extract keywords from requirement mappings. Pure function, no LLM."""
```

Move `_extract_keywords_from_proposal()` logic out of `src/steps/matching.py`. Instead of parsing a markdown file, operate on `state["requirement_mappings"]` directly:
- Extract keywords from requirement text (words > 3 chars)
- Infer categories (Programming, Technical, Education, Experience)
- Calculate match_strength as proportion of full/partial coverage
- Write `planning/keywords.json` to disk
- Return `{"keywords": {"keywords": [...], "categories": [...], "match_strength": float}}`

### 4. Implement `src/graph/nodes/review.py`

```python
def review_gate(state: ApplicationState) -> Command | dict:
    """Pause for human review, then parse decisions and route."""
```

**On first entry (before human review):**
- Call `interrupt({"proposal_path": state["proposal_path"], "review_round": state["review_round"]})`
- Graph pauses here. User edits `match_proposal.md` in Obsidian.

**On resume (after `Command(resume=True)`):**
- Parse the edited proposal via `parse_reviewed_proposal()` from `src/graph/parsers/proposal_parser.py`
- For claims with `decision == "edited"`: carry the `Edited Claim:` value forward in `reviewed_claims` (user's words take priority)
- Write `planning/reviewed_mapping.json`
- Log comments from the proposal
- Return `{"reviewed_claims": [...], "review_round": state["review_round"] + 1}`

**Routing (in `src/graph/pipeline.py`):**
```python
def after_review(state: ApplicationState) -> str:
    claims = state.get("reviewed_claims", [])
    has_edits = any(c["decision"] == "edited" for c in claims)
    if has_edits:
        return "match"      # loop back for regeneration
    return "motivate"        # continue forward
```

### 5. Update `src/graph/pipeline.py`

Replace the stubs for `ingest`, `match`, `keywords`, and `review_gate` with imports from the real node modules. Keep the other 5 nodes as stubs.

## What NOT to do

- Do NOT implement motivate, email, tailor_cv, render, or package — those are Phase 3
- Do NOT leave keyword extraction inside `src/steps/matching.py` — splitting this domain is mandatory
- Do NOT modify `src/cli/pipeline.py` — CLI integration is Phase 4
- Do NOT change the `ApplicationState` TypedDict (unless absolutely necessary, and document why)
- Do NOT add new Pydantic models
- Do NOT implement URL-based ingestion (fresh scrape from URL) — only regeneration from existing `raw/raw.html`. URL handling stays in CLI.

## Completion criteria

The phase is done when:
1. `src/graph/nodes/{ingest,match,keywords,review}.py` contain real implementations
2. The graph compiles and can be invoked through the first 4 nodes
3. **Review loop test**: invoke graph → pauses at review_gate → resume with edited decisions → routes back to match → re-pauses → resume with all approved → routes to motivate stub
4. **Per-requirement directives test**: verify that round 2 match receives structured per-requirement instructions (not a JSON dump)
5. **Claim priority test**: verify `build_claim_text` is used in proposal writing and that LLM claims take priority over templates
6. **Edited claim carry-forward test**: verify that when user writes `Edited Claim: my custom text`, that exact text appears in `reviewed_claims` and is passed to the next round
7. **Artifact persistence test**: verify `planning/match_proposal.md`, `planning/keywords.json`, `planning/reviewed_mapping.json` are written to disk
8. **Round archive test**: verify `match_proposal.round1.md` created on regeneration
9. All existing tests still pass: `pytest tests/ -x --ignore=tests/graph`
10. `pytest tests/graph/` all pass

## Commit

```
feat: implement core graph nodes (ingest, match, keywords, review)

- ingest node wraps existing scrapers, populates state with job_posting
- match node generates proposals with per-requirement revision directives
  (replaces flat JSON dump with structured feedback per requirement)
- keywords node extracts keywords from state (split from matching)
- review_gate uses interrupt() for human-in-the-loop editing
- Claim priority chain: user edit > LLM claim > template fallback
- Conditional routing: edited claims loop back to match, else continue
```

Update `changelog.md`:
```
## 2026-03-03 — LangGraph Pipeline Migration: Phase 2 (Core Nodes)

- Implemented `ingest` node wrapping existing scraper infrastructure.
- Implemented `match` node with per-requirement revision directives (replaces flat JSON dump of previous proposal + comments with structured per-requirement feedback).
- Improved claim text generation: priority chain is now user-edited claim > LLM-generated claim > template fallback (was: template only, ignoring LLM output).
- Split keyword extraction into standalone `keywords` node (was bolted onto matching).
- Implemented `review_gate` node using LangGraph `interrupt()` for human-in-the-loop review.
- Conditional routing after review: edited claims loop back to `match` for regeneration, approved/rejected continue forward.
- Edited claims now carry forward verbatim — user's `Edited Claim:` text takes priority over LLM regeneration.
- Added comprehensive tests for graph invocation, interrupt/resume cycle, regeneration loop, and claim priority.
```
