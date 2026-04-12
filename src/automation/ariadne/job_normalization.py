from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class JobNormalizationResult(BaseModel):
    payload: Dict[str, Any] = Field(default_factory=dict)
    diagnostics: Dict[str, Any] = Field(default_factory=dict)


def _init_normalization_diagnostics(
    existing_diagnostics: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "field_sources": dict((existing_diagnostics or {}).get("field_sources", {})),
        "operations": list((existing_diagnostics or {}).get("operations", [])),
    }


def _record_field_source(
    diagnostics: Dict[str, Any],
    *,
    field: str,
    source: str,
) -> None:
    diagnostics.setdefault("field_sources", {})[field] = source


def _record_operation(diagnostics: Dict[str, Any], operation: str) -> None:
    operations = diagnostics.setdefault("operations", [])
    if operation not in operations:
        operations.append(operation)


def extract_job_title_from_markdown(markdown_text: str) -> Optional[str]:
    if not markdown_text:
        return None
    
    error_titles = {
        "your connection was interrupted",
        "access denied",
        "page not found",
        "404 not found",
        "service unavailable",
        "just a moment",
        "checking your browser",
    }

    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            if title:
                if title.lower() in error_titles:
                    continue
                return title
    for line in markdown_text.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith(("-", "*", "#")):
            if stripped.lower() in error_titles:
                continue
            return stripped[:200]
    return None


def detect_employment_type_from_text(markdown_text: str) -> Optional[str]:
    lower = markdown_text.lower()
    patterns = {
        "Full-time": ["full-time", "full time", "vollzeit"],
        "Part-time": ["part-time", "part time", "teilzeit"],
        "Internship": ["internship", "praktikum", "intern"],
        "Working Student": ["werkstudent", "working student"],
        "Contract": ["contract", "befristet"],
    }
    for label, variants in patterns.items():
        if any(variant in lower for variant in variants):
            return label
    return None


def clean_location_text(value: Any) -> Optional[str]:
    if not isinstance(value, str):
        return None
    cleaned = re.sub(r"\*+", "", value).strip()
    cleaned = re.sub(r"\s*\+\s*\d+\s+more$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,")
    return cleaned or None


