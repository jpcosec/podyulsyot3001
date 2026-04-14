import pytest
from src.automation.ariadne.labyrinth.url_node import URLNode


@pytest.fixture
def jobs_node():
    return URLNode(id="jobs", url_template="https://stepstone.de/jobs/in-{city}")


@pytest.fixture
def paged_node():
    return URLNode(id="jobs_paged", url_template="https://stepstone.de/jobs/in-{city}{?page,sort}")


class TestMatch:
    def test_matches_plain_url(self, jobs_node):
        assert jobs_node.match("https://stepstone.de/jobs/in-berlin")

    def test_matches_url_with_query_params(self, jobs_node):
        assert jobs_node.match("https://stepstone.de/jobs/in-berlin?page=2&sort=date")

    def test_matches_optional_query_template(self, paged_node):
        assert paged_node.match("https://stepstone.de/jobs/in-berlin")
        assert paged_node.match("https://stepstone.de/jobs/in-berlin?page=3")

    def test_no_match_different_path(self, jobs_node):
        assert not jobs_node.match("https://stepstone.de/home")

    def test_no_match_different_domain(self, jobs_node):
        assert not jobs_node.match("https://linkedin.com/jobs/in-berlin")

    def test_no_match_extra_segment(self, jobs_node):
        assert not jobs_node.match("https://stepstone.de/jobs/in-berlin/details/123")

    def test_matches_trailing_slash_ignored(self, jobs_node):
        assert jobs_node.match("https://stepstone.de/jobs/in-berlin/")


class TestExtractParams:
    def test_extracts_path_param(self, jobs_node):
        params = jobs_node.extract_params("https://stepstone.de/jobs/in-berlin")
        assert params["city"] == "berlin"

    def test_extracts_query_params(self, jobs_node):
        params = jobs_node.extract_params("https://stepstone.de/jobs/in-berlin?page=2&sort=date")
        assert params["page"] == "2"
        assert params["sort"] == "date"

    def test_extracts_combined(self, paged_node):
        params = paged_node.extract_params("https://stepstone.de/jobs/in-munich?page=5")
        assert params["city"] == "munich"
        assert params["page"] == "5"

    def test_no_params_empty_dict(self, jobs_node):
        params = jobs_node.extract_params("https://stepstone.de/jobs/in-berlin")
        assert "page" not in params


class TestSerialization:
    def test_roundtrip(self, jobs_node):
        restored = URLNode.from_dict(jobs_node.to_dict())
        assert restored.id == jobs_node.id
        assert restored.url_template == jobs_node.url_template
        assert restored.match("https://stepstone.de/jobs/in-berlin")
