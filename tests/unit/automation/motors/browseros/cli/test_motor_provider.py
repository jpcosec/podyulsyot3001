"""Unit tests for BrowserOSMotorProvider / BrowserOSMotorSession."""
from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.automation.motors.browseros.cli.backend import BrowserOSMotorProvider
from src.automation.motors.browseros.cli.replayer import BrowserOSReplayer


def _fake_client():
    client = MagicMock()
    client.new_hidden_page.return_value = 42
    client.take_snapshot.return_value = []
    client.search_dom.return_value = []
    return client


def test_provider_is_instantiable():
    client = _fake_client()
    provider = BrowserOSMotorProvider(client=client)
    assert hasattr(provider, "open_session")


def test_provider_has_no_portal_map():
    client = _fake_client()
    provider = BrowserOSMotorProvider(client=client)
    assert not hasattr(provider, "portal_map")
    assert not hasattr(provider, "source_name")


@pytest.mark.asyncio
async def test_open_session_opens_and_closes_page():
    client = _fake_client()
    provider = BrowserOSMotorProvider(client=client)

    async with provider.open_session("test-session") as session:
        assert hasattr(session, "observe")
        assert hasattr(session, "execute_step")

    client.new_hidden_page.assert_called_once()
    client.close_page.assert_called_once_with(42)


@pytest.mark.asyncio
async def test_observe_checks_selectors_via_search_dom():
    client = _fake_client()
    client.search_dom.return_value = [1]  # found
    provider = BrowserOSMotorProvider(client=client)

    async with provider.open_session("sess") as session:
        result = await session.observe({"div.apply-btn"})

    assert result == {"div.apply-btn": True}


def test_replayer_has_execute_single_step():
    assert hasattr(BrowserOSReplayer, "execute_single_step")
