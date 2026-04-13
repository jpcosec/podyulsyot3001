# Unit tests for Graph Routing (Conditional Edges)
# Consolidates test_dynamic_edge_evaluation and test_mission_pathfinding

import pytest
from src.automation.ariadne.graph import orchestrator as orch


class TestRouteAfterObserve:
    """Test route_after_observe function."""

    def test_route_to_deterministic_when_state_identified(self):
        """State identified -> execute_deterministic"""
        state = {"current_state_id": "job_details", "session_memory": {}}
        result = orch.route_after_observe(state)
        assert result == "execute_deterministic"

    def test_route_to_deterministic_when_no_goal(self):
        """No goal achieved -> execute_deterministic"""
        state = {
            "current_state_id": "job_details",
            "session_memory": {"goal_achieved": False},
        }
        result = orch.route_after_observe(state)
        assert result == "execute_deterministic"

    def test_route_to_end_on_goal_achieved(self):
        """Goal achieved -> END"""
        state = {
            "current_state_id": "job_details",
            "session_memory": {"goal_achieved": True},
        }
        result = orch.route_after_observe(state)
        assert result == orch.END

    def test_route_to_hitl_on_danger(self):
        """Danger detected -> human_in_the_loop"""
        state = {
            "current_state_id": "job_details",
            "session_memory": {"danger_detected": True, "goal_achieved": False},
        }
        result = orch.route_after_observe(state)
        assert result == "human_in_the_loop"


class TestRouteAfterDeterministic:
    """Test route_after_deterministic function."""

    def test_route_to_observe_on_success(self):
        """Execution success -> observe"""
        state = {"errors": [], "session_memory": {}}
        result = orch.route_after_deterministic(state)
        assert result == "observe"

    def test_route_to_heuristics_on_failure(self):
        """Execution failed -> heuristics"""
        state = {"errors": ["ClickFailed"], "session_memory": {}}
        result = orch.route_after_deterministic(state)
        assert result == "apply_local_heuristics"


class TestRouteAfterHeuristics:
    """Test route_after_heuristics function."""

    def test_route_to_llm_rescue_on_errors(self):
        """Has errors -> LLM rescue"""
        state = {"errors": ["HeuristicFailed"], "session_memory": {}}
        result = orch.route_after_heuristics(state)
        assert result == "llm_rescue_agent"

    def test_route_to_llm_rescue_on_max_retries(self):
        """Max retries reached -> LLM rescue"""
        state = {"errors": [], "session_memory": {"heuristic_retries": 2}}
        result = orch.route_after_heuristics(state)
        assert result == "llm_rescue_agent"

    def test_route_to_deterministic_on_retry(self):
        """Under max retries -> execute_deterministic"""
        state = {"errors": [], "session_memory": {"heuristic_retries": 1}}
        result = orch.route_after_heuristics(state)
        assert result == "execute_deterministic"


class TestRouteAfterAgent:
    """Test route_after_agent function (Circuit Breaker)."""

    def test_route_to_observe_on_recovery(self):
        """No errors, no failures -> observe"""
        state = {"errors": [], "session_memory": {"agent_failures": 0}}
        result = orch.route_after_agent(state)
        assert result == "observe"

    def test_route_to_hitl_after_max_retries(self):
        """3 failures reached -> human_in_the_loop"""
        state = {"session_memory": {"agent_failures": 3}}
        result = orch.route_after_agent(state)
        assert result == "human_in_the_loop"

    def test_route_to_hitl_on_errors(self):
        """Has errors -> human_in_the_loop"""
        state = {"errors": ["AgentError"], "session_memory": {"agent_failures": 1}}
        result = orch.route_after_agent(state)
        assert result == "human_in_the_loop"

    def test_route_to_hitl_on_give_up(self):
        """give_up flag set -> human_in_the_loop"""
        state = {"errors": [], "session_memory": {"give_up": True, "agent_failures": 1}}
        result = orch.route_after_agent(state)
        assert result == "human_in_the_loop"

    def test_route_to_observe_under_max_retries(self):
        """Under 3 failures -> observe"""
        state = {"errors": [], "session_memory": {"agent_failures": 2}}
        result = orch.route_after_agent(state)
        assert result == "observe"
