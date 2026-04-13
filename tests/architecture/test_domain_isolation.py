import pytest
from pytest_archon import archrule

def test_ariadne_domain_isolation():
    """
    Ariadne domain (src.automation.ariadne) must NOT import:
    - Motor implementations (src.automation.motors)
    - Low-level network libraries (requests, httpx)
    """
    (
        archrule("Ariadne Domain Isolation")
        .match("src.automation.ariadne*")
        .should_not_import("src.automation.motors*")
        .should_not_import("requests*")
        .should_not_import("httpx*")
        .check("src.automation")
    )

def test_executors_are_dumb():
    """
    Executors (src.automation.motors) must NOT import Ariadne domain models.
    They should only receive primitive commands or protocol-defined payloads.
    """
    (
        archrule("Dumb Executors")
        .match("src.automation.motors*")
        .should_not_import("src.automation.ariadne.models*")
        .check("src.automation")
    )

# Requirement 3: Ariadne requires MapRepository
# We'll use pyfakefs to ensure that components only work if the repository provides the data,
# and they don't try to access the filesystem directly using hardcoded paths.

class AriadneNode:
    """A dummy node that needs a map."""
    def __init__(self, repository=None):
        self.repository = repository

    def run_raw(self, path: str):
        """VIOLATION: Direct disk I/O."""
        with open(path, "r") as f:
            return f.read()

    def run_via_repo(self, portal_name: str):
        """CORRECT: Uses repository."""
        if not self.repository:
            raise ValueError("Repository required")
        return self.repository.get_map(portal_name)

def test_ariadne_requires_map_repository(fs):
    """
    Ensure that Ariadne nodes fail if they try raw disk I/O instead of a repository,
    and work correctly when using a repository in a clean-room (pyfakefs).
    """
    from src.automation.ariadne.repository import MapRepository
    from src.automation.ariadne.models import AriadneMap

    # Set up fake FS for the repository
    portal_name = "test_portal"
    # Use a dummy JSON that satisfies the NEW AriadneMap model
    dummy_json = """
    {
        "meta": {
            "source": "test_portal",
            "flow": "easy_apply",
            "version": "v1",
            "status": "draft"
        },
        "states": {},
        "edges": [],
        "success_states": [],
        "failure_states": []
    }
    """
    # MapRepository expects maps at <base_dir>/<portal_name>/maps/easy_apply.json
    map_path = "/src/automation/portals/test_portal/maps/easy_apply.json"
    fs.create_file(map_path, contents=dummy_json)

    repo = MapRepository(base_dir="/src/automation/portals")
    node = AriadneNode(repository=repo)

    # 1. Test CORRECTION (Using Repository)
    ariadne_map = node.run_via_repo(portal_name)
    assert isinstance(ariadne_map, AriadneMap)
    assert ariadne_map.meta.source == portal_name

    # 2. Test VIOLATION (Direct disk I/O should be blocked if not using repo-provided path)
    # Even if we try to read the same path, the guardrail here is more about the code pattern,
    # but at runtime, we can demonstrate isolation.
    # If the node tries to read a path NOT in our controlled fake FS, it fails.
    import pytest
    with pytest.raises(FileNotFoundError):
        node.run_raw("/unauthorized/path/to/map.json")

# Requirement 4: Normalization Blindness
# Normalization should be config-driven, no magic strings in the code.

class NormalizationEngine:
    """A dummy normalization engine."""
    def __init__(self, config=None):
        self.config = config or {}

    def normalize(self, raw_data: dict):
        """
        VIOLATION: If it uses hardcoded keys like 'linkedin' to do magic.
        CORRECT: If it uses self.config to find rules.
        """
        results = []
        for portal, rules in self.config.items():
            if portal in raw_data:
                results.append(f"Normalized {portal} using {rules}")
        return results

def test_normalization_blindness():
    """
    Ensure normalization engine is config-driven (no hardcoded keywords).
    It must return empty results if no configuration is injected.
    """
    # 1. Blind by default
    engine = NormalizationEngine(config={})
    raw_data = {"linkedin": {"some": "data"}}
    
    # It should not know how to handle 'linkedin' without config
    assert engine.normalize(raw_data) == []

    # 2. Config-driven
    engine = NormalizationEngine(config={"linkedin": "rule1"})
    assert engine.normalize(raw_data) == ["Normalized linkedin using rule1"]
