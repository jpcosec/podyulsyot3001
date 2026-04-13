"""Theseus actor - Pure LangGraph implementation from scratch."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Union

from langgraph.graph import END, StateGraph
from src.automation.ariadne.core.cognition import AriadneThread, Labyrinth
from src.automation.ariadne.core.periphery import BrowserAdapter, Motor, Sensor
from src.automation.ariadne.models import AriadneState


class Theseus:
    """
    Deterministic coordinator for Ariadne.
    Owns the LangGraph and coordinates Sensor/Motor/Labyrinth/Thread.
    """

    def __init__(
        self,
        sensor: Sensor,
        motor: Motor,
        labyrinth: Labyrinth,
        thread: AriadneThread,
    ) -> None:
        self.sensor = sensor
        self.motor = motor
        self.labyrinth = labyrinth
        self.thread = thread

    async def observe(self, state: AriadneState) -> Dict[str, Any]:
        """Capture the current JIT state and identify the room."""
        print("--- [NODE] Observe ---")
        if not await self.sensor.is_healthy():
            return {"errors": ["Sensor unhealthy"]}

        snapshot = await self.sensor.perceive()
        room_id = await self.labyrinth.identify_room(snapshot)
        
        # Check if goal was reached
        goal_achieved = False
        if room_id in self.labyrinth.ariadne_map.success_states:
            goal_achieved = True

        return {
            "current_url": snapshot.url,
            "dom_elements": snapshot.dom_elements,
            "screenshot_b64": snapshot.screenshot_b64,
            "current_state_id": room_id,
            "session_memory": {
                **state.get("session_memory", {}),
                "goal_achieved": goal_achieved
            }
        }

    async def execute_deterministic(self, state: AriadneState) -> Dict[str, Any]:
        """Plan and execute the next deterministic step."""
        print("--- [NODE] Execute Deterministic ---")
        current_room = state.get("current_state_id")
        if not current_room:
            return {"errors": ["Unknown room - cannot execute deterministically"]}

        edge = self.thread.get_next_step(current_room)
        if not edge:
            return {"errors": ["No deterministic path found"]}

        # For scratch implementation, we simplify translation 
        # In a real scenario, this would use TranslatorRegistry
        print(f"[⚡] Taking edge: {edge.from_state} -> {edge.to_state} ({edge.intent})")
        
        # NOTE: This is a placeholder for actual translation logic
        # For now we assume a raw command or simple mapping
        from src.automation.ariadne.contracts.base import BrowserOSCommand
        command = BrowserOSCommand(tool="click", selector_text=edge.target)
        
        result = await self.motor.act(command)
        if result.status == "failed":
            return {"errors": [f"Execution failed: {result.error}"]}

        return {
            "current_state_id": edge.to_state,
            "errors": []
        }

    def route_after_observe(self, state: AriadneState) -> str:
        """Route based on observation result."""
        if state.get("session_memory", {}).get("goal_achieved"):
            return END
        if not state.get("current_state_id"):
            return "llm_rescue" # Placeholder for Delphi
        return "execute_deterministic"

    def route_after_execute(self, state: AriadneState) -> str:
        """Route back to observe after execution."""
        if state.get("errors"):
            return "apply_heuristics" # Placeholder for Heuristics
        return "observe"

    def build_graph(self) -> StateGraph:
        """Assemble the LangGraph."""
        workflow = StateGraph(AriadneState)
        
        workflow.add_node("observe", self.observe)
        workflow.add_node("execute_deterministic", self.execute_deterministic)
        
        workflow.set_entry_point("observe")
        
        workflow.add_conditional_edges(
            "observe",
            self.route_after_observe,
            {
                "execute_deterministic": "execute_deterministic",
                "llm_rescue": END, # TODO: Add Delphi
                END: END
            }
        )
        
        workflow.add_conditional_edges(
            "execute_deterministic",
            self.route_after_execute,
            {
                "observe": "observe",
                "apply_heuristics": END # TODO: Add Heuristics
            }
        )
        
        return workflow
