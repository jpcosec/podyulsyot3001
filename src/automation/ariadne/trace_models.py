"""Ariadne Trace Models — Raw Recording & Normalization.

This module defines the models for capturing raw interaction traces 
(from motors or Chrome DevTools Recorder exports) before they are 
promoted to semantic Ariadne Maps.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class RawTraceEvent(BaseModel):
    """An atomic event captured during a live session."""
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="ISO timestamp when the event was captured."
    )
    event_type: str = Field(
        description="Type of interaction (e.g., 'click', 'change', 'navigate', 'screenshot')."
    )
    
    # Motor-specific raw data
    selector: Optional[str] = Field(
        default=None, 
        description="Primary CSS selector for the interacted element."
    )
    selectors: Optional[List[List[str]]] = Field(
        default=None, 
        description="Nested list of selectors compatible with Chrome DevTools Recorder."
    )
    value: Optional[str] = Field(
        default=None, 
        description="Input value for 'change' or 'keydown' events."
    )
    url: Optional[str] = Field(
        default=None, 
        description="Target URL for 'navigate' events."
    )
    
    # Page Context
    page_title: Optional[str] = Field(default=None, description="Title of the page at the time of event.")
    page_url: Optional[str] = Field(default=None, description="Full URL of the page at the time of event.")
    
    # Artifacts
    screenshot_path: Optional[str] = Field(default=None, description="Relative path to the screenshot PNG.")
    dom_snapshot_path: Optional[str] = Field(default=None, description="Relative path to the DOM snapshot file.")
    
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Extensible bag for motor-specific event metadata."
    )


class AriadneSessionTrace(BaseModel):
    """A collection of raw events representing a single recording session."""
    session_id: str
    portal_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    events: List[RawTraceEvent] = Field(default_factory=list)
    
    # Device/Browser Info
    viewport: Dict[str, int] = Field(default_factory=lambda: {"width": 1280, "height": 720})
    user_agent: Optional[str] = None


class TraceNormalizationReport(BaseModel):
    """Summary of the conversion from Raw Trace -> Ariadne Map."""
    raw_event_count: int
    steps_generated: int
    states_inferred: List[str]
    confidence_score: float  # 0.0 to 1.0
    warnings: List[str] = Field(default_factory=list)
