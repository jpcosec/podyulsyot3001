#!/usr/bin/env python3
"""
Test Corneta: Fuerza la cascada de fallos de Ariadne 2.0.
Determinista -> Heurísticas -> Agente LLM -> HITL.

Usage:
    python scripts/test_corneta.py

Requires:
    - GEMINI_API_KEY or GOOGLE_API_KEY in environment
    - Crawl4AI installed
"""

import asyncio
import os
import uuid

from src.automation.ariadne.graph.orchestrator import create_ariadne_graph
from src.automation.motors.crawl4ai.executor import Crawl4AIExecutor


async def run_test():
    print("\n[🚀] Iniciando Test Corneta en example.com...")

    thread_id = str(uuid.uuid4())
    initial_state = {
        "job_id": "test_123",
        "portal_name": "example",
        "profile_data": {},
        "job_data": {},
        "path_id": "test_cascade",
        "current_mission_id": "test",
        "current_state_id": "home",
        "current_url": "https://example.com",
        "dom_elements": [],
        "screenshot_b64": None,
        "session_memory": {},
        "errors": [],
        "history": [],
        "portal_mode": "example",
        "patched_components": {},
    }

    executor = Crawl4AIExecutor()

    config = {
        "configurable": {
            "thread_id": thread_id,
            "executor": executor,
            "motor_name": "crawl4ai",
            "record_graph": True,
            "recording_dir": "data/ariadne/recordings",
        }
    }

    print(f"[⚡] Thread ID: {thread_id}")
    print("[⚡] Ejecutando Grafo (Observa la terminal para ver los nodos)...\n")

    async with executor:
        async with create_ariadne_graph(use_memory=True) as app:
            async for event in app.astream(
                initial_state, config, stream_mode="updates"
            ):
                for node, state_update in event.items():
                    print(f"\n[🔄] Nodo completado: {node.upper()}")
                    if "errors" in state_update and state_update["errors"]:
                        print(f"     [⚠️] Errores reportados: {state_update['errors']}")
                    if "session_memory" in state_update:
                        failures = state_update["session_memory"].get(
                            "agent_failures", 0
                        )
                        if failures > 0:
                            print(f"     [🧠] Fallos del Agente: {failures}/3")

            final_state = await app.aget_state(config)

            print("\n" + "=" * 50)
            print("[🛑] EJECUCIÓN DETENIDA")
            print("=" * 50)

            if final_state.next and final_state.next[0] == "human_in_the_loop":
                print(
                    "\n[✅] ÉXITO DEL TEST: El sistema alcanzó el breakpoint de HITL correctamente."
                )
                print(
                    "El determinismo falló, las heurísticas fallaron, el agente falló, y el humano fue llamado."
                )
            else:
                print(
                    f"\n[❌] FALLO DEL TEST: El sistema se detuvo en: {final_state.next}"
                )

            print(
                f"\n[💾] Revisa los logs de la sesión en: data/ariadne/recordings/{thread_id}/raw_timeline.jsonl"
            )


if __name__ == "__main__":
    asyncio.run(run_test())
