# Step 04 — Fix Multi-Agent CV Pipeline

## Goal
Rewrite `CVMultiAgentPipeline` in `src/cv_generator/pipeline.py` to use the full prompt files from `src/prompts/`, Pydantic models for structured output, and proper error handling. Replace the `cv-tailor` CLI command (which uses hardcoded `CV_RULES` and `build_cv_tailoring()`) with this pipeline. Delete all hardcoded CV content from `src/cli/pipeline.py`.

## Depends on
- **01-pydantic-models** — uses `PipelineState`, `EvidenceItem`, `ProposedClaim`
- **02-prompts-to-src** — loads prompts via `load_prompt()`

## Files to Read First
- `src/cv_generator/pipeline.py` — current `CVMultiAgentPipeline` (understand what exists)
- `src/prompts/cv_multi_agent.txt` — the full 4-agent prompt specification (after step 02 moves it)
- `src/prompts/cv_renderer.txt` — renderer agent prompt
- `src/models/pipeline_contract.py` — `PipelineState` and related models (after step 01)
- `src/cli/pipeline.py` — `CV_RULES`, `build_cv_tailoring()`, `render_job_cv_body()`, `render_job_cv_main()` (code to delete)
- `src/utils/gemini.py` — `GeminiClient` (use this, not raw `genai`)

## Files to Modify

### `src/cv_generator/pipeline.py` — REWRITE
Replace the existing `CVMultiAgentPipeline` class. Key changes:

1. **Use `GeminiClient`** instead of raw `genai.configure()` + `genai.GenerativeModel()`.
2. **Load full prompts from files** instead of inline 1-sentence summaries.
3. **Use `PipelineState` Pydantic model** as `response_schema` for structured output.
4. **Extract agent-specific prompts** from the multi-agent prompt file by section markers.
5. **Validate each step's output** with Pydantic before passing to the next step.

```python
"""Multi-agent CV tailoring pipeline: MATCHER → SELLER → REALITY-CHECKER."""

import json
import logging
from pathlib import Path

from src.models.pipeline_contract import PipelineState, EvidenceItem
from src.models.job import JobPosting
from src.prompts import load_prompt
from src.utils.gemini import GeminiClient
from src.cv_generator.config import CVConfig
from src.cv_generator.loaders.profile_loader import load_base_profile
from src.cv_generator.model import CVModel

logger = logging.getLogger(__name__)


class CVTailoringPipeline:
    """Runs MATCHER → SELLER → REALITY-CHECKER to produce tailored CV claims."""

    AGENT_SECTIONS = {
        "matcher": "AGENT 1 — MATCHER",
        "seller": "AGENT 2 — SELLER",
        "checker": "AGENT 3 — REALITY-CHECKER",
    }

    def __init__(self, config: CVConfig | None = None):
        self.config = config or CVConfig.from_defaults()
        self.gemini = GeminiClient()
        self.full_prompt = load_prompt("cv_multi_agent")

    def _extract_agent_prompt(self, agent_key: str) -> str:
        """Extract a single agent's prompt section from the full prompt file."""
        ...

    def _build_initial_context(
        self, job: JobPosting, profile: dict, model: CVModel
    ) -> str:
        """Build the input data string for the MATCHER step."""
        ...

    def run_step(self, agent_key: str, input_data: str) -> PipelineState:
        """Run one agent step, validate output as PipelineState."""
        prompt = self._extract_agent_prompt(agent_key)
        full_input = f"SYSTEM INSTRUCTIONS:\n{prompt}\n\nINPUT DATA:\n{input_data}"
        response = self.gemini.generate(full_input)
        return PipelineState.model_validate_json(response)

    def execute(
        self,
        job_id: str,
        source: str = "tu_berlin",
    ) -> PipelineState:
        """Run the full MATCHER → SELLER → CHECKER pipeline.

        Returns the final PipelineState with approved/rejected claims.
        Writes intermediate outputs to cv/pipeline_intermediates/.
        """
        # 1. Load job + profile
        job_dir = self.config.pipeline_root / source / job_id
        job_posting = ...  # Load from job.md / summary.json → JobPosting
        profile = load_base_profile(self.config.profile_path())
        model = CVModel.from_profile(profile)

        # 2. Build initial context
        context = self._build_initial_context(job_posting, profile, model)

        # 3. MATCHER
        logger.info("Running MATCHER...")
        matcher_state = self.run_step("matcher", context)
        self._save_intermediate(job_dir, "01_matcher.json", matcher_state)

        # 4. SELLER
        logger.info("Running SELLER...")
        seller_state = self.run_step("seller", matcher_state.model_dump_json(indent=2))
        self._save_intermediate(job_dir, "02_seller.json", seller_state)

        # 5. REALITY-CHECKER
        logger.info("Running REALITY-CHECKER...")
        final_state = self.run_step("checker", seller_state.model_dump_json(indent=2))
        self._save_intermediate(job_dir, "03_reality_checker.json", final_state)

        # 6. Write tailoring summary
        self._write_tailoring_md(job_dir, final_state)

        return final_state

    def _save_intermediate(self, job_dir: Path, filename: str, state: PipelineState):
        """Save pipeline intermediate to cv/pipeline_intermediates/."""
        out_dir = job_dir / "cv" / "pipeline_intermediates"
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / filename).write_text(state.model_dump_json(indent=2), encoding="utf-8")

    def _write_tailoring_md(self, job_dir: Path, state: PipelineState):
        """Write planning/cv_tailoring.md from approved claims."""
        planning_dir = job_dir / "planning"
        planning_dir.mkdir(parents=True, exist_ok=True)
        # Generate markdown from state.proposed_claims where status == "approved"
        ...
```

