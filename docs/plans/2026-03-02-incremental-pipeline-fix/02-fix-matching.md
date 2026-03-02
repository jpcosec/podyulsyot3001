# Fix 2: Replace 3-Agent Gauntlet with Single Match + Human Review

## The Problem

The current `CVTailoringPipeline.execute()` runs three sequential LLM calls with no human input:

```
MATCHER (extract evidence, map requirements)
  → SELLER (propose stronger phrasing, pick top 6-10 reqs)
  → REALITY-CHECKER (veto/compress claims)
  → cv_tailoring.md (final, take-it-or-leave-it)
```

Problems with this:
1. **No feedback loop.** If the MATCHER misses your strongest qualification, every downstream step inherits that gap. You only see the damage in `cv_tailoring.md`, after 3 LLM calls.
2. **SELLER is an arbitrary filter.** It targets "top 6-10 requirements" — who decides what's top? The LLM does, with no input from you.
3. **REALITY-CHECKER vetoes too aggressively.** It rejects claims as "unsupported" when the evidence exists but was poorly extracted by the MATCHER.
4. **3 LLM calls for what should be 1 + human judgment.** The SELLER and CHECKER are proxies for human review. Replace the proxies with the actual human.

## The Fix

### New Flow

```
1. Single LLM MATCH call → produces requirement mapping + evidence catalog + gap analysis
2. Human reviews mapping in a markdown file → approves/edits/adds items
3. Pipeline reads approved mapping → drives CV render + motivation letter
```

### Step 1: Rewrite the matching step as a single comprehensive call

Replace the 3-agent prompt with one prompt that does:
- Extract ALL requirements from the full job description (not just alias-matched sections)
- Map each requirement to profile evidence with coverage assessment
- Identify gaps explicitly (requirements with no evidence)
- Propose claim text for each mapped requirement (one pass, not Seller→Checker)
- Tag confidence per claim (strong/moderate/weak) instead of inflation/risk theater

Output: `planning/match_proposal.md` — a human-reviewable markdown file.

### Step 2: Design the reviewable proposal format

`planning/match_proposal.md`:

```markdown
---
status: proposed  # proposed | reviewed | approved
job_id: 201084
generated: 2026-03-02T14:30:00Z
---

# Match Proposal: Research Assistant III-51/26

## Requirements Mapping

### R1: PhD or advanced degree in bioprocess engineering ✅ FULL
Evidence: MSc Chemical Engineering (UPLA, 2022), bioprocess coursework
Claim: "MSc in Chemical Engineering with specialization in bioprocess systems"
Confidence: strong
**Decision: [ ] approve  [ ] edit  [ ] reject**
Notes:

### R2: Experience with fermentation process control ⚠️ PARTIAL
Evidence: Airflow pipeline work (tangential), no direct fermentation
Claim: "Experience designing process control pipelines for production systems"
Confidence: weak
**Decision: [ ] approve  [ ] edit  [ ] reject**
Notes:

### R3: Python programming skills ✅ FULL
Evidence: 4 years Python, multiple projects, publications
Claim: "4+ years Python development including data pipelines and ML workflows"
Confidence: strong
**Decision: [ ] approve  [ ] edit  [ ] reject**
Notes:

## Gaps (no evidence found)

- G1: "Experience with bioreactor scale-up" — no matching profile entry
- G2: "Knowledge of GMP documentation" — not mentioned in profile

## Proposed Summary

> [Generated 3-4 sentence summary based on approved claims above]

**Edit summary here if needed:**

## Full Evidence Catalog

| ID | Type | Text | Source |
|----|------|------|--------|
| E1 | education | MSc Chemical Engineering, UPLA 2022 | profile |
| E2 | skill | Python, 4 years | profile |
| ... | ... | ... | ... |
```

The human edits this file:
- Check approve/edit/reject per requirement
- Edit claim text directly in the markdown
- Add notes explaining decisions
- Edit the summary
- Optionally add evidence the LLM missed

### Step 3: Parse the reviewed proposal

Add a parser that reads `match_proposal.md` after human review:
- Extract approved claims with their (possibly edited) text
- Extract rejected items (excluded from CV/letter)
- Extract the edited summary
- Build a `ReviewedMapping` model that downstream steps consume

```python
class ReviewedClaim(BaseModel):
    req_id: str
    decision: Literal["approved", "edited", "rejected"]
    claim_text: str  # may be human-edited
    evidence_ids: list[str]
    section: str  # summary, experience, education, etc.

class ReviewedMapping(BaseModel):
    job_id: str
    claims: list[ReviewedClaim]
    gaps: list[str]  # acknowledged gaps
    summary: str  # human-approved summary text
```

### Step 4: Update the CLI

```
# Step 1: Generate proposal (single LLM call)
python src/cli/pipeline.py match-propose 201084

# Step 2: Human edits planning/match_proposal.md in their editor

# Step 3: Parse and lock the reviewed mapping
python src/cli/pipeline.py match-approve 201084

# Steps 4+: CV render and motivation letter consume the approved mapping
python src/cli/pipeline.py cv-build 201084 english --via docx
python src/cli/pipeline.py motivation-build 201084
```

### Step 5: Backward compatibility

- `cv-tailor` command stays as an alias that runs the old 3-agent flow (deprecated)
- New `match-propose` / `match-approve` commands are the recommended path
- Both flows produce artifacts that `cv-build` and `motivation-build` can consume

## Files Changed

| File | Change |
|------|--------|
| `src/cv_generator/pipeline.py` | Add `MatchProposalPipeline` class (single LLM call, markdown output) |
| `src/cv_generator/pipeline.py` | Add `parse_reviewed_proposal()` function |
| `src/models/pipeline_contract.py` | Add `ReviewedClaim`, `ReviewedMapping` models |
| `src/prompts/cv_multi_agent.txt` | Rewrite as single matching prompt (keep old text in git history via tag) |
| `src/cli/pipeline.py` | Add `match-propose` and `match-approve` commands |

## Files NOT Changed

- `src/render/` — renderers consume the same CV model, don't care how claims were produced
- `src/utils/gemini.py` — transport unchanged
- `src/cv_generator/model.py` — CV data model unchanged

## Testing

1. Run `match-propose` on job 201084, verify `match_proposal.md` is readable and complete
2. Manually review and approve, run `match-approve`, verify `ReviewedMapping` parses correctly
3. Run `cv-build` consuming the reviewed mapping, verify CV reflects approved claims
4. Compare output quality: old 3-agent flow vs new single-match + human review

## Verification Results (2026-03-02)

### Live Testing on Job 201711
- ✅ Scraper produced 56-line `job.md` with full posting (vs. 46 lines filtered)
- ✅ `match-propose` extracted 8 requirements with evidence mapping
- ✅ `match-approve` parsed human-marked decisions and locked `reviewed_mapping.json`
- ✅ Parser accepts both `req_N` and `RN` heading formats

### Regex Enhancement
The heading pattern now accepts both formats:
- `### R1: requirement text [COVERAGE]` (original format)
- `### req_1: requirement text [COVERAGE]` (generator output format)

This provides flexibility while maintaining backward compatibility.
