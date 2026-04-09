# AGENTS.md — Agent Guidelines for Unified Automation

This file provides guidance for AI agents operating in this repository.

---

## 1. Build, Lint, and Test Commands

### Running Tests

```bash
# Run all unit tests (quiet mode)
python -m pytest tests/unit/automation/ -q

# Run all tests with verbose output
python -m pytest tests/unit/automation/ -v

# Run a specific test file
python -m pytest tests/unit/automation/motors/crawl4ai/test_compiler.py -v

# Run a specific test function
python -m pytest tests/unit/automation/ariadne/test_normalizer.py::test_normalize_builds_canonical_states_and_observations -v
```

### Running the Application

```bash
# Scrape jobs from a portal
python -m src.automation.main scrape --source <portal> --limit <count>

# Apply to a job (dry-run)
python -m src.automation.main apply --source <portal> --job-id <id> --cv <path> --dry-run

# Apply via BrowserOS backend
python -m src.automation.main apply --backend browseros --source <portal> --job-id <id> --cv <path>
```

---

## 2. Project Architecture

The project uses the **Ariadne Semantic Layer** to unify all browser automation:

- **`src/automation/ariadne/`**: Core "Brain" (Neutral Models & Logic)
  - `models.py`: Unified models for States, Tasks, Paths
  - `navigator.py`: State-aware replay logic
  - `normalizer.py`: Trace normalization
- **`src/automation/portals/`**: The "Map" of each portal
  - `maps/`: JSON files defining portal flows (AriadnePortalMap)
- **`src/automation/motors/`**: The "Engines" that execute actions
  - `crawl4ai/compiler/`: Translates Ariadne Paths to motor scripts
  - `browseros/`: Uses direct tool calls via MCP (Port 9200)

---

## 3. Code Style Guidelines

### Imports

```python
from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, Field, field_validator
```

- Always use `from __future__ import annotations` for forward references
- Group imports: stdlib → third-party → local
- Use type hints throughout

### Naming Conventions

- **Classes**: `PascalCase` (e.g., `AriadneNavigator`, `JobPosting`)
- **Functions/Methods**: `snake_case` (e.g., `find_current_state`, `get_next_step_index`)
- **Constants**: `UPPER_SNAKE_CASE` (e.g., `DEFAULT_TIMEOUT`)
- **Private methods**: Prefix with underscore (e.g., `_matches_predicate`)
- **Files**: `snake_case.py`

### Types

- Use Pydantic `BaseModel` for all data classes
- Use `Optional[T]` instead of `T | None` for Python 3.9 compatibility
- Use `List[T]`, `Dict[K, V]` from `typing` module
- Add docstrings to all public methods:

```python
def find_current_state(self, observation_results: Dict[str, bool]) -> Optional[str]:
    """Identifies the current state based on presence of elements.
    
    Args:
        observation_results: Mapping of selector/text to presence boolean.
        
    Returns:
        The ID of the matched state, or None if no state matches.
    """
```

### Pydantic Models

```python
class JobPosting(BaseModel):
    job_title: str = Field(..., description="The official job title")
    company_name: str = Field(..., description="Name of the company")
    salary: Optional[str] = Field(default=None, description="Estimated salary")

    @field_validator("job_id_pattern")
    @classmethod
    def must_be_valid_regex(cls, v: str) -> str:
        re.compile(v)
        return v
```

### Error Handling

- Use custom exceptions in `ariadne/exceptions.py`
- Raise specific exceptions with clear messages
- Use logging for debugging:

```python
logger = logging.getLogger(__name__)

logger.info("Semantic Recovery: Detected state '%s'", current_state_id)
logger.debug("Step %d completed", step_index)
```

### Enumerations

```python
class EventType(str, Enum):
    NAVIGATE = "navigate"
    CLICK = "click"
    FILL = "fill"
    UPLOAD = "upload"
```

---

## 4. Development Principles

1. **Ariadne First**: Every new portal/flow MUST start as an `AriadnePortalMap` in JSON. Never hardcode logic into motor-specific adapters.

2. **Backend Neutrality**: Define actions as `AriadneIntent` (CLICK, FILL, UPLOAD) rather than backend-specific tool calls.

3. **States & Transitions**: Use `AriadneState` to define logical rooms (e.g., "Resume Modal") for state-aware recovery.

4. **Semantic Targets**: Every `AriadneTarget` should contain both `css` (for Crawl4AI) and `text` (for BrowserOS).

---

## 5. Key Files

- `src/automation/main.py` — CLI entry point
- `src/automation/ariadne/models.py` — Core data models
- `src/automation/ariadne/navigator.py` — State-aware navigation
- `src/automation/portals/*/routing.py` — Portal-specific routing

---

## 6. Testing Guidelines

- Tests go in `tests/unit/automation/` mirroring the `src/` structure
- Use pytest with type hints in test signatures
- Test file naming: `test_*.py`
- Test function naming: `test_*` with descriptive names

---

## 7. Troubleshooting

- **RuntimeError: already submitted**: Delete `apply_meta.json` in the job's artifact directory
- **Compilation Errors**: Check `src/automation/motors/crawl4ai/compiler/` and portal map JSON
- **Motor Failures**: Inspect logs under `logs/`