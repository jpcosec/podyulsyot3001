"""Tests for the Ariadne-to-Crawl4AI Compiler & Serializer."""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from src.automation.ariadne.models import (
    AriadneAction,
    AriadneIntent,
    AriadneObserve,
    AriadnePath,
    AriadnePortalMap,
    AriadneStep,
    AriadneTarget,
)
from src.automation.motors.crawl4ai.compiler.compiler import AriadneC4AICompiler
from src.automation.motors.crawl4ai.compiler.serializer import C4AIScriptSerializer


def test_compile_linkedin_easy_apply_map():
    # Load the real LinkedIn map
    map_path = Path("src/automation/portals/linkedin/maps/easy_apply.json")
    with open(map_path, "r") as f:
        data = json.load(f)

    portal_map = AriadnePortalMap.model_validate(data)
    path = portal_map.paths["standard_easy_apply"]

    # Compile
    compiler = AriadneC4AICompiler()
    ir = compiler.compile(path)

    # Verify IR instructions count (4 steps, with waits and interactions)
    # Step 1: 1 Wait, 1 Click
    # Step 2: 1 Wait, 1 Fill, 1 Click
    # Step 3: 1 Wait, 1 Upload, 1 Click (3)
    # Step 4: 1 Wait, 1 Click (2)
    assert len(ir.instructions) == 10

    # Serialize
    serializer = C4AIScriptSerializer()
    script = serializer.serialize(ir)

    # Basic check of the generated DSL
    assert "WAIT button.jobs-apply-button" in script
    assert "CLICK button.jobs-apply-button" in script
    assert "SET input[name='firstName'] \"{{profile.first_name}}\"" in script
    assert "UPLOAD input[type='file'] \"{{cv_path}}\"" in script
    assert "CLICK button[aria-label='Submit application']" in script


if __name__ == "__main__":
    test_compile_linkedin_easy_apply_map()


def test_compile_upload_letter_intent_uses_upload_instruction():
    compiler = AriadneC4AICompiler()
    path = AriadnePath(
        id="letter-path",
        task_id="task",
        steps=[
            AriadneStep(
                step_index=1,
                name="upload_letter",
                description="Upload cover letter",
                state_id="state",
                observe=AriadneObserve(),
                actions=[
                    AriadneAction(
                        intent=AriadneIntent.UPLOAD_LETTER,
                        target=AriadneTarget(css="input[type='file'][name='letter']"),
                        value="{{letter_path}}",
                    )
                ],
            )
        ],
    )

    script = C4AIScriptSerializer().serialize(compiler.compile(path))

    assert "UPLOAD input[type='file'][name='letter'] \"{{letter_path}}\"" in script
