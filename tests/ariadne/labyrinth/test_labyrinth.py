import json
import pytest
from unittest.mock import patch

from src.automation.contracts.sensor import SnapshotResult
from src.automation.ariadne.labyrinth.url_node import URLNode
from src.automation.ariadne.labyrinth.room_state import RoomState
from src.automation.ariadne.labyrinth.skeleton import Skeleton, AbstractElement, ElementType
from src.automation.ariadne.labyrinth.labyrinth import Labyrinth


def make_snapshot(url: str, html: str = "<html/>") -> SnapshotResult:
    return SnapshotResult(url=url, html=html)


def make_room(room_id: str, url_template: str, predicate):
    url_node = URLNode(id=room_id.split(".")[0], url_template=url_template)
    state = RoomState(id=room_id, url_node_id=url_node.id, predicate=predicate)
    skeleton = Skeleton()
    return url_node, state, skeleton


class TestIdentifyRoom:
    def test_identifies_known_room(self):
        lab = Labyrinth("test_portal")
        url_node, state, skeleton = make_room(
            "home.anon",
            "https://stepstone.de",
            predicate=lambda s: True,
        )
        lab.expand(url_node, state, skeleton)

        snap = make_snapshot("https://stepstone.de")
        assert lab.identify_room(snap) == "home.anon"

    def test_unknown_url_returns_none(self):
        lab = Labyrinth("test_portal")
        snap = make_snapshot("https://unknown-portal.com")
        assert lab.identify_room(snap) is None

    def test_url_matches_but_predicate_fails(self):
        lab = Labyrinth("test_portal")
        url_node, state, skeleton = make_room(
            "home.with_modal",
            "https://stepstone.de",
            predicate=lambda s: "cookie-modal" in s.html,
        )
        lab.expand(url_node, state, skeleton)

        snap = make_snapshot("https://stepstone.de", html="<html>no modal here</html>")
        assert lab.identify_room(snap) is None

    def test_predicate_uses_html(self):
        lab = Labyrinth("test_portal")
        url_node, state, skeleton = make_room(
            "home.with_modal",
            "https://stepstone.de",
            predicate=lambda s: "cookie-modal" in s.html,
        )
        lab.expand(url_node, state, skeleton)

        snap = make_snapshot("https://stepstone.de", html='<div class="cookie-modal"/>')
        assert lab.identify_room(snap) == "home.with_modal"

    def test_first_matching_predicate_wins(self):
        lab = Labyrinth("test_portal")
        url_node = URLNode(id="home", url_template="https://stepstone.de")
        s1 = RoomState(id="home.anon", url_node_id="home", predicate=lambda s: True)
        s2 = RoomState(id="home.modal", url_node_id="home", predicate=lambda s: True)
        lab.expand(url_node, s1, Skeleton())
        lab.expand(url_node, s2, Skeleton())

        snap = make_snapshot("https://stepstone.de")
        result = lab.identify_room(snap)
        assert result in ("home.anon", "home.modal")


class TestExpand:
    def test_expand_adds_room(self):
        lab = Labyrinth("test_portal")
        url_node, state, skeleton = make_room("home.anon", "https://stepstone.de", lambda s: True)
        lab.expand(url_node, state, skeleton)
        assert lab.get_room("home.anon") is not None

    def test_expand_overwrites_existing(self):
        lab = Labyrinth("test_portal")
        url_node = URLNode(id="home", url_template="https://stepstone.de")
        s1 = RoomState(id="home.anon", url_node_id="home", predicate=lambda s: True)
        s2 = RoomState(id="home.anon", url_node_id="home", predicate=lambda s: False)
        lab.expand(url_node, s1, Skeleton())
        lab.expand(url_node, s2, Skeleton())

        room = lab.get_room("home.anon")
        snap = make_snapshot("https://stepstone.de")
        assert not room.state.matches(snap)  # second predicate (always False) wins


class TestPersistence:
    def test_save_and_load(self, tmp_path):
        with patch("src.automation.ariadne.labyrinth.labyrinth.DATA_ROOT", tmp_path):
            lab = Labyrinth("portal_x")
            url_node, state, skeleton = make_room("home.anon", "https://example.com", lambda s: True)
            lab.expand(url_node, state, skeleton)
            lab.save()

            restored = Labyrinth.load("portal_x")
            assert restored.get_room("home.anon") is not None

    def test_load_nonexistent_returns_empty(self, tmp_path):
        with patch("src.automation.ariadne.labyrinth.labyrinth.DATA_ROOT", tmp_path):
            lab = Labyrinth.load("nonexistent_portal")
            snap = make_snapshot("https://anywhere.com")
            assert lab.identify_room(snap) is None

    def test_loaded_room_matches_by_url(self, tmp_path):
        with patch("src.automation.ariadne.labyrinth.labyrinth.DATA_ROOT", tmp_path):
            lab = Labyrinth("portal_y")
            url_node, state, skeleton = make_room("home.anon", "https://example.com", lambda s: True)
            lab.expand(url_node, state, skeleton)
            lab.save()

            restored = Labyrinth.load("portal_y")
            snap = make_snapshot("https://example.com")
            assert restored.identify_room(snap) == "home.anon"
