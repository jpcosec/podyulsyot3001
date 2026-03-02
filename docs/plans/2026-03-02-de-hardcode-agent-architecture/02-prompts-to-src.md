# Step 02 — Move Prompts to src/ and Create Loader

## Goal
Move all prompt files from `data/reference_data/prompts/` into `src/prompts/`, create a loader utility, add new prompt templates for email draft and pre-letter planning, and delete the duplicate `AST.md`. After this step, every agent in the system loads its prompt through `src/prompts/`.

## Depends on
Nothing — can start immediately.

## Files to Read First
- `data/reference_data/prompts/` — all 5 files (understand content and naming)
- `src/motivation_letter/service.py` — see how `PROMPT_RELATIVE_PATH` is used (line ~20) and how `build_prompt()` injects `{{CONTEXT_JSON}}`
- `src/cv_generator/ats.py` — see `load_ats_prompt()` function (loads from `data/reference_data/prompts/`)
- `src/cv_generator/pipeline.py` — see line ~155 where the prompts path is commented out

## Files to Create

### `src/prompts/__init__.py`
Prompt loader utility.

```python
from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent

def load_prompt(name: str) -> str:
    """Load a prompt file by name (without extension).

    Usage: load_prompt("cv_multi_agent") -> reads cv_multi_agent.txt
    """
    path = _PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")

def load_prompt_with_context(name: str, context_json: str) -> str:
    """Load a prompt and inject context at {{CONTEXT_JSON}} placeholder."""
    template = load_prompt(name)
    if "{{CONTEXT_JSON}}" not in template:
        raise ValueError(f"Prompt '{name}' has no {{{{CONTEXT_JSON}}}} placeholder")
    return template.replace("{{CONTEXT_JSON}}", context_json)
```

### Prompt Files (moved and renamed)

| Source | Destination | Notes |
|---|---|---|
| `Academic_ATS_Prompt_Architecture.txt` | `src/prompts/ats_evaluation.txt` | Unchanged content |
| `Academic_Motivation_Letter_Prompt.txt` | `src/prompts/motivation_letter.txt` | Unchanged content |
| `Academic_CV_MultiAgent_Pipeline_Prompts.txt` | `src/prompts/cv_multi_agent.txt` | Unchanged content |
| `Academic_CV_Renderer_Agent_Prompt.txt` | `src/prompts/cv_renderer.txt` | Unchanged content |
| `AST.md` | **DELETE** | Duplicate of ats_evaluation |

### New Prompt Files

#### `src/prompts/email_draft.txt`
Extract the email generation logic from `service.py:generate_email_draft()` into a prompt. The agent generates the email instead of hardcoded string concatenation.

```
EMAIL DRAFT GENERATION SPECIFICATION

ROLE
You generate a brief, professional application email for a German university research position.
The email accompanies a motivation letter and CV as attachments.

INPUT
You receive a JSON context with:
- job: title, reference_number, contact_name, contact_email, institution
- candidate: name, email, phone, summary

RULES
1. Subject line must include the reference number when available.
2. Use "Dear [contact_name]," or "Dear Hiring Committee," as salutation.
3. Body is exactly 2 short paragraphs:
   - Paragraph 1: State the position, mention attachments (motivation letter, CV, supporting documents), mention Berlin availability.
   - Paragraph 2: One sentence on alignment, one on degree equivalency evidence, one expressing interest in discussion.
4. Sign with candidate name, email, phone.
5. Total body: 60-100 words.
6. Do not invent facts not present in the context.

OUTPUT CONTRACT (JSON ONLY)
{
  "to": "string",
  "subject": "string",
  "salutation": "string",
  "body": "string",
  "closing": "Best regards,",
  "sender_name": "string",
  "sender_email": "string",
  "sender_phone": "string"
}

{{CONTEXT_JSON}}
```

#### `src/prompts/motivation_pre_letter.txt`
Replace the hardcoded `_build_section_plan()` and `_render_pre_letter()` with an agent-driven planning step.

```
MOTIVATION LETTER PRE-PLANNING SPECIFICATION

ROLE
You are a motivation letter planner for German university research positions.
You analyze a job posting against a candidate profile and produce a structured section plan
with evidence references. You do NOT write the final letter — only the plan.

INPUT
You receive a JSON context with:
- job: title, requirements (must/nice), responsibilities, themes
- candidate: profile data including experience, education, publications, skills
- evidence_catalog: list of atomic evidence items with IDs

TASKS
1. Identify the 5-8 strongest requirement-evidence alignments.
2. Assign evidence to 5 letter sections:
   - hook_alignment: 2-3 evidence IDs that establish immediate role fit
   - formal_eligibility: evidence for degree equivalency, language, mobility
   - technical_match: 3-5 evidence IDs for core technical requirements
   - project_motivation: 2-4 evidence IDs linking to the research project specifically
   - closing: 1-2 evidence IDs for team/communication fit
3. For each section, write a 1-sentence planning note describing the angle.
4. Flag any requirements with no matching evidence as gaps.

RULES
1. Only reference evidence IDs that exist in the evidence_catalog.
2. Do not invent evidence. If coverage is weak, flag it as a gap.
3. Prefer must-priority requirements over nice-to-have.
4. Each evidence ID should appear in at most 2 sections.

OUTPUT CONTRACT (JSON ONLY)
{
  "sections": {
    "hook_alignment": {"evidence_ids": ["E1"], "planning_note": "string"},
    "formal_eligibility": {"evidence_ids": ["E2"], "planning_note": "string"},
    "technical_match": {"evidence_ids": ["E3"], "planning_note": "string"},
    "project_motivation": {"evidence_ids": ["E4"], "planning_note": "string"},
    "closing": {"evidence_ids": ["E5"], "planning_note": "string"}
  },
  "gaps": [{"requirement": "string", "severity": "critical|minor"}],
  "recommended_tone": "string",
  "word_target": 400
}

{{CONTEXT_JSON}}
```