### `src/cli/pipeline.py` — DELETE hardcoded code

**Delete these functions entirely:**
- `render_job_cv_body()` — hardcoded LaTeX CV body
- `render_job_cv_main()` — hardcoded LaTeX CV header
- `ensure_job_cv_sources()` — writes hardcoded LaTeX files

**Delete this constant:**
- `CV_RULES` — hardcoded keyword-matching rules

**Rewrite `build_cv_tailoring()`:**
Replace the hardcoded keyword matching + "Suggested CV Actions" with a call to `CVTailoringPipeline.execute()`.

```python
# Before: 50+ lines of hardcoded keyword matching and fixed suggestions
def build_cv_tailoring(job_id, source="tu_berlin"):
    ...CV_RULES loop...
    ...hardcoded "Suggested CV Actions"...

# After: delegate to the pipeline
def build_cv_tailoring(job_id: str, source: str = "tu_berlin"):
    from src.cv_generator.pipeline import CVTailoringPipeline
    pipeline = CVTailoringPipeline()
    pipeline.execute(job_id=job_id, source=source)
```

## Specification

### Prompt Extraction Strategy
The full `cv_multi_agent.txt` prompt contains 4 agent sections separated by headers like `AGENT 1 — MATCHER`. The `_extract_agent_prompt()` method splits the text at these headers and returns the relevant section. This preserves all the detailed instructions, hard constraints, and schema requirements from the original prompt file.

### Why Rename to `CVTailoringPipeline`
- `CVMultiAgentPipeline` is vague — "multi-agent" doesn't describe what it does
- `CVTailoringPipeline` is descriptive — it tailors a CV for a specific job
- The class name matches the CLI command: `cv-tailor`

### Intermediate Output Location
- Before: `output_dir/pipeline_intermediates/` (arbitrary)
- After: `<job_dir>/cv/pipeline_intermediates/` (under the job's cv directory)

### What Gets Deleted from `src/cli/pipeline.py`
These are the hardcoded pieces that the agent replaces:

| Function/Constant | Lines (approx) | Why delete |
|---|---|---|
| `CV_RULES` | ~8 entries | Agent does semantic matching, not keyword regex |
| `render_job_cv_body()` | ~100 lines | Hardcoded LaTeX with personal dates/orgs |
| `render_job_cv_main()` | ~50 lines | Hardcoded name/email/phone in LaTeX |
| `ensure_job_cv_sources()` | ~20 lines | Wrote hardcoded LaTeX files to disk |
| `build_cv_tailoring()` body | ~50 lines | Replaced by pipeline call |

Total: ~230 lines of hardcoded content removed.

## Verification
```bash
cd /home/jp/phd

# 1. Pipeline class imports
python -c "
from src.cv_generator.pipeline import CVTailoringPipeline
p = CVTailoringPipeline()
assert hasattr(p, 'execute')
assert hasattr(p, 'run_step')
assert hasattr(p, 'gemini')
print('CVTailoringPipeline importable and has expected methods.')
"

# 2. Hardcoded code is gone
python -c "
import inspect
from src.cli import pipeline as cli_pipeline

# These should NOT exist anymore
for name in ['render_job_cv_body', 'render_job_cv_main', 'ensure_job_cv_sources', 'CV_RULES']:
    assert not hasattr(cli_pipeline, name), f'{name} should be deleted'

# build_cv_tailoring should still exist but be a thin wrapper
assert hasattr(cli_pipeline, 'build_cv_tailoring')
print('Hardcoded functions deleted, build_cv_tailoring still exists.')
"

# 3. Prompt loading works
python -c "
from src.cv_generator.pipeline import CVTailoringPipeline
p = CVTailoringPipeline()
prompt = p._extract_agent_prompt('matcher')
assert 'MATCHER' in prompt
assert len(prompt) > 200  # Full prompt, not 1-sentence summary
print('Full prompt loaded from file.')
"
```

## Done Criteria
- [ ] `CVTailoringPipeline` in `src/cv_generator/pipeline.py` loads full prompts from `src/prompts/cv_multi_agent.txt`
- [ ] Pipeline uses `PipelineState` Pydantic model for structured output
- [ ] Pipeline uses `GeminiClient` (not raw `genai`)
- [ ] `render_job_cv_body()`, `render_job_cv_main()`, `ensure_job_cv_sources()` deleted from `src/cli/pipeline.py`
- [ ] `CV_RULES` constant deleted from `src/cli/pipeline.py`
- [ ] `build_cv_tailoring()` in `src/cli/pipeline.py` delegates to `CVTailoringPipeline.execute()`
- [ ] Intermediate outputs written to `<job_dir>/cv/pipeline_intermediates/`
- [ ] Tailoring summary written to `<job_dir>/planning/cv_tailoring.md`
- [ ] Verification script exits 0
