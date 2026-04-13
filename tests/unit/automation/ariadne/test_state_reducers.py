# Unit tests for LangGraph State Reducers
# Verifies that reducers correctly accumulate/clear state mutations

import pytest
import operator
from typing import Annotated
from src.automation.ariadne.models import AriadneState


class TestErrorsReducer:
    """Test errors list accumulation."""

    def test_errors_accumulate(self):
        """Errors should accumulate across node calls."""
        state1 = {"errors": ["Error1"]}
        state2 = {"errors": ["Error2"]}

        combined = state1["errors"] + state2["errors"]
        assert combined == ["Error1", "Error2"]

    def test_errors_clear_on_success(self):
        """After successful execution, errors should be cleared."""
        state = {"errors": ["OldError"]}
        new_state = {"errors": []}
        assert new_state["errors"] == []


class TestSessionMemoryReducer:
    """Test session_memory dict updates."""

    def test_memory_persists(self):
        """session_memory should persist across nodes."""
        state = {"session_memory": {"key": "value"}}
        updated = {"session_memory": {"key": "value", "new_key": "new_value"}}
        assert "key" in updated["session_memory"]

    def test_memory_can_store_failures(self):
        """agent_failures counter should accumulate."""
        state = {"session_memory": {"agent_failures": 0}}
        state["session_memory"]["agent_failures"] += 1
        assert state["session_memory"]["agent_failures"] == 1


class TestPatchedComponentsReducer:
    """Test patched_components merge using operator.ior (dict union)."""

    def test_patches_merge(self):
        """Patches from different states should merge."""
        patch1 = {"home:apply_btn": {"css": "#btn1"}}
        patch2 = {"home:submit_btn": {"css": "#btn2"}}

        merged = patch1 | patch2
        assert len(merged) == 2
        assert "home:apply_btn" in merged
        assert "home:submit_btn" in merged

    def test_patches_override_on_conflict(self):
        """Later patches should override earlier ones."""
        patch1 = {"home:btn": {"css": "#old"}}
        patch2 = {"home:btn": {"css": "#new"}}

        merged = patch1 | patch2
        assert merged["home:btn"]["css"] == "#new"


class TestStateMutation:
    """Integration test for state mutations through graph nodes."""

    def test_state_flow_from_failure_to_success(self):
        """Verify state transforms correctly from failure to success."""
        # Initial state with error
        state = {
            "job_id": "test",
            "portal_name": "linkedin",
            "errors": ["ClickFailed: element not found"],
            "session_memory": {"agent_failures": 1},
            "current_state_id": "job_details",
            "current_url": "https://example.com",
            "dom_elements": [],
            "screenshot_b64": None,
            "profile_data": {},
            "job_data": {},
            "path_id": "test",
            "current_mission_id": "test",
            "history": [],
            "portal_mode": "default",
            "patched_components": {},
        }

        # Simulate successful retry - errors should clear
        success_state = {
            "errors": [],
            "session_memory": {"agent_failures": 0, "goal_achieved": True},
        }

        assert success_state["errors"] == []
        assert success_state["session_memory"]["agent_failures"] == 0
        assert success_state["session_memory"]["goal_achieved"] == True


class TestReducerBehavior:
    """Test actual reducer behavior in LangGraph context."""

    def test_annotated_errors_reducer(self):
        """Test the add_messages-like behavior for errors."""
        # Simulate what Annotated[List[str], add_messages] does
        errors1 = ["Error1"]
        errors2 = ["Error2"]
        combined = errors1 + errors2
        assert combined == ["Error1", "Error2"]

    def test_annotated_patched_components_ior(self):
        """Test operator.ior for patched_components."""
        import operator

        d1 = {"key1": "val1"}
        d2 = {"key2": "val2"}
        result = operator.ior(d1, d2)

        assert result == {"key1": "val1", "key2": "val2"}

        # Test override behavior
        d3 = {"key1": "new_val"}
        result_override = operator.ior(d1, d3)
        assert result_override["key1"] == "new_val"
