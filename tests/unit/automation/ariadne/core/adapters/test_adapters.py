import pytest
from src.automation.ariadne.core.periphery import Sensor, Motor, BrowserAdapter
from src.automation.ariadne.core.adapters.browseros import BrowserOSAdapter
from src.automation.ariadne.core.adapters.crawl4ai import Crawl4AIAdapter

def test_browseros_adapter_protocols():
    adapter = BrowserOSAdapter()
    assert isinstance(adapter, Sensor)
    assert isinstance(adapter, Motor)
    assert isinstance(adapter, BrowserAdapter)
    
    # Check for required methods
    assert hasattr(adapter, "perceive")
    assert hasattr(adapter, "act")
    assert hasattr(adapter, "is_healthy")
    assert hasattr(adapter, "__aenter__")
    assert hasattr(adapter, "__aexit__")

def test_crawl4ai_adapter_protocols():
    adapter = Crawl4AIAdapter()
    assert isinstance(adapter, Sensor)
    assert isinstance(adapter, Motor)
    assert isinstance(adapter, BrowserAdapter)
    
    # Check for required methods
    assert hasattr(adapter, "perceive")
    assert hasattr(adapter, "act")
    assert hasattr(adapter, "is_healthy")
    assert hasattr(adapter, "__aenter__")
    assert hasattr(adapter, "__aexit__")
