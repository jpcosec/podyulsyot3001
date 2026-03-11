"""Contracts for scrape ingestion stage."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class IngestedData(BaseModel):
    source_url: str
    original_language: str
    raw_text: str
    metadata: dict[str, Any] = Field(default_factory=dict)