def hero_markdown_value(markdown_text: str, *, field: str) -> Optional[str]:
    if not markdown_text:
        return None
    lines = [line.strip() for line in markdown_text.splitlines() if line.strip()]
    title = extract_job_title_from_markdown(markdown_text)
    title_index = 0
    if title:
        for index, line in enumerate(lines):
            if title in line or line == f"# {title}":
                title_index = index
                break
    hero_lines = lines[title_index : title_index + 12]

    if field == "location":
        skip_values = {"suche", "login", "menu", "jobs finden", "speichern"}
        metadata_like_terms = {
            "feste anstellung",
            "vollzeit",
            "teilzeit",
            "homeoffice möglich",
            "homeoffice moglich",
            "erschienen",
            "gehalt anzeigen",
        }
        company_like_patterns = (
            r"\bgmbh\b",
            r"\bag\b",
            r"\bse\b",
            r"\bkg\b",
            r"\binc\b",
            r"\bllc\b",
            r"\bgroup\b",
            r"\bconsulting\b",
            r"\bservices\b",
            r"\bdata\b",
            r"\breply\b",
            r"\bntt\b",
        )
        for line in hero_lines:
            if not line.startswith(("*", "-")):
                continue
            match = re.match(r"^[*-]\s+\[([^\]]+)\]\([^\)]+\)$", line)
            candidate = match.group(1) if match else re.sub(r"^[*-]\s+", "", line)
            candidate = clean_location_text(candidate)
            if candidate and candidate.lower() not in skip_values:
                if candidate.lower() in metadata_like_terms:
                    continue
                if any(term in candidate.lower() for term in metadata_like_terms):
                    continue
                if any(
                    re.search(pattern, candidate.lower())
                    for pattern in company_like_patterns
                ):
                    continue
                
                # Broad rejection: if it contains 'data' or 'reply' or other markers, skip it as location
                # unless it also has a comma (e.g. "Berlin, Reply Group" - wait, that's still bad)
                # Actually, if it has a comma, it's more likely a location if the first part is a city.
                
                if "," in candidate:
                    return candidate
                if re.fullmatch(
                    r"[A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-]+(?:,? [A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-]+)*",
                    candidate,
                ):
                    return candidate
        return None

    if field == "company_name":
        company_markers = (
            r"\bgmbh\b",
            r"\bag\b",
            r"\be\.v\.\b",
            r"universit",
            r"institute",
            r"institut",
            r"charité",
            r"charite",
            r"\binc\b",
            r"\bllc\b",
            r"\bse\b",
            r"\bgroup\b",
            r"\bntt\b",
            r"\breply\b",
            r"\bdata\b",
        )
        metadata_markers = {
            "feste anstellung",
            "vollzeit",
            "teilzeit",
            "homeoffice möglich",
            "homeoffice moglich",
            "erschienen",
            "gehalt anzeigen",
        }
        
        for line in hero_lines:
            if not line.startswith(("*", "-")):
                continue
            
            # Check for link-based company (e.g. [Company](url))
            for candidate in re.findall(r"\[([^\]]+)\]\([^\)]+\)", line):
                candidate = candidate.strip()
                if candidate and candidate != title:
                    if any(re.search(marker, candidate.lower()) for marker in company_markers):
                        return candidate
            
            # Check for plain text company
            candidate = re.sub(r"^[*-]\s+", "", line)
            candidate = re.sub(r"\[([^\]]*)\]\([^\)]+\)", r"\1", candidate)
            candidate = re.sub(r"\*+", "", candidate).strip()
            
            if not candidate or candidate == title:
                continue
                
            if any(re.search(marker, candidate.lower()) for marker in company_markers):
                return candidate
            
            # Heuristic fallback: if it's the first bullet after title and doesn't look like metadata/location
            if candidate.lower() not in metadata_markers and not any(m in candidate.lower() for m in metadata_markers):
                # If it doesn't look like a location (no commas, no obvious city-only pattern)
                # This is risky, but StepStone's first bullet is ALMOST ALWAYS the company.
                if "," not in candidate and len(candidate) > 2:
                    return candidate
        
        return None

    return None


def merge_rescue_payloads(
    *,
    base_payload: Optional[Dict[str, Any]],
    rescue_payload: Optional[Dict[str, Any]],
) -> Optional[Dict[str, Any]]:
    if base_payload is None and rescue_payload is None:
        return None
    merged = dict(base_payload or {})
    override_fields = {"job_title", "responsibilities", "requirements", "benefits"}
    for key, value in (rescue_payload or {}).items():
        if value in (None, "", [], {}):
            continue
        if (
            key in merged
            and merged.get(key) not in (None, "", [], {})
            and key not in override_fields
        ):
            continue
        merged[key] = value
    return merged


def listing_case_metadata_value(
    listing_case: Dict[str, Any],
    *,
    field: str,
) -> Optional[str]:
    source_metadata = listing_case.get("source_metadata") or {}
    listing_texts = source_metadata.get("listing_texts") or []
    if not isinstance(listing_texts, list):
        return None

    title = str(listing_case.get("teaser_title") or "").strip()
    skip_texts = {"be an early applicant", "save job", "posted yesterday", "yesterday"}

    if field == "company_name":
        for text in listing_texts:
            candidate = str(text).strip()
            if not candidate or candidate == title:
                continue
            lower = candidate.lower()
            if lower in skip_texts or candidate.startswith("+") or "€" in candidate:
                continue
            if candidate in {"Berlin", "Full-time"}:
                continue
            return candidate

    if field == "location":
        for text in listing_texts:
            candidate = clean_location_text(text)
            if not candidate or candidate == title:
                continue
            lower = candidate.lower()
            if lower in skip_texts or any(
                marker in lower for marker in ("gmbh", "ag", "jobriver", "service")
            ):
                continue
            if re.fullmatch(
                r"[A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-]+(?:,? [A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-]+)*",
                candidate,
            ):
                return candidate

    return None


