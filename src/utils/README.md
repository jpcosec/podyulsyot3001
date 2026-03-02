# Utils Module

Centralized utilities, configuration, and orchestration modules for the CV pipeline.

## Core Modules

### Configuration & State
- **`config.py`** — `CVConfig` dataclass (project root, profile root, pipeline root)
- **`state.py`** — `JobState` class (unified job path authority, artifact I/O, step tracking)

### CV Data & Loading
- **`model.py`** — CV data models (`CVModel`, `ContactInfo`, `EducationEntry`, etc.)
- **`loaders/profile_loader.py`** — profile JSON loading utilities

### Pipeline Orchestration
- **`pipeline.py`** — multi-agent pipelines (`CVTailoringPipeline`, `MatchProposalPipeline`)
- **`ats.py`** — ATS dual-engine (code 0.6 weight + Gemini LLM 0.4 weight)
- **`cv_rendering.py`** — rendering orchestration (rendering functions, output path resolution)

### Supporting Utilities
- **`loader.py`** — JSON/YAML/file loading helpers
- **`comments.py`** — inline HTML comment extraction and logging
- **`gemini.py`** — `GeminiClient` wrapper (google-genai SDK)
- **`pdf_merger.py`** — merge and compress PDF bundles
- **`build_backup_compendium.py`** — regenerate backup manifest
- **`nlp/text_analyzer.py`** — spaCy-based text analysis (fallback ATS)

## Usage Examples

```bash
# PDF utilities
python src/utils/pdf_merger.py -o Final_Application.pdf <file1.pdf> <file2.pdf>
python src/utils/build_backup_compendium.py

# Direct pipeline imports
from src.utils.pipeline import CVTailoringPipeline, MatchProposalPipeline
from src.utils.config import CVConfig
from src.utils.model import CVModel
from src.utils.loaders import load_base_profile
from src.utils.ats import run_ats_analysis
```

Manifest output:
- `data/reference_data/backup/backup_compendium.json`
