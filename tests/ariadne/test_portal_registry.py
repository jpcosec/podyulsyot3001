import pytest
from unittest.mock import patch, MagicMock

from src.automation.ariadne.portal_registry import PortalRegistry


def make_pair():
    return MagicMock(), MagicMock()


class TestPortalRegistry:
    def test_get_loads_labyrinth_and_thread(self, tmp_path):
        with patch("src.automation.ariadne.portal_registry.Labyrinth") as MockLab, \
             patch("src.automation.ariadne.portal_registry.AriadneThread") as MockThread:
            reg = PortalRegistry("mission1")
            reg.get("emol.com")
            MockLab.load.assert_called_once_with("emol.com")
            MockThread.load.assert_called_once_with("emol.com", "mission1")

    def test_get_caches_on_second_call(self):
        with patch("src.automation.ariadne.portal_registry.Labyrinth") as MockLab, \
             patch("src.automation.ariadne.portal_registry.AriadneThread") as MockThread:
            reg = PortalRegistry("m")
            reg.get("emol.com")
            reg.get("emol.com")
            assert MockLab.load.call_count == 1
            assert MockThread.load.call_count == 1

    def test_different_domains_load_independently(self):
        with patch("src.automation.ariadne.portal_registry.Labyrinth") as MockLab, \
             patch("src.automation.ariadne.portal_registry.AriadneThread") as MockThread:
            reg = PortalRegistry("m")
            reg.get("emol.com")
            reg.get("stepstone.de")
            assert MockLab.load.call_count == 2

    def test_save_calls_save_on_both(self):
        with patch("src.automation.ariadne.portal_registry.Labyrinth") as MockLab, \
             patch("src.automation.ariadne.portal_registry.AriadneThread") as MockThread:
            reg = PortalRegistry("m")
            reg.get("emol.com")
            reg.save("emol.com")
            MockLab.load.return_value.save.assert_called_once()
            MockThread.load.return_value.save.assert_called_once()

    def test_save_unknown_domain_is_noop(self):
        reg = PortalRegistry("m")
        reg.save("never-visited.com")  # no error
