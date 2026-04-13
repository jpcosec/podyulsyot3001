"""Theseus deterministic coordinator."""

from __future__ import annotations

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator, Dict

from src.automation.ariadne.core.actors.delphi import Delphi
from src.automation.ariadne.core.actors.recorder import Recorder
from src.automation.ariadne.core.cognition import AriadneThread, Labyrinth
from src.automation.ariadne.core.periphery import Motor, Sensor
from src.automation.ariadne.models import AriadneState
from src.automation.adapters.translators.registry import TranslatorRegistry


class Theseus:
    """Deterministic-first coordinator for Ariadne runtime flows."""

    def __init__(
        self,
        sensor: Sensor,
        motor: Motor,
        labyrinth: Labyrinth,
        thread: AriadneThread,
        delphi: Delphi | None = None,
        recorder: Recorder | None = None,
    ) -> None:
        self.sensor = sensor
        self.motor = motor
        self.labyrinth = labyrinth
        self.thread = thread
        self.delphi = delphi or Delphi(sensor, motor, labyrinth=labyrinth)
        self.recorder = recorder or Recorder(labyrinth, thread)

    async def __call__(
        self, state: AriadneState, config: Any | None = None
    ) -> Dict[str, Any]:
        """Run the transitional deterministic path (legacy graph compatibility)."""
        # This allows Theseus to be a single node in a larger graph if needed,
        # but primarily we use the individual methods as nodes in Theseus's graph.
        return await self.observe(state, config or {})

    async def observe(self, state: AriadneState, config: dict) -> Dict[str, Any]:
        """Captures the JIT state (URL, DOM, Screenshot) via the active Sensor."""
        print("--- ACTOR: Theseus/Observe ---")
        if not await self.sensor.is_healthy():
            return {"errors": ["FatalError: Sensor is down or disconnected."]}

        from src.automation.ariadne.graph._orchestrator_helpers import (
            _snapshot_updates,
            _apply_identified_state,
            _danger_signals,
            _update_danger_memory,
            _mark_goal_achieved,
            _record_observe_event,
        )
        from src.automation.ariadne.modes.registry import ModeRegistry

        try:
            snapshot = await self.sensor.perceive()
            updates = _snapshot_updates(snapshot)
            
            # Use injected Labyrinth
            identified_state_id = await self.labyrinth.identify_room(snapshot)
            ariadne_map = self.labyrinth.ariadne_map
            
            _apply_identified_state(updates, identified_state_id)
            
            mode = ModeRegistry.get_mode_for_url(snapshot.url)
            danger_report = await mode.inspect_danger(_danger_signals(snapshot))
            _update_danger_memory(updates, state, danger_report)
            
            _mark_goal_achieved(updates, state, identified_state_id, ariadne_map)
            
            # Injection for helpers that still expect labyrinth in config
            cfg_with_lab = config.copy()
            if "configurable" not in cfg_with_lab: cfg_with_lab["configurable"] = {}
            cfg_with_lab["configurable"]["labyrinth"] = self.labyrinth
            
            await _record_observe_event(cfg_with_lab, state, updates, snapshot)
            return updates
        except Exception as e:
            return {"errors": [f"ObservationError: {str(e)}"]}

    async def execute_deterministic(self, state: AriadneState, config: dict) -> Dict[str, Any]:
        """Executes the next deterministic step from the AriadneThread."""
        print("--- ACTOR: Theseus/Execute ---")
        print(f"DEBUG: motor is_healthy? {await self.motor.is_healthy()}")
        print(f"DEBUG: current_state_id: {state.get('current_state_id')}")
        if not await self.motor.is_healthy():
            return {"errors": ["FatalError: Motor is down or disconnected."]}

        current_state_id = state.get("current_state_id")
        if not current_state_id:
            return {"errors": ["StateError: No current_state_id found in state."]}

        from src.automation.ariadne.graph._orchestrator_helpers import (
            _translate_command,
            _execution_failed,
            _deterministic_updates,
            _record_deterministic_event,
        )

        # Use injected Thread
        edge = self.thread.get_next_step(current_state_id)
        if not edge:
            # No deterministic path; graph routing will handle escalation to Delphi
            return {"errors": [f"NoTransitionError: No deterministic edge from '{current_state_id}'"]}

        # Micro-batching is currently handled in the orchestrator helpers, 
        # but for now we follow the simple path.
        batch = [edge]
        
        motor_name = config.get("configurable", {}).get("motor_name", "crawl4ai")
        translator = TranslatorRegistry.get_translator_by_name(motor_name)
        
        try:
            command = _translate_command(batch, translator, self.labyrinth.ariadne_map, state)
            print(f"--- Dispatching Command: {command} ---")
            
            result = await self.motor.act(command)
            failure = _execution_failed(result)
            if failure is not None:
                return failure
                
            try:
                print(f"DEBUG: calling _deterministic_updates with batch size {len(batch)} and result {result}")
                updates = _deterministic_updates(state, batch, result)
                print(f"DEBUG: updates from _deterministic_updates: {updates}")
            except Exception as e:
                print(f"DEBUG: _deterministic_updates failed with: {str(e)}")
                import traceback
                traceback.print_exc()
                return {"errors": [f"InternalError: {str(e)}"]}
            
            # Injection for recorder/helpers
            cfg_with_cognition = config.copy()
            if "configurable" not in cfg_with_cognition: cfg_with_cognition["configurable"] = {}
            cfg_with_cognition["configurable"]["labyrinth"] = self.labyrinth
            cfg_with_cognition["configurable"]["ariadne_thread"] = self.thread
            
            await _record_deterministic_event(cfg_with_cognition, state, batch, result, updates)
            return updates
        except Exception as e:
            return {"errors": [f"ExecutionError: {str(e)}"]}

    async def apply_local_heuristics(self, state: AriadneState, config: dict) -> Dict[str, Any]:
        """Applies JIT patches from the portal mode heuristics."""
        print("--- ACTOR: Theseus/Heuristics ---")
        from src.automation.ariadne.graph._orchestrator_helpers import (
            _resolve_mode,
            _apply_heuristic_patches,
        )
        
        mode = _resolve_mode(state)
        current_state_id = state.get("current_state_id")
        definition = self.labyrinth.ariadne_map.states.get(current_state_id)
        
        if not definition:
            return {"errors": [f"StateDefinitionNotFoundError: {current_state_id}"]}

        return await _apply_heuristic_patches(definition, current_state_id, state, mode)

    async def human_in_the_loop(self, state: AriadneState, config: dict) -> Dict[str, Any]:
        """Standard HITL pause point."""
        print("--- ACTOR: Theseus/HITL ---")
        new_memory = state.get("session_memory", {}).copy()
        new_memory["human_intervention"] = True
        return {"session_memory": new_memory}

    async def run(self, initial_state: AriadneState, config: dict):
        """Run a graph session owned by Theseus."""
        async with self.graph_context() as app:
            async for chunk in app.astream(
                initial_state, config, stream_mode="updates"
            ):
                from src.automation.ariadne.core.actors._theseus_debug import (
                    print_streamed_updates,
                )
                print_streamed_updates(chunk)
            return await app.aget_state(config)

    @asynccontextmanager
    async def graph_context(
        self,
        checkpoint_path: Path | str | None = None,
        use_memory: bool = False,
    ) -> AsyncIterator[Any]:
        """Yield a compiled LangGraph owned by Theseus."""
        from src.automation.ariadne.core.actors._theseus_checkpointer import (
            compile_with_memory,
            compile_with_sqlite,
        )
        from src.automation.ariadne.core.actors._theseus_workflow import build_workflow

        # Note: Delphi is also an actor, we pass its __call__
        workflow = build_workflow(
            self.observe,
            self.execute_deterministic,
            self.apply_local_heuristics,
            self.delphi,
            self.human_in_the_loop,
        )

        if use_memory:
            yield compile_with_memory(workflow)
        else:
            yield await compile_with_sqlite(workflow, checkpoint_path)
