"""Extraction node logic using LangChain structured output."""

from __future__ import annotations

import os
import re
import importlib
from contextlib import nullcontext
from typing import Any, Mapping

from src.ai.llm_runtime import LLMRuntimeDependencyError, LLMRuntimeResponseError
from src.ai.prompt_manager import PromptManager
from src.nodes.extract_understand.contract import ContactInfo, JobUnderstandingExtract

EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.IGNORECASE)
SALARY_RE = re.compile(
    r"\b(?:E\s?\d{1,2}[A-Z]?|TV-L\s*E\s?\d{1,2}[A-Z]?|salary\s+grade\s+\d{1,2}[A-Z]?|Entgeltgruppe\s+\d{1,2}[A-Z]?)\b",
    re.IGNORECASE,
)
NAME_RE = re.compile(
    r"(?:Prof\.?\s*)?(?:Dr\.?\s*)?(?:[A-Z][A-Za-z'`.-]+(?:\s+[A-Z][A-Za-z'`.-]+){1,4})"
)


def run_logic(state: Mapping[str, Any]) -> dict[str, Any]:
    """Transform raw job text into structured extraction output."""
    node_data = _build_node_data(state)
    result = _run_langchain_extraction(node_data)
    enriched = _enrich_extraction_result(result, node_data["source_text_md"])
    return {
        **dict(state),
        "extracted_data": enriched.model_dump(),
    }


def _run_langchain_extraction(node_data: dict[str, Any]) -> JobUnderstandingExtract:
    prompt_value = _build_prompt_value(node_data)
    llm = _build_structured_llm()
    try:
        with _langsmith_trace_context(node_data):
            response = llm.invoke(prompt_value)
    except Exception as exc:  # noqa: BLE001
        raise LLMRuntimeResponseError("langchain structured extraction failed") from exc

    try:
        return JobUnderstandingExtract.model_validate(response)
    except Exception as exc:  # noqa: BLE001
        raise LLMRuntimeResponseError(
            "langchain response failed schema validation"
        ) from exc


def _build_prompt_value(node_data: dict[str, Any]) -> Any:
    manager = PromptManager(base_path="src/nodes")
    system_prompt = manager.load_template("extract_understand", "system")
    user_template = manager.load_template("extract_understand", "user_template")

    ChatPromptTemplate = _load_chat_prompt_template()
    chat_prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_template),
        ]
    )
    prompt_value = chat_prompt.invoke(node_data)

    rendered_user = _extract_human_message(prompt_value)
    manager._validate_xml_tags(rendered_user, ("input_data",), must_exist=True)
    manager._validate_xml_tags(rendered_user, ("feedback_rules",), must_exist=False)
    return prompt_value


def _build_structured_llm() -> Any:
    ChatGoogleGenerativeAI = _load_chat_google_model()
    model_name = os.getenv("PHD2_GEMINI_MODEL", "gemini-2.5-flash")
    llm = ChatGoogleGenerativeAI(model=model_name, temperature=0)
    return llm.with_structured_output(JobUnderstandingExtract)


def _load_chat_prompt_template() -> Any:
    try:
        prompts_module = importlib.import_module("langchain_core.prompts")
    except ImportError as exc:
        raise LLMRuntimeDependencyError(
            "langchain-core is required for extract_understand"
        ) from exc
    return getattr(prompts_module, "ChatPromptTemplate")


def _load_chat_google_model() -> Any:
    try:
        genai_module = importlib.import_module("langchain_google_genai")
    except ImportError as exc:
        raise LLMRuntimeDependencyError(
            "langchain-google-genai is required for extract_understand"
        ) from exc
    return getattr(genai_module, "ChatGoogleGenerativeAI")


def _extract_human_message(prompt_value: Any) -> str:
    messages = getattr(prompt_value, "messages", [])
    for message in messages:
        if getattr(message, "type", "") == "human":
            content = getattr(message, "content", "")
            if isinstance(content, str):
                return content
    return ""


def _langsmith_trace_context(node_data: Mapping[str, Any]) -> Any:
    if not os.getenv("LANGSMITH_API_KEY"):
        return nullcontext()
    try:
        run_helpers = importlib.import_module("langsmith.run_helpers")
    except ImportError:
        return nullcontext()

    trace = getattr(run_helpers, "trace", None)
    if not callable(trace):
        return nullcontext()
    return trace(
        "extract_understand",
        run_type="chain",
        inputs={
            "job_id": node_data.get("job_id"),
            "active_feedback": node_data.get("active_feedback", []),
        },
        tags=["phd2", "extract_understand", "minimal-architecture"],
    )


def _enrich_extraction_result(
    result: JobUnderstandingExtract, source_text: str
) -> JobUnderstandingExtract:
    payload = result.model_dump()
    contact_payload = payload.get("contact_info") or {}
    if not isinstance(contact_payload, dict):
        contact_payload = {}

    email = contact_payload.get("email") or _detect_contact_email(source_text)
    name = contact_payload.get("name") or _detect_contact_name(source_text, email)

    payload["contact_info"] = ContactInfo(name=name, email=email).model_dump()
    payload["salary_grade"] = payload.get("salary_grade") or _detect_salary_grade(
        source_text
    )
    return JobUnderstandingExtract.model_validate(payload)


def _detect_contact_email(source_text: str) -> str | None:
    match = EMAIL_RE.search(source_text)
    if not match:
        return None
    return match.group(0)


def _detect_contact_name(source_text: str, email: str | None) -> str | None:
    lines = [line.strip() for line in source_text.splitlines() if line.strip()]
    if not lines:
        return None

    if email:
        for index, line in enumerate(lines):
            if email not in line:
                continue
            same_line = _extract_name_fragment(line.replace(email, " "))
            if same_line:
                return same_line
            for neighbor in _neighbor_lines(lines, index):
                candidate = _extract_name_fragment(neighbor)
                if candidate:
                    return candidate

    for line in lines:
        candidate = _extract_name_fragment(line)
        if candidate:
            return candidate
    return None


def _detect_salary_grade(source_text: str) -> str | None:
    match = SALARY_RE.search(source_text)
    if not match:
        return None
    return " ".join(match.group(0).split())


def _neighbor_lines(lines: list[str], index: int) -> list[str]:
    output: list[str] = []
    for offset in (-1, 1):
        neighbor_index = index + offset
        if 0 <= neighbor_index < len(lines):
            output.append(lines[neighbor_index])
    return output


def _extract_name_fragment(value: str) -> str | None:
    match = NAME_RE.search(value)
    if not match:
        return None
    candidate = " ".join(match.group(0).split())
    lowered = candidate.lower()
    if any(token in lowered for token in ("job", "salary", "application")):
        return None
    return candidate


def _build_node_data(state: Mapping[str, Any]) -> dict[str, Any]:
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