## Files to Modify

### `src/cv_generator/ats.py`
Change `load_ats_prompt()` to use the new loader:
```python
# Before:
prompt_path = project_root / "data" / "reference_data" / "prompts" / "Academic_ATS_Prompt_Architecture.txt"

# After:
from src.prompts import load_prompt
prompt_text = load_prompt("ats_evaluation")
```

### `src/motivation_letter/service.py`
Change `PROMPT_RELATIVE_PATH` and `build_prompt()` to use the new loader:
```python
# Before:
PROMPT_RELATIVE_PATH = "data/reference_data/prompts/Academic_Motivation_Letter_Prompt.txt"
self.prompt_path = prompt_path or self.config.project_root / PROMPT_RELATIVE_PATH

# After:
from src.prompts import load_prompt_with_context
# In build_prompt():
return load_prompt_with_context("motivation_letter", context_json)
```

### `src/cv_generator/pipeline.py`
Change `execute_pipeline()` to load the full prompt from file:
```python
# Before (line ~155, commented out):
# prompts_path=str(cfg.project_root / "data" / "reference_data" / "prompts" / "Academic_CV_MultiAgent_Pipeline_Prompts.txt"),

# After:
from src.prompts import load_prompt
full_prompt = load_prompt("cv_multi_agent")
```

## Files to Delete
- `data/reference_data/prompts/AST.md` (duplicate of ATS prompt)

## What Happens to `data/reference_data/prompts/`
The original files stay in place temporarily (other scripts may reference them). They will be removed in the closure step after all references are verified to point to `src/prompts/`.

## Specification

### Why Move Prompts?
- Prompts are **code behavior** — they define what agents do. They belong next to code, not next to data.
- `src/prompts/` is importable via `Path(__file__)` — no dependency on `CVConfig` or project root resolution.
- Co-location makes it obvious which prompts exist and which code uses them.

### Naming Convention
- Lowercase, underscores, no `Academic_` prefix (redundant in this project)
- `.txt` extension (not `.md`) — these are prompt specifications, not documentation

### Loader Design
- `load_prompt(name)` — simple file read, raises `FileNotFoundError` if missing
- `load_prompt_with_context(name, json)` — reads + injects context at `{{CONTEXT_JSON}}`
- No caching, no templating engine — just `str.replace()`. Keep it simple.

## Verification
```bash
cd /home/jp/phd

# 1. Loader works
python -c "
from src.prompts import load_prompt, load_prompt_with_context
p = load_prompt('ats_evaluation')
assert 'Academic Pre-Screening' in p
assert len(p) > 500

p2 = load_prompt('cv_multi_agent')
assert 'MATCHER' in p2

p3 = load_prompt_with_context('motivation_letter', '{\"test\": true}')
assert '{\"test\": true}' in p3
assert '{{CONTEXT_JSON}}' not in p3

p4 = load_prompt('email_draft')
assert '{{CONTEXT_JSON}}' in load_prompt('email_draft')

p5 = load_prompt('motivation_pre_letter')
assert 'hook_alignment' in p5

print('All prompt loader tests passed.')
"

# 2. ATS still loads prompt correctly
python -c "
from src.cv_generator.ats import load_ats_prompt
prompt = load_ats_prompt()
assert 'Academic Pre-Screening' in prompt
print('ATS prompt loading works.')
"

# 3. AST.md is deleted
python -c "
from pathlib import Path
assert not (Path('data/reference_data/prompts/AST.md')).exists(), 'AST.md should be deleted'
print('AST.md deleted.')
"
```

## Done Criteria
- [ ] `src/prompts/__init__.py` — `load_prompt()` and `load_prompt_with_context()` work
- [ ] All 6 prompt files exist in `src/prompts/`: `ats_evaluation.txt`, `motivation_letter.txt`, `cv_multi_agent.txt`, `cv_renderer.txt`, `email_draft.txt`, `motivation_pre_letter.txt`
- [ ] `src/cv_generator/ats.py` uses `load_prompt("ats_evaluation")`
- [ ] `src/motivation_letter/service.py` uses `load_prompt_with_context("motivation_letter", ...)`
- [ ] `src/cv_generator/pipeline.py` uses `load_prompt("cv_multi_agent")`
- [ ] `data/reference_data/prompts/AST.md` deleted
- [ ] Verification script exits 0
