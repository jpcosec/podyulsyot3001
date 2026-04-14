"""Graph builder — composition root.

Loads Labyrinth + Thread, wires nodes and routing, returns a compiled graph.
The CLI only calls:
    graph = build_graph(adapter, portal_name, mission_id)
    await graph.ainvoke({"instruction": "..."})
"""

from __future__ import annotations

from langgraph.graph import StateGraph, END

from src.automation.contracts.sensor import Sensor
from src.automation.contracts.motor import Motor
from src.automation.contracts.state import AriadneState
from src.automation.ariadne.labyrinth.labyrinth import Labyrinth
from src.automation.ariadne.thread.thread import AriadneThread
from src.automation.langgraph.nodes.interpreter import InterpreterNode
from src.automation.langgraph.nodes.observe import ObserveNode
from src.automation.langgraph.nodes.theseus import TheseusNode
from src.automation.langgraph.nodes.delphi import DelphiNode, MAX_FAILURES
from src.automation.langgraph.nodes.recorder import RecorderNode


def build_graph(sensor: Sensor, motor: Motor, portal_name: str, mission_id: str):
    labyrinth = Labyrinth.load(portal_name)
    thread = AriadneThread.load(portal_name, mission_id)

    interpreter = InterpreterNode()
    observe     = ObserveNode(sensor)
    theseus     = TheseusNode(motor, labyrinth, thread)
    delphi      = DelphiNode()
    recorder    = RecorderNode(labyrinth, thread)

    g = StateGraph(AriadneState)
    g.add_node("interpreter", interpreter)
    g.add_node("observe",     observe)
    g.add_node("theseus",     theseus)
    g.add_node("delphi",      delphi)
    g.add_node("recorder",    recorder)

    g.set_entry_point("interpreter")
    g.add_edge("interpreter", "observe")
    g.add_edge("recorder",    "observe")

    g.add_conditional_edges("observe",   _route_after_observe,  {"theseus": "theseus", END: END})
    g.add_conditional_edges("theseus",   _route_after_theseus,  {"recorder": "recorder", "delphi": "delphi", END: END})
    g.add_conditional_edges("delphi",    _route_after_delphi,   {"recorder": "recorder", END: END})

    return g.compile()


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
    if trace:
        return "recorder"
    return END


def _has_fatal(state: AriadneState) -> bool:
    return any("FatalError" in e for e in state.get("errors", []))
