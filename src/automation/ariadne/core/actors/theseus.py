"""Theseus - The Deterministic Fast Path Actor."""

from __future__ import annotations

from typing import Any, Dict, Optional, Union, List
from langgraph.graph import StateGraph, END

from src.automation.ariadne.core.periphery import Sensor, Motor
from src.automation.ariadne.core.cognition import Labyrinth, AriadneThread
from src.automation.ariadne.models import AriadneState, AriadneEdge
from src.automation.ariadne.contracts.base import SnapshotResult


class Theseus:
    """
    The low-cost deterministic coordinator.
    Implements the core LangGraph loop: Observe -> Think -> Act.
    """

    def __init__(
        self,
        sensor: Sensor,
        motor: Motor,
        labyrinth: Labyrinth,
        thread: AriadneThread,
    ):
        self.sensor = sensor
        self.motor = motor
        self.labyrinth = labyrinth
        self.thread = thread

    async def observe(self, state: AriadneState) -> Dict[str, Any]:
        """Perceive the world and identify the current room."""
        print("--- [ACTOR] Theseus: Observe ---")
        
        # 1. Health check
        if not await self.sensor.is_healthy():
            return {"errors": ["FatalError: Sensor disconnected"]}

        # 2. Perceive
        snapshot = await self.sensor.perceive()
        
        # 3. Identify Room
        room_id = await self.labyrinth.identify_room(snapshot)
        
        print(f"--- [ACTOR] Identified Room: {room_id} ---")
        
        return {
            "current_url": snapshot.url,
            "dom_elements": snapshot.dom_elements,
            "screenshot_b64": snapshot.screenshot_b64,
            "current_state_id": room_id,
        }

    async def execute_deterministic(self, state: AriadneState) -> Dict[str, Any]:
        """Determine next step and execute if it exists in the thread."""
        print("--- [ACTOR] Theseus: Execute ---")
        
        room_id = state.get("current_state_id")
        if not room_id:
            return {"errors": ["LogicError: Cannot execute from unknown room"]}

        # 1. Find edge in mission thread
        edge = self.thread.get_next_step(room_id)
        if not edge:
            print("--- [ACTOR] No deterministic edge found. Escalating. ---")
            return {"errors": ["NoDeterministicPath"]}

        # 2. Translate intent to motor command (Simplified for now)
        # In a full implementation, this uses TranslatorRegistry
        from src.automation.ariadne.contracts.base import BrowserOSCommand
        command = BrowserOSCommand(
            tool="click" if edge.intent == "click" else "fill",
            selector_text=edge.target,
            value=edge.value
        )

        # 3. Act
        print(f"--- [ACTOR] Acting: {edge.intent} on {edge.target} ---")
        result = await self.motor.act(command)
        
        if result.status == "failed":
            return {"errors": [f"ExecutionError: {result.error}"]}

        return {
            "current_state_id": edge.to_state,
            "errors": []
        }

    def route_after_observe(self, state: AriadneState) -> str:
        """Decide whether to execute, rescue or finish."""
        room_id = state.get("current_state_id")
        
        # Goal achieved?
        if room_id in self.labyrinth.ariadne_map.success_states:
            print("--- [ROUTING] Goal Achieved! ---")
            return END
            
        # Lost?
        if not room_id:
            return "delphi_rescue"
            
        return "execute_deterministic"

    def route_after_execute(self, state: AriadneState) -> str:
        """Check for errors before observing again."""
        if state.get("errors"):
            # If we couldn't find a path, escalate to rescue
            if "NoDeterministicPath" in state["errors"]:
                return "delphi_rescue"
            return "apply_heuristics"
            
        return "observe"

    def build_graph(self) -> StateGraph:
        """Assemble the Theseus LangGraph."""
        workflow = StateGraph(AriadneState)

        workflow.add_node("observe", self.observe)
        workflow.add_node("execute_deterministic", self.execute_deterministic)
        
        # Placeholders for Delphi and Heuristics (to be implemented)
        workflow.add_node("delphi_rescue", self._placeholder_node)
        workflow.add_node("apply_heuristics", self._placeholder_node)

        workflow.set_entry_point("observe")

        workflow.add_conditional_edges(
            "observe",
            self.route_after_observe,
            {
                "execute_deterministic": "execute_deterministic",
                "delphi_rescue": "delphi_rescue",
                END: END
            }
        )

        workflow.add_conditional_edges(
            "execute_deterministic",
            self.route_after_execute,
            {
                "observe": "observe",
                "delphi_rescue": "delphi_rescue",
                "apply_heuristics": "apply_heuristics"
            }
        )

        return workflow

    async def _placeholder_node(self, state: AriadneState) -> Dict[str, Any]:
        """Temporary node for parts not yet implemented."""
        print(f"--- [ACTOR] HIT PLACEHOLDER: Escalating to Human ---")
        return {"session_memory": {**state.get("session_memory", {}), "human_intervention": True}}
