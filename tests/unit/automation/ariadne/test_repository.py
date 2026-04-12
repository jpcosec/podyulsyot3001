"""Unit tests for MapRepository caching."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from src.automation.ariadne.repository import MapRepository


def _create_test_map(portal_name: str, map_type: str) -> dict:
    """Create a minimal test map JSON."""
    return {
        "meta": {"source": portal_name, "flow": map_type},
        "states": {
            "start": {
                "id": "start",
                "description": "Start state",
                "presence_predicate": {"required_elements": [], "logical_op": "AND"},
                "components": {},
            }
        },
        "edges": [],
        "success_states": ["complete"],
        "failure_states": [],
    }


@pytest.fixture
def temp_map_dir():
    """Create a temporary directory with test map files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        # Create test portals
        for portal in ["linkedin", "indeed"]:
            portal_dir = base / portal / "maps"
            portal_dir.mkdir(parents=True)
            # Write easy_apply map
            map_data = _create_test_map(portal, "easy_apply")
            with open(portal_dir / "easy_apply.json", "w") as f:
                json.dump(map_data, f)
        yield base


@pytest.mark.asyncio
async def test_get_map_async_caches_on_first_call(temp_map_dir):
    """First async call should load from disk and cache."""
    MapRepository._map_cache.clear()
    repo = MapRepository(base_dir=temp_map_dir)

    # First call - should read from disk
    map1 = await repo.get_map_async("linkedin", "easy_apply")

    # Should be cached now
    assert "linkedin:easy_apply" in MapRepository._map_cache
    assert MapRepository._map_cache["linkedin:easy_apply"] is map1


@pytest.mark.asyncio
async def test_get_map_async_returns_cached_on_second_call(temp_map_dir):
    """Second async call should return cached value without hitting disk."""
    MapRepository._map_cache.clear()
    repo = MapRepository(base_dir=temp_map_dir)

    # First call
    map1 = await repo.get_map_async("linkedin", "easy_apply")

    # Clear the base dir to prove cache hit
    (temp_map_dir / "linkedin" / "maps" / "easy_apply.json").unlink()

    # Second call - should use cache, not hit disk
    map2 = await repo.get_map_async("linkedin", "easy_apply")

    assert map1 is map2


@pytest.mark.asyncio
async def test_get_map_async_different_portals_separate_caches(temp_map_dir):
    """Different portals should have separate cache entries."""
    MapRepository._map_cache.clear()
    repo = MapRepository(base_dir=temp_map_dir)

    map_linkedin = await repo.get_map_async("linkedin", "easy_apply")
    map_indeed = await repo.get_map_async("indeed", "easy_apply")

    assert map_linkedin.meta.source == "linkedin"
    assert map_indeed.meta.source == "indeed"
    assert len(MapRepository._map_cache) == 2


def test_get_map_sync_uses_cache(temp_map_dir):
    """Sync get_map should also use cache via run_until_complete."""
    MapRepository._map_cache.clear()
    repo = MapRepository(base_dir=temp_map_dir)

    # First sync call
    map1 = repo.get_map("linkedin", "easy_apply")
    assert "linkedin:easy_apply" in MapRepository._map_cache

    # Second sync call - should use cache
    map2 = repo.get_map("linkedin", "easy_apply")
    assert map1 is map2


def test_get_map_sync_falls_back_to_async_for_first_call(temp_map_dir):
    """Sync get_map should work via run_until_complete for first call."""
    MapRepository._map_cache.clear()
    repo = MapRepository(base_dir=temp_map_dir)

    map1 = repo.get_map("linkedin", "easy_apply")
    assert map1.meta.source == "linkedin"
