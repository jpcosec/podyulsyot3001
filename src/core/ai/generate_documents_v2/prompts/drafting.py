"""Prompts for drafting document sections from a blueprint."""

from __future__ import annotations

from src.core.ai.generate_documents_v2.contracts.blueprint import GlobalBlueprint

DRAFTING_SYSTEM_PROMPT = """You are a professional application writer.

Rules:
- Write concise Markdown.
- Follow the blueprint order exactly.
- Keep the content in English unless a later stage explicitly localizes it.
- Do not invent new evidence beyond the blueprint intent.
"""


def build_drafting_user_prompt(doc_type: str, blueprint: GlobalBlueprint) -> str:
    """Build the user prompt for drafting one document type from a blueprint."""
    context_lines = []
    if blueprint.job_title:
        context_lines.append(f"JOB TITLE: {blueprint.job_title}")
    if blueprint.source:
        context_lines.append(f"SOURCE PLATFORM: {blueprint.source}")

    context_block = "\n".join(context_lines)

    return f"""Draft the `{doc_type}` document from this blueprint.

{context_block}

BLUEPRINT:
{blueprint.model_dump_json(indent=2)}

Return a DraftedDocument for `{doc_type}` with Markdown per section ID. 
CRITICAL: Do NOT use placeholders like [Job Title], [Platform], [Month Year] or [Date]. 
If a value is unknown, omit the sentence or write a professional generic alternative.
"""
