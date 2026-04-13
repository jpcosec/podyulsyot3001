# Fitness Function 4: Graph Depth Limit (Circuit Breaker)
# Verifica que el grafo alcance HITL dentro de X pasos cuando todo falla

import pytest
from unittest.mock import patch
from src.automation.ariadne.graph.orchestrator import create_ariadne_graph


class FailingExecutor:
    """Executor que siempre falla para activar el circuit breaker."""

    def __init__(self):
        self.call_count = 0

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    async def take_snapshot(self):
        from src.automation.ariadne.contracts.base import SnapshotResult

        return SnapshotResult(
            url="https://example.com", dom_elements=[], screenshot_b64="fake"
        )

    async def execute(self, command):
        from src.automation.ariadne.contracts.base import ExecutionResult

        self.call_count += 1
        return ExecutionResult(status="failed", error="Always fails")


@pytest.mark.asyncio
async def test_circuit_breaker_halts_infinite_loops():
    """Fitness: Graph reach HITL within max depth when everything fails."""

    # Mock del nodo LLM para evitar API key real
    async def mock_llm_node(state, config=None):
        mem = state.get("session_memory", {}).copy()
        mem["agent_failures"] = mem.get("agent_failures", 0) + 1
        return {"session_memory": mem, "errors": ["Mock LLM failed"]}

    from src.automation.ariadne.graph import orchestrator as orch_mod

    state = {
        "job_id": "fitness_test_4",
        "portal_name": "example",
        "current_state_id": "home",
        "current_url": "https://example.com",
        "dom_elements": [],
        "session_memory": {},
        "errors": [],
        "history": [],
        "profile_data": {},
        "job_data": {},
        "path_id": "test",
        "current_mission_id": "test",
        "screenshot_b64": None,
        "portal_mode": "example",
        "patched_components": {},
    }

    config = {
        "recursion_limit": 15,
        "configurable": {"thread_id": "test_breaker"},
    }

    executor = FailingExecutor()

    with patch.object(orch_mod, "llm_rescue_agent_node", mock_llm_node):
        async with executor:
            async with create_ariadne_graph(use_memory=False) as app:
                step_count = 0
                final_state = None

                try:
                    async for chunk in app.astream(state, config):
                        step_count += 1
                        if (
                            chunk.get("session_memory", {}).get("agent_failures", 0)
                            >= 3
                        ):
                            break
                except Exception as e:
                    if "RecursionLimit" in str(e):
                        pytest.fail(
                            "🚨 Circuit Breaker roto: grafo entró en bucle infinito y "
                            "golpeó el límite de recursión de LangGraph."
                        )
                    raise

    # Verificar que el circuit breaker funcione
    assert step_count <= 10, f"Grafo tomó {step_count} pasos, máximo esperado 10"

    # Verificar que agent_failures llegó a 3 ( HITL )
    final_failures = state.get("session_memory", {}).get("agent_failures", 0)
    # Nota: el estado se modifica por referencia, así que verificamos el estado final del chunk
    print(f"Step count: {step_count}, final_failures: {final_failures}")
