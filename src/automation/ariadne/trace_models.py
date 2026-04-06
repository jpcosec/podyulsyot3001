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
    timestamp: datetime = Field(default_factory=datetime.now)
    event_type: str  # click, change, navigate, keydown, snapshot, screenshot
    
    # Motor-specific raw data
    selector: Optional[str] = None
    selectors: Optional[List[List[str]]] = None  # Compatible with Chrome Recorder
    value: Optional[str] = None
    url: Optional[str] = None
    
    # Page Context
    page_title: Optional[str] = None
    page_url: Optional[str] = None
    
    # Artifacts
    screenshot_path: Optional[str] = None
    dom_snapshot_path: Optional[str] = None
    
    metadata: Dict[str, Any] = Field(default_factory=dict)


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
