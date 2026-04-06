"""Ariadne Core Models — The Unified Semantic & Path Layer.

This module defines the backend-neutral models for automation:
1. Target Resolution (How to find elements)
2. Intent Vocabulary (What actions to perform)
3. Standardized Path (Linear sequences)
4. Semantic Layer (States, Tasks, and Goals)
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field


# --- Target Layer ---

class AriadneTarget(BaseModel):
    """Multi-strategy element descriptor. Each motor uses what it understands."""

    css: Optional[str] = Field(default=None, description="CSS selector for Crawl4AI/Playwright")
    text: Optional[str] = Field(default=None, description="Fuzzy text match for BrowserOS")
    image_template: Optional[str] = Field(default=None, description="OpenCV template path for Vision")
    ocr_text: Optional[str] = Field(default=None, description="OCR text region for Vision fallback")
    region: Optional[Dict[str, int]] = Field(default=None, description="Bounding box {x, y, w, h}")


# --- Intent Layer ---

class AriadneIntent(str, Enum):
    """The 'What to do' — backend-neutral action vocabulary."""

    CLICK = "click"
    FILL = "fill"
    FILL_REACT = "fill_react_controlled"
    SELECT = "select"
    UPLOAD = "upload"
    PRESS_KEY = "press_key"
    SCROLL = "scroll"
    WAIT = "wait"
    NAVIGATE = "navigate"


class AriadneAction(BaseModel):
    """An atomic interaction with a target."""

    intent: AriadneIntent
    target: Optional[AriadneTarget] = None
    value: Optional[str] = Field(default=None, description="Value with {{placeholders}}")
    fallback: Optional[AriadneAction] = None
    optional: bool = False


# --- Observation Layer ---

class AriadneObserve(BaseModel):
    """Predicate to identify a state or confirm a result."""

    required_elements: List[AriadneTarget] = Field(default_factory=list)
    forbidden_elements: List[AriadneTarget] = Field(default_factory=list)
    logical_op: Literal["AND", "OR"] = "AND"


# --- Semantic Layer ---

class AriadneState(BaseModel):
    """A semantic 'Room' in the portal (e.g., Login Page, Contact Info Modal)."""

    id: str
    description: str
    presence_predicate: AriadneObserve
    
    # Components that compose this page/state
    components: Dict[str, AriadneTarget] = Field(default_factory=dict)
    
    # Possible actions leading to other states
    transitions: Dict[str, str] = Field(
        default_factory=dict, 
        description="Mapping of action_id -> next_state_id"
    )


class AriadneRecoveryPlan(BaseModel):
    """Standardized recovery steps for known blockers (e.g., Cookie Banners)."""

    trigger_predicate: AriadneObserve
    recovery_actions: List[AriadneAction]
    resume_strategy: Literal["RETRY_STEP", "RESTART_FLOW", "ABORT"] = "RETRY_STEP"


class AriadneTask(BaseModel):
    """The 'Mission' (e.g., Submit Application). Defines success/failure boundaries."""

    id: str
    goal: str
    entry_state: str
    
    success_states: List[str] = Field(description="State IDs that signal mission success")
    failure_states: List[str] = Field(description="State IDs that signal terminal failure")
    
    # Recovery for blockers like captchas or popups
    blocker_recovery: List[AriadneRecoveryPlan] = Field(default_factory=list)


# --- Path Layer ---

class AriadneStep(BaseModel):
    """One sequential unit of a path traversal."""

    step_index: int
    name: str
    description: str
    
    # Semantic Context
    state_id: Optional[str] = None
    
    # Execution
    observe: AriadneObserve
    actions: List[AriadneAction]
    
    # Flow Control
    next_step_index: Optional[int] = None
    human_required: bool = False
    dry_run_stop: bool = False


class AriadnePath(BaseModel):
    """A linear 'Tape' through a task, used by deterministic replayers."""

    id: str
    task_id: str
    steps: List[AriadneStep]
    metadata: Dict[str, str] = Field(default_factory=dict)


# --- The Unified Map ---

class AriadnePortalMap(BaseModel):
    """The 'One Map' per portal flow, containing all semantics and paths."""

    portal_name: str
    base_url: str
    
    # Semantic Registry
    states: Dict[str, AriadneState]
    tasks: Dict[str, AriadneTask]
    
    # Path Registry (Deterministic sequences)
    paths: Dict[str, AriadnePath]
    
    # Global/Cross-State components
    global_components: Dict[str, AriadneTarget] = Field(default_factory=dict)
