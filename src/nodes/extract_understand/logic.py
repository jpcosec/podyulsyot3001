"""Extraction node logic using prompt manager and LLM runtime."""

from __future__ import annotations

import os
from typing import Any, Mapping

from src.ai.prompt_manager import PromptManager
from src.ai.runtime import LLMRuntime
from src.nodes.extract_understand.contract import JobUnderstandingExtract


def run_logic(state: Mapping[str, Any]) -> dict[str, Any]:
    """Transform raw job text into structured extraction output."""
    node_data = _build_node_data(state)

    prompt_manager = PromptManager(base_path="src/nodes")
    model_name = os.getenv("PHD2_GEMINI_MODEL", "gemini-2.5-flash")
    runtime = LLMRuntime(model_name=model_name)

    system_prompt, user_prompt = prompt_manager.build_prompt(
        "extract_understand", node_data
    )

    result = runtime.generate_structured(
        system_prompt=system_prompt,
        user_prompt=user_prompt,#TODO: We are missing crucial extra info here such as job description!!, 
        output_schema=JobUnderstandingExtract,
    )

    return {
        **dict(state),
        "extracted_data": result.model_dump(),
    }


def _build_node_data(state: Mapping[str, Any]) -> dict[str, Any]:#TODO: isn't this automatic from the pydantic data?
    job_id = state.get("job_id")
    if not isinstance(job_id, str) or not job_id.strip():
        raise ValueError("state.job_id is required")

    ingested_data = state.get("ingested_data")
    raw_text = None
    if isinstance(ingested_data, Mapping):
        raw_text = ingested_data.get("raw_text")

    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("state.ingested_data.raw_text is required")

    active_feedback = state.get("active_feedback", [])
    if not isinstance(active_feedback, list):
        raise ValueError("state.active_feedback must be a list")

    return {
        "job_id": job_id,
        "source_text_md": raw_text,
        "active_feedback": active_feedback,
    }
