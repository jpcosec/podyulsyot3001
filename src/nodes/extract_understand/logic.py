"""Extraction node logic using LangChain structured output."""

from __future__ import annotations

import os
import re
import importlib
from typing import Any, Mapping

from src.ai.llm_runtime import LLMRuntimeDependencyError, LLMRuntimeResponseError
from src.ai.prompt_manager import PromptManager
from src.core.ai.config import LLMConfig
from src.core.ai.tracing import trace_section
from src.core.text.span_resolver import resolve_span
from src.nodes.extract_understand.contract import (
    ContactInfo,
    JobRequirement,
    JobUnderstandingExtract,
    TextSpan,
)

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
    cfg = LLMConfig.from_env()
    prompt_value = _build_prompt_value(node_data)
    llm = _build_structured_llm()
    try:
        with trace_section(
            "extract_understand.llm_call",
            metadata={
                "job_id": node_data.get("job_id"),
                "langsmith_enabled": cfg.langsmith_enabled,
            },
        ):
            response = llm.invoke(prompt_value)
    except Exception as exc:  # noqa: BLE001
        raise LLMRuntimeResponseError("langchain structured extraction failed") from exc

    try:
        result = JobUnderstandingExtract.model_validate(response)
        with trace_section(
            "extract_understand.persist",
            metadata={"job_id": node_data.get("job_id"), "validated": True},
        ):
            pass
        return result
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
        ],
        template_format="jinja2",
    )
    prompt_value = chat_prompt.invoke(node_data)

    rendered_user = _extract_human_message(prompt_value)
    manager._validate_xml_tags(rendered_user, ("input_data",), must_exist=True)
    manager._validate_xml_tags(rendered_user, ("feedback_rules",), must_exist=False)
    return prompt_value


def _build_structured_llm() -> Any:
    ChatGoogleGenerativeAI = _load_chat_google_model()
    cfg = LLMConfig.from_env()
    llm = ChatGoogleGenerativeAI(model=cfg.model, temperature=cfg.temperature)
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


def _enrich_extraction_result(
    result: JobUnderstandingExtract, source_text: str
) -> JobUnderstandingExtract:
    payload = result.model_dump()
    contact_payload = payload.get("contact_info") or {}
    if not isinstance(contact_payload, dict):
        contact_payload = {}

    contact_infos_payload = payload.get("contact_infos")
    existing_contacts = _normalize_contact_infos(contact_infos_payload)
    detected_contacts = _detect_contact_infos(source_text)

    email = contact_payload.get("email") or _detect_contact_email(source_text)
    name = contact_payload.get("name") or _detect_contact_name(source_text, email)
    primary = ContactInfo(name=name, email=email)

    merged_contacts = _merge_contacts(existing_contacts, detected_contacts)
    merged_contacts = _merge_contacts([primary], merged_contacts)
    primary_contact = _select_primary_contact(primary, merged_contacts)

    payload["contact_info"] = primary_contact.model_dump()
    payload["contact_infos"] = [contact.model_dump() for contact in merged_contacts]
    payload["salary_grade"] = payload.get("salary_grade") or _detect_salary_grade(
        source_text
    )
    payload["requirements"] = _enrich_requirements(
        payload.get("requirements", []), source_text
    )
    return JobUnderstandingExtract.model_validate(payload)


def _enrich_requirements(requirements: list[dict], source_text: str) -> list[dict]:
    enriched = []
    for req in requirements:
        span_resolution = resolve_span(source_text, req.get("text"))
        if span_resolution.found:
            req["text_span"] = TextSpan(
                start_line=span_resolution.start_line,
                end_line=span_resolution.end_line,
                start_offset=span_resolution.start_offset,
                end_offset=span_resolution.end_offset,
                preview_snippet=span_resolution.preview_snippet,
            ).model_dump()
        else:
            req["text_span"] = None
        enriched.append(req)
    return enriched


def _detect_contact_email(source_text: str) -> str | None:
    emails = _detect_contact_emails(source_text)
    if not emails:
        return None
    return emails[0]


def _detect_contact_emails(source_text: str) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for match in EMAIL_RE.finditer(source_text):
        email = match.group(0)
        lowered = email.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        output.append(email)
    return output


def _detect_contact_infos(source_text: str) -> list[ContactInfo]:
    emails = _detect_contact_emails(source_text)
    output: list[ContactInfo] = []
    for email in emails:
        output.append(
            ContactInfo(
                name=_detect_contact_name(source_text, email),
                email=email,
            )
        )
    return output


def _normalize_contact_infos(value: Any) -> list[ContactInfo]:
    if not isinstance(value, list):
        return []
    output: list[ContactInfo] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        output.append(
            ContactInfo(
                name=str(item.get("name") or "").strip() or None,
                email=str(item.get("email") or "").strip() or None,
            )
        )
    return output


def _merge_contacts(
    base_contacts: list[ContactInfo],
    other_contacts: list[ContactInfo],
) -> list[ContactInfo]:
    merged: list[ContactInfo] = []
    for candidate in [*base_contacts, *other_contacts]:
        merged = _upsert_contact(merged, candidate)
    return merged


def _upsert_contact(
    contacts: list[ContactInfo], candidate: ContactInfo
) -> list[ContactInfo]:
    has_name = bool(candidate.name and candidate.name.strip())
    has_email = bool(candidate.email and candidate.email.strip())
    if not has_name and not has_email:
        return contacts

    candidate_email = (candidate.email or "").strip().lower()
    candidate_name = (candidate.name or "").strip().lower()

    for index, existing in enumerate(contacts):
        existing_email = (existing.email or "").strip().lower()
        existing_name = (existing.name or "").strip().lower()
        same_email = bool(
            candidate_email and existing_email and candidate_email == existing_email
        )
        same_name = bool(
            candidate_name and existing_name and candidate_name == existing_name
        )
        if not same_email and not same_name:
            continue

        best_name = existing.name or candidate.name
        best_email = existing.email or candidate.email
        contacts[index] = ContactInfo(name=best_name, email=best_email)
        return contacts

    contacts.append(candidate)
    return contacts


def _select_primary_contact(
    preferred: ContactInfo,
    contacts: list[ContactInfo],
) -> ContactInfo:
    if preferred.name or preferred.email:
        return preferred
    if contacts:
        return contacts[0]
    return ContactInfo()


def _detect_contact_name(source_text: str, email: str | None) -> str | None:
    lines = [line.strip() for line in source_text.splitlines() if line.strip()]
    if not lines:
        return None

    if email:
        for index, line in enumerate(lines):
            if email not in line:
                continue
            same_line = _extract_name_near_email(line, email)
            if same_line:
                return same_line
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


def _extract_name_near_email(line: str, email: str) -> str | None:
    before, _, after = line.partition(email)
    candidates = [before, after]
    for candidate in candidates:
        compact = re.sub(r"\s+", " ", candidate).strip(" -,:;|()")
        if not compact:
            continue
        local = compact
        if " at " in local.lower():
            local = local.rsplit(" at ", 1)[-1]
        if " unter " in local.lower():
            local = local.rsplit(" unter ", 1)[-1]
        found = _extract_name_fragment(local)
        if found:
            return found
    return None


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
