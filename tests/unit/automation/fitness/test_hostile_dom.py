# Fitness Function 3: DOM Sandbox Hostile Test
# Protege el DOM contra crash en elementos vacíos (void elements)

import pytest
import tempfile
import os
from pathlib import Path


HOSTILE_HTML = """
<!DOCTYPE html>
<html>
<head><title>Hostile DOM Test</title></head>
<body>
    <!-- Void elements that crash appendChild -->
    <input type="text" id="input1" placeholder="Enter text">
    <input type="checkbox" id="check1">
    <img src="fake.jpg" id="img1">
    <br id="br1">
    <hr id="hr1">
    
    <!-- Normal elements -->
    <button id="btn1">Click me</button>
    <div id="div1"><span>Nested</span></div>
    <a href="#" id="link1">Link</a>
    
    <!-- Hidden elements -->
    <div id="hidden1" style="display:none">Hidden</div>
    
    <!-- Overflow hidden -->
    <div id="overflow1" style="overflow:hidden">
        <button>Overflow btn</button>
    </div>
</body>
</html>
"""


@pytest.mark.asyncio
async def test_hinting_js_doesnt_crash_on_void_elements():
    """Fitness: Hinting script doesn't crash on void elements."""
    from src.automation.ariadne.capabilities.hinting import HintingToolImpl

    with tempfile.TemporaryDirectory() as tmpdir:
        html_path = Path(tmpdir) / "hostile.html"
        html_path.write_text(HOSTILE_HTML)

        from unittest.mock import AsyncMock
        from src.automation.ariadne.contracts.base import ExecutionResult

        class ScriptCatcher:
            def __init__(self):
                self.last_script = None

            async def execute(self, command):
                self.last_script = command.script
                return ExecutionResult(
                    status="success",
                    extracted_data={
                        "hint_map": {
                            "AA": {
                                "selector": "[data-ariadne-hint='AA']",
                                "text": "test",
                                "rect": {"x": 10, "y": 10, "w": 50, "h": 20},
                            }
                        }
                    },
                )

        executor = ScriptCatcher()
        tool = HintingToolImpl(executor)

        try:
            hint_map = await tool.inject_hints()
        except Exception as e:
            pytest.fail(f"Hinting crashed on hostile DOM: {e}")

        assert (
            "overlay" in executor.last_script.lower()
            or "insertadjacent" in executor.last_script.lower()
        ), "Hinting should use overlay approach, not appendChild"
