"""Ariadne Payload Transformers — Pipeline for job normalization."""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from .job_normalization import (
    clean_location_text,
    detect_employment_type_from_text,
    hero_markdown_value,
    listing_case_metadata_value,
    mine_bullets_from_markdown,
    _record_field_source,
    _record_operation,
)


class NormalizationContext:
    """Carries the state through the transformation pipeline."""

    def __init__(
        self,
        payload: Dict[str, Any],
        markdown_text: str = "",
        listing_case: Optional[Dict[str, Any]] = None,
        rescue_source: Optional[str] = None,
        diagnostics: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.payload = payload
        self.markdown_text = markdown_text
        self.listing_case = listing_case
        self.rescue_source = rescue_source
        self.diagnostics = diagnostics or {
            "field_sources": {},
            "operations": [],
        }

    def record_operation(self, operation: str) -> None:
        _record_operation(self.diagnostics, operation)

    def record_field_source(self, field: str, source: str) -> None:
        _record_field_source(self.diagnostics, field=field, source=source)


class PayloadTransformer(ABC):
    """Abstract base class for a single normalization step."""

    @abstractmethod
    def transform(self, context: NormalizationContext) -> None:
        """Apply the transformation to the context."""
        ...


class UnwrapDataTransformer(PayloadTransformer):
    """Unwraps 'data' wrappers from the payload."""

    def transform(self, context: NormalizationContext) -> None:
        data = context.payload.get("data")
        if data is not None:
            del context.payload["data"]
            context.record_operation("unwrap_data")
            if isinstance(data, dict):
                context.payload.update(data)
            elif isinstance(data, list):
                for item in data:
                    if isinstance(item, dict):
                        context.payload.update(item)

            for field, value in context.payload.items():
                if (
                    field != "listing_case"
                    and value not in (None, "", [], {})
                    and field not in context.diagnostics.get("field_sources", {})
                ):
                    context.record_field_source(
                        field=field, source=context.rescue_source or "raw"
                    )


class FieldFlatteningTransformer(PayloadTransformer):
    """Flattens list fields like responsibilities."""

    def transform(self, context: NormalizationContext) -> None:
        for key in ("responsibilities", "requirements", "benefits"):
            if isinstance(context.payload.get(key), list):
                flattened = [
                    v["item"] if isinstance(v, dict) and "item" in v else v
                    for v in context.payload[key]
                ]
                if flattened != context.payload.get(key):
                    context.record_operation(f"flatten_{key}")
                context.payload[key] = flattened


class CleanupTransformer(PayloadTransformer):
    """General cleanup: empty strings to None, location cleanup."""

    def transform(self, context: NormalizationContext) -> None:
        for key in ("company_name", "location", "employment_type", "posted_date"):
            if context.payload.get(key) == "":
                context.payload[key] = None
                context.record_operation(f"empty_to_none:{key}")

        if context.payload.get("location"):
            cleaned = clean_location_text(context.payload["location"])
            if cleaned != context.payload["location"]:
                context.record_operation("clean_location_suffix")
                context.record_field_source(field="location", source="normalized")
            context.payload["location"] = cleaned


class ListingCaseTransformer(PayloadTransformer):
    """Enriches payload from listing card data."""

    def transform(self, context: NormalizationContext) -> None:
        if not context.listing_case:
            return

        lc = context.listing_case
        mappings = {
            "company_name": "teaser_company",
            "location": "teaser_location",
            "employment_type": "teaser_employment_type",
        }
        for field, teaser_key in mappings.items():
            if not context.payload.get(field) and lc.get(teaser_key):
                context.payload[field] = lc.get(teaser_key)
                context.record_field_source(field=field, source="listing_case")

        # Fallback to metadata
        invalid_company = {"be an early applicant", "save job"}
        current_company = str(context.payload.get("company_name") or "").strip().lower()
        if not context.payload.get("company_name") or current_company in invalid_company:
            meta_company = listing_case_metadata_value(lc, field="company_name")
            if meta_company:
                context.payload["company_name"] = meta_company
                context.record_field_source(field="company_name", source="listing_metadata")

        if not context.payload.get("location"):
            meta_location = listing_case_metadata_value(lc, field="location")
            if meta_location:
                context.payload["location"] = meta_location
                context.record_field_source(field="location", source="listing_metadata")


class MarkdownMiningTransformer(PayloadTransformer):
    """Mines fields from markdown text."""

    def transform(self, context: NormalizationContext) -> None:
        if not context.markdown_text:
            return

        md = context.markdown_text
        if not context.payload.get("company_name"):
            val = hero_markdown_value(md, field="company_name")
            if val:
                context.payload["company_name"] = val
                context.record_field_source(field="company_name", source="hero_markdown")

        if not context.payload.get("location"):
            val = hero_markdown_value(md, field="location")
            if val:
                context.payload["location"] = val
                context.record_field_source(field="location", source="hero_markdown")

        if not context.payload.get("employment_type"):
            val = detect_employment_type_from_text(md)
            if val:
                context.payload["employment_type"] = val
                context.record_field_source(field="employment_type", source="hero_markdown")

        if not context.payload.get("responsibilities") or not context.payload.get("requirements"):
            bullets = mine_bullets_from_markdown(md)
            if not context.payload.get("responsibilities") and bullets.get("responsibilities"):
                context.payload["responsibilities"] = bullets["responsibilities"]
                context.record_field_source(field="responsibilities", source="text_mining")
            if not context.payload.get("requirements") and bullets.get("requirements"):
                context.payload["requirements"] = bullets["requirements"]
                context.record_field_source(field="requirements", source="text_mining")


class SwapGuardTransformer(PayloadTransformer):
    """Final guard to swap obvious misclassifications."""

    def transform(self, context: NormalizationContext) -> None:
        company_markers = r"\bgmbh\b|\bag\b|\bse\b|\bgroup\b|\bconsulting\b|\bservices\b|\bdata\b|\breply\b|\bntt\b"
        if not context.payload.get("company_name") and context.payload.get("location"):
            if re.search(company_markers, context.payload["location"].lower()):
                context.payload["company_name"] = context.payload["location"]
                context.payload["location"] = None
                context.record_operation("swap_location_to_company")


class NormalizationPipeline:
    """Executes a series of transformers."""

    def __init__(self, transformers: List[PayloadTransformer]) -> None:
        self.transformers = transformers

    def execute(self, context: NormalizationContext) -> None:
        for transformer in self.transformers:
            transformer.transform(context)
