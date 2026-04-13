---
type: pattern
domain: architecture
source: src/automation/ariadne/config.py:1
---

# Pill: Structured Output Pattern (VLM/LLM)

## Pattern
Use Gemini Flash with Pydantic models to force deterministic structured outputs for mission resolution or data extraction.

## Implementation
```python
from pydantic import BaseModel, Field
from src.automation.ariadne.config import get_gemini_model
from langchain_google_genai import ChatGoogleGenerativeAI

class MyResolution(BaseModel):
    id: str = Field(description="The exact ID from the map")
    is_valid: bool = Field(description="True if the intent matches")

# Initialize LLM with structured output
llm = ChatGoogleGenerativeAI(model=get_gemini_model()).with_structured_output(MyResolution)

# Invoke
try:
    resolution = await llm.ainvoke("Analyze this: ...")
    print(resolution.id)
except Exception as e:
    # Always have a fallback for LLM failures
    resolution = MyResolution(id="default", is_valid=False)
```

## When to use
Use in `interpreter.py` for intent mapping and `agent.py` for tool selection.

## Verify
Test with invalid inputs to ensure the fallback logic triggers.
