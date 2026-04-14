"""Graph builder — composition root.

Builds a PortalRegistry keyed by mission_id, then wires nodes and routing.
Portals (Labyrinth + Thread) are loaded lazily per domain as the browser navigates.

The CLI calls:
    graph = build_graph(sensor, motor, portal_name, mission_id)
    await graph.ainvoke({"instruction": "..."})
"""

from __future__ import annotations

import os

from langgraph.graph import StateGraph, END

from src.automation.contracts.sensor import Sensor
from src.automation.contracts.motor import Motor
from src.automation.contracts.state import AriadneState
from src.automation.ariadne.portal_registry import PortalRegistry
from src.automation.adapters.gemini import GeminiClient
from src.automation.adapters.portal_extractor import PortalExtractor
from src.automation.ariadne.extraction.portal_dictionary import PortalDictionary
from src.automation.ariadne.extraction.schema_builder import SchemaBuilder
from src.automation.langgraph.nodes.interpreter import InterpreterNode
from src.automation.langgraph.nodes.observe import ObserveNode
from src.automation.langgraph.nodes.theseus import TheseusNode
from src.automation.langgraph.nodes.delphi import DelphiNode, MAX_FAILURES
from src.automation.langgraph.nodes.recorder import RecorderNode


def build_graph(sensor: Sensor, motor: Motor, portal_name: str, mission_id: str):
    registry = PortalRegistry(mission_id)
    llm = GeminiClient(
        api_key=os.environ["GOOGLE_API_KEY"],
        model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    )

    schema_builder = SchemaBuilder(portal_name, _llm_config())
    extractor = PortalExtractor(PortalDictionary.load(portal_name, schema_builder))

    interpreter = InterpreterNode()
    observe     = ObserveNode(sensor)
    theseus     = TheseusNode(motor, registry, extractor)
    delphi      = DelphiNode(motor, _labyrinth_for(registry, portal_name), llm)
    recorder    = RecorderNode(registry)

    g = StateGraph(AriadneState)
    g.add_node("interpreter", interpreter)
    g.add_node("observe",     observe)
    g.add_node("theseus",     theseus)
    g.add_node("delphi",      delphi)
    g.add_node("recorder",    recorder)

    g.set_entry_point("interpreter")
    g.add_edge("interpreter", "observe")
    g.add_edge("recorder",    "observe")

    g.add_conditional_edges("observe",  _route_after_observe, {"theseus": "theseus", END: END})
    g.add_conditional_edges("theseus",  _route_after_theseus, {"recorder": "recorder", "delphi": "delphi", END: END})
    g.add_conditional_edges("delphi",   _route_after_delphi,  {"recorder": "recorder", END: END})

    return g.compile()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _labyrinth_for(registry: PortalRegistry, portal_name: str):
    """Provide the initial-domain Labyrinth to DelphiNode (it holds a fixed ref)."""
    labyrinth, _ = registry.get(portal_name)
    return labyrinth


# ── Routing ───────────────────────────────────────────────────────────────────

def _route_after_observe(state: AriadneState) -> str:
    if _has_fatal(state):
        return END
    return "theseus"


def _route_after_theseus(state: AriadneState) -> str:
    if _has_fatal(state) or state.get("is_mission_complete"):
        return END
    if not state.get("current_room_id"):
        return "delphi"
    trace = state.get("trace", [])
    if not trace or (trace and not trace[-1].success):
        return "delphi"
    return "recorder"


def _route_after_delphi(state: AriadneState) -> str:
    if state.get("agent_failures", 0) >= MAX_FAILURES:
        return END
    if _has_fatal(state):
        return END
    trace = state.get("trace", [])
    return "recorder" if trace else END


def _has_fatal(state: AriadneState) -> bool:
    return any("FatalError" in e for e in state.get("errors", []))


def _llm_config():
    from crawl4ai import LLMConfig
    return LLMConfig(
        provider=f"gemini/{os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')}",
        api_token=os.environ["GOOGLE_API_KEY"],
    )