def mine_bullets_from_markdown(markdown: str) -> Dict[str, List[str]]:
    responsibilities_headings = {
        "beschreibung",
        "deine rolle",
        "das erwartet dich",
        "deine aufgaben",
        "aufgaben",
        "ihre aufgaben",
        "du übernimmst",
        "du ubernimmst",
        "dein beitrag",
        "was du tust",
        "die stelle im überblick",
        "die stelle im uberblick",
        "your responsibilities",
        "your responsibility",
        "responsibilities",
    }
    requirements_headings = {
        "das bringst du mit",
        "dein profil",
        "das zeichnet dich aus",
        "dein equipment",
        "qualifikation",
        "anforderungen",
        "ihre qualifikationen",
        "qualifikationen",
        "danach suchen wir",
        "was wir erwarten",
        "what you bring",
        "your profile",
        "requirements",
    }

    bullets: Dict[str, List[str]] = {"responsibilities": [], "requirements": []}
    prose: Dict[str, List[str]] = {"responsibilities": [], "requirements": []}
    if not markdown:
        return bullets

    current_section: Optional[str] = None
    for line in markdown.split("\n"):
        stripped = line.strip()
        heading_match = re.match(r"^#{2,4}\s+(.+)", stripped)
        if heading_match is None:
            heading_match = re.match(r"^\*\*(.+?)\*\*$", stripped)
        if heading_match:
            heading_lower = heading_match.group(1).replace("**", "").lower().strip(" :")
            if heading_lower in responsibilities_headings:
                current_section = "responsibilities"
                continue
            if heading_lower in requirements_headings:
                current_section = "requirements"
                continue
            current_section = None
            continue

        if current_section and re.match(r"^[-*•]\s+(.+)", stripped):
            bullets[current_section].append(stripped[2:].strip())
            continue

        if current_section and stripped:
            if stripped.startswith(("[", "!", "|")) or stripped == "* * *":
                continue
            prose[current_section].append(stripped)

    for section, values in prose.items():
        if values and not bullets[section]:
            bullets[section] = [" ".join(values)]

    return bullets


def normalize_job_payload(
    payload: Optional[Dict[str, Any]],
    *,
    markdown_text: str = "",
    listing_case: Optional[Dict[str, Any]] = None,
    rescue_source: Optional[str] = None,
    existing_diagnostics: Optional[Dict[str, Any]] = None,
) -> JobNormalizationResult:
    """Standardizes a job payload using a pipeline of transformers."""
    if not payload:
        diagnostics = _init_normalization_diagnostics(existing_diagnostics)
        return JobNormalizationResult(payload={}, diagnostics=diagnostics)

    from .transformers import (
        CleanupTransformer,
        FieldFlatteningTransformer,
        ListingCaseTransformer,
        MarkdownMiningTransformer,
        NormalizationContext,
        NormalizationPipeline,
        SwapGuardTransformer,
        UnwrapDataTransformer,
    )

    context = NormalizationContext(
        payload=dict(payload),
        markdown_text=markdown_text,
        listing_case=listing_case,
        rescue_source=rescue_source,
        diagnostics=_init_normalization_diagnostics(existing_diagnostics),
    )

    pipeline = NormalizationPipeline(
        [
            UnwrapDataTransformer(),
            FieldFlatteningTransformer(),
            CleanupTransformer(),
            ListingCaseTransformer(),
            MarkdownMiningTransformer(),
            SwapGuardTransformer(),
        ]
    )

    pipeline.execute(context)

    return JobNormalizationResult(payload=context.payload, diagnostics=context.diagnostics)
