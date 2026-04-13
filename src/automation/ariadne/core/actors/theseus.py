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
        """Run the transitional deterministic path."""
        from src.automation.ariadne.graph.orchestrator import (
            observe_node,
            execute_deterministic_node,
        )
        from src.automation.ariadne.core.actors._theseus_debug import (
            should_stop_after_observe,
        )

        updates = await observe_node(state, config or {})
        merged_state = dict(state)
        merged_state.update(updates)
        if should_stop_after_observe(merged_state, updates):
            return updates
        updates.update(await execute_deterministic_node(merged_state, config or {}))
        return updates

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
        from src.automation.ariadne.graph.orchestrator import (
            route_after_observe,
            route_after_deterministic,
            route_after_heuristics,
            route_after_agent,
        )
        from src.automation.ariadne.core.actors._theseus_checkpointer import (
            compile_with_memory,
            compile_with_sqlite,
        )
        from src.automation.ariadne.core.actors._theseus_workflow import build_workflow
        from langgraph.graph import END

        workflow = build_workflow(
            self,
            self._execute_deterministic,
            self._apply_local_heuristics,
            self.delphi,
            self._human_in_the_loop,
        )

        if use_memory:
            yield compile_with_memory(workflow)
        else:
            yield await compile_with_sqlite(workflow, checkpoint_path)

    async def _execute_deterministic(
        self, state: AriadneState, config: dict
    ) -> Dict[str, Any]:
        """Run the transitional deterministic node."""
        from src.automation.ariadne.graph.orchestrator import execute_deterministic_node

        return await execute_deterministic_node(state, config)

    async def _apply_local_heuristics(
        self, state: AriadneState, config: dict
    ) -> Dict[str, Any]:
        """Run the transitional heuristic node."""
        from src.automation.ariadne.graph.orchestrator import (
            apply_local_heuristics_node,
        )

        return await apply_local_heuristics_node(state, config)

    async def _human_in_the_loop(
        self, state: AriadneState, config: dict
    ) -> Dict[str, Any]:
        """Run the transitional HITL node."""
        from src.automation.ariadne.graph.orchestrator import human_in_the_loop_node

        return await human_in_the_loop_node(state, config)
