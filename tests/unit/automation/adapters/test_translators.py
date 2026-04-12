"""Tests for translator registry."""

import pytest

from src.automation.ariadne.contracts.base import (
    BrowserOSCommand,
    CrawlCommand,
)
from src.automation.adapters.translators.registry import TranslatorRegistry
from src.automation.adapters.translators.browseros import BrowserOSTranslator
from src.automation.adapters.translators.crawl4ai import Crawl4AITranslator


class TestTranslatorRegistry:
    """Tests for TranslatorRegistry."""

    def test_get_translator_for_browseros_command(self):
        """Test getting translator for BrowserOSCommand."""
        # Reset the registry to ensure fresh discovery
        TranslatorRegistry._loaded = False
        TranslatorRegistry._by_command.clear()
        TranslatorRegistry._by_name.clear()

        translator = TranslatorRegistry.get_translator_for_command(BrowserOSCommand)

        assert isinstance(translator, BrowserOSTranslator)

    def test_get_translator_for_crawl_command(self):
        """Test getting translator for CrawlCommand."""
        # Reset the registry to ensure fresh discovery
        TranslatorRegistry._loaded = False
        TranslatorRegistry._by_command.clear()
        TranslatorRegistry._by_name.clear()

        translator = TranslatorRegistry.get_translator_for_command(CrawlCommand)

        assert isinstance(translator, Crawl4AITranslator)

    def test_get_translator_by_name_browseros(self):
        """Test getting translator by name 'browseros'."""
        # Reset the registry to ensure fresh discovery
        TranslatorRegistry._loaded = False
        TranslatorRegistry._by_command.clear()
        TranslatorRegistry._by_name.clear()

        translator = TranslatorRegistry.get_translator_by_name("browseros")

        assert isinstance(translator, BrowserOSTranslator)

    def test_get_translator_by_name_crawl4ai(self):
        """Test getting translator by name 'crawl4ai'."""
        # Reset the registry to ensure fresh discovery
        TranslatorRegistry._loaded = False
        TranslatorRegistry._by_command.clear()
        TranslatorRegistry._by_name.clear()

        translator = TranslatorRegistry.get_translator_by_name("crawl4ai")

        assert isinstance(translator, Crawl4AITranslator)

    def test_get_translator_by_name_case_insensitive(self):
        """Test that name lookup is case insensitive."""
        # Reset the registry to ensure fresh discovery
        TranslatorRegistry._loaded = False
        TranslatorRegistry._by_command.clear()
        TranslatorRegistry._by_name.clear()

        translator_upper = TranslatorRegistry.get_translator_by_name("BROWSEROS")
        translator_mixed = TranslatorRegistry.get_translator_by_name("BrowserOS")

        assert isinstance(translator_upper, BrowserOSTranslator)
        assert isinstance(translator_mixed, BrowserOSTranslator)

    def test_get_translator_fallback_to_crawl(self):
        """Test fallback to CrawlCommand translator for unknown command types."""
        # Reset the registry to ensure fresh discovery
        TranslatorRegistry._loaded = False
        TranslatorRegistry._by_command.clear()
        TranslatorRegistry._by_name.clear()

        # Mock a command class that isn't registered
        class UnknownCommand:
            pass

        translator = TranslatorRegistry.get_translator_for_command(UnknownCommand)

        # Should fall back to CrawlCommand translator
        assert isinstance(translator, Crawl4AITranslator)

    def test_get_translator_fallback_to_crawl_by_name(self):
        """Test fallback to CrawlCommand translator for unknown names."""
        # Reset the registry to ensure fresh discovery
        TranslatorRegistry._loaded = False
        TranslatorRegistry._by_command.clear()
        TranslatorRegistry._by_name.clear()

        translator = TranslatorRegistry.get_translator_by_name("unknown_motor")

        # Should fall back to CrawlCommand translator
        assert isinstance(translator, Crawl4AITranslator)

    def test_discovery_finds_all_translators(self):
        """Test that discovery finds all expected translators."""
        # Reset the registry to ensure fresh discovery
        TranslatorRegistry._loaded = False
        TranslatorRegistry._by_command.clear()
        TranslatorRegistry._by_name.clear()

        TranslatorRegistry._discover_translators()

        # Check that both translators are registered by name
        assert "browseros" in TranslatorRegistry._by_name
        assert "crawl4ai" in TranslatorRegistry._by_name

        # Check that both translators are registered by command type
        assert BrowserOSCommand in TranslatorRegistry._by_command
        assert CrawlCommand in TranslatorRegistry._by_command
