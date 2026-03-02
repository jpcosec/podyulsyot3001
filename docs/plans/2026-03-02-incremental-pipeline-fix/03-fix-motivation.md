# Fix 3: Feed Full Context to Motivation Letter

## The Problem

The motivation letter LLM call currently receives:
- Extracted requirements from `extracted.json` (filtered by alias matching)
- Atomic evidence items (flattened profile facts)
- A pre-letter scaffold (if generated)

It never sees:
- The full job posting text (research group context, project description, "what we offer")
- The human-reviewed matching decisions (what you chose to emphasize and why)
- The actual CV being submitted (so the letter can complement rather than repeat it)

The result is a generic letter that could be about any job, because the LLM is writing about a job it hasn't fully read, for a candidate it only knows through atomic facts.

## The Fix

### Step 1: Build a rich context payload for the motivation letter

After Fix 1 (full source text available) and Fix 2 (human-reviewed mapping available), the motivation letter has access to everything it needs. Wire it up:

```python
def build_motivation_context(job_dir: Path, profile: dict) -> dict:
    return {
        "full_job_description": (job_dir / "raw" / "source_text.md").read_text(),
        "job_metadata": load_job_metadata(job_dir / "job.md"),  # structured fields
        "reviewed_mapping": load_reviewed_mapping(job_dir / "planning"),
        "approved_claims": [c for c in mapping.claims if c.decision != "rejected"],
        "acknowledged_gaps": mapping.gaps,
        "candidate_summary": mapping.summary,  # human-approved
        "candidate_profile": profile,
        "cv_content": (job_dir / "cv" / "to_render.md").read_text(),  # actual CV
    }
```

Key additions vs current:
- `full_job_description`: the complete job posting, not filtered excerpts
- `reviewed_mapping`: what the human decided matters, including their notes
- `acknowledged_gaps`: explicit gaps the letter should address or avoid
- `cv_content`: the actual CV, so the letter complements it

### Step 2: Update the motivation letter prompt

Modify `src/prompts/motivation_letter.txt` to use the richer context:

Add instructions:
```
You have the FULL job description. Use specific details from it:
- Reference the research group or PI by name if mentioned
- Reference the specific project or research topic
- Reference what the position offers (not just what it requires)

You have the candidate's REVIEWED MAPPING with human decisions:
- Focus on claims marked "approved" — these are the candidate's chosen emphasis
- For gaps marked "acknowledged" — do not fabricate coverage, but you may briefly
  address them as areas of growth if appropriate
- The candidate's approved summary reflects their self-positioning — align with it

You have the ACTUAL CV being submitted:
- Do not repeat CV bullet points verbatim in the letter
- The letter should add narrative and motivation that the CV cannot convey
- Reference specific CV entries by connecting them to the job's research context
```

### Step 3: Kill the two-stage pre-letter flow

The current flow is: `motivation-pre` (scaffold) → `motivation-build` (expand scaffold).

This was needed because the single-stage letter had too little context and produced garbage. With full context now available, one well-informed LLM call produces a better letter than two poorly-informed calls.

Replace with:
```
python src/cli/pipeline.py motivation-build 201084
```

This single command:
1. Loads full context (source text + reviewed mapping + CV)
2. Calls LLM once with the rich context
3. Produces `planning/motivation_letter.md`

The `motivation-pre` command becomes deprecated (kept as alias that prints a deprecation notice).

### Step 4: Wire motivation to reviewed mapping

The motivation letter must require an approved matching before it can run:

```python
def run_motivation_build(job_id, source, ...):
    reviewed_path = job_dir / "planning" / "match_proposal.md"
    if not reviewed_path.exists():
        raise FileNotFoundError("Run match-propose first")

    mapping = parse_reviewed_proposal(reviewed_path)
    if mapping.status != "approved":
        raise ValueError("Review and approve the match proposal first (match-approve)")

    context = build_motivation_context(job_dir, profile)
    # ... generate letter with full context
```

This enforces the human-in-the-loop: no letter gets generated from an unreviewed mapping.

## Files Changed

| File | Change |
|------|--------|
| `src/cli/pipeline.py` | Update `run_motivation_build()` to use rich context + require approved mapping |
| `src/prompts/motivation_letter.txt` | Add instructions for using full job description, reviewed mapping, and CV content |
| `src/motivation_letter/__init__.py` | Update context assembly (or inline into CLI if the module is thin enough) |

## Files Deleted

| File | Reason |
|------|--------|
| `src/prompts/motivation_pre_letter.txt` | Already deleted in previous commit; pre-letter flow replaced by single rich call |

## Files NOT Changed

- `src/render/` — motivation letter rendering is separate from CV rendering
- `src/models/` — `MotivationLetterOutput` contract stays the same
- `src/utils/gemini.py` — transport unchanged

## Testing

1. Run the full new flow on job 201084:
   - `match-propose` → edit proposal → `match-approve` → `motivation-build`
2. Compare letter quality: old (filtered context, 2-stage) vs new (full context, 1-stage)
3. Verify the letter references specific details from the full job posting
4. Verify the letter doesn't repeat CV bullet points verbatim
5. Verify the letter addresses or avoids acknowledged gaps appropriately

## End State

After all three fixes, the application flow is:

```
1. fetch-url <url>           → raw/source_text.md + raw/extracted.json + job.md
2. match-propose <job_id>    → planning/match_proposal.md (LLM, uses full source text)
3. [human reviews and edits match_proposal.md]
4. match-approve <job_id>    → locks reviewed mapping
5. cv-build <job_id>         → CV from approved claims
6. motivation-build <job_id> → letter from full context + reviewed mapping + CV
```

Each step has a clear input, a clear output, and a human checkpoint where it matters most.
