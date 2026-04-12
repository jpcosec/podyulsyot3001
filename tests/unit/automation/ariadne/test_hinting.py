import pytest
from unittest.mock import AsyncMock
from pathlib import Path

from src.automation.ariadne.capabilities.hinting import HintingToolImpl
from src.automation.ariadne.contracts.base import (
    ExecutionResult,
    AriadneTarget,
    ScriptCommand,
)


@pytest.mark.asyncio
async def test_hinting_tool_inject_hints():
    # Mock executor
    executor = AsyncMock()
    executor.execute.return_value = ExecutionResult(
        status="success",
        extracted_data={
            "hint_map": {
                "AA": {
                    "selector": "[data-ariadne-hint='AA']",
                    "text": "Click me",
                    "rect": {"x": 10, "y": 10, "width": 50, "height": 20},
                },
                "AB": {
                    "selector": "[data-ariadne-hint='AB']",
                    "text": "Submit",
                    "rect": {"x": 100, "y": 10, "width": 80, "height": 30},
                },
            }
        },
    )

    tool = HintingToolImpl(executor)

    # Inject hints
    hint_map = await tool.inject_hints()

    assert len(hint_map) == 2
    assert hint_map["AA"] == "[data-ariadne-hint='AA']"
    assert hint_map["AB"] == "[data-ariadne-hint='AB']"

    # Check that executor was called with ScriptCommand and the script content
    args, kwargs = executor.execute.call_args
    command = args[0]
    assert isinstance(command, ScriptCommand)
    assert "data-ariadne-hint-label" in command.script
    assert "el.appendChild(label)" in command.script


@pytest.mark.asyncio
async def test_hinting_tool_resolve_hint():
    # Mock executor
    executor = AsyncMock()
    executor.execute.return_value = ExecutionResult(
        status="success",
        extracted_data={
            "hint_map": {
                "AA": {
                    "selector": "[data-ariadne-hint='AA']",
                    "text": "Click me",
                    "rect": {"x": 10, "y": 10, "width": 50, "height": 20},
                },
            }
        },
    )

    tool = HintingToolImpl(executor)
    await tool.inject_hints()

    # Resolve hint
    target = await tool.resolve_hint("AA")

    assert isinstance(target, AriadneTarget)
    assert target.hint == "AA"
    assert target.css == "[data-ariadne-hint='AA']"
    assert target.text == "Click me"
    assert target.vision == {"x": 10, "y": 10, "width": 50, "height": 20}

    # Case-insensitive resolution
    target_lower = await tool.resolve_hint("aa")
    assert target_lower.hint == "AA"

    # Unknown hint
    assert await tool.resolve_hint("ZZ") is None
