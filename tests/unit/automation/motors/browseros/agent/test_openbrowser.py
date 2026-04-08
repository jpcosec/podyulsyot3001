"""Tests for BrowserOS natural-language agent communication."""

from __future__ import annotations

from pathlib import Path

from src.automation.motors.browseros.agent.openbrowser import OpenBrowserClient
from src.automation.motors.browseros.cli.client import SnapshotElement


def _snapshot(*entries: tuple[int, str, str]) -> list[SnapshotElement]:
    return [
        SnapshotElement(
            element_id=element_id,
            element_type=element_type,
            text=text,
            raw_line=f'[{element_id}] {element_type} "{text}"',
        )
        for element_id, element_type, text in entries
    ]


class _FakeBrowserClient:
    def __init__(
        self, snapshots: list[list[SnapshotElement]], active_pages: list[dict]
    ):
        self.snapshots = list(snapshots)
        self.active_pages = list(active_pages)
        self.calls: list[tuple] = []

    def new_page(
        self, url: str = "about:blank", *, background: bool = True, hidden: bool = False
    ) -> int:
        self.calls.append(("new_page", url, background, hidden))
        return 7

    def take_snapshot(self, page_id: int):
        self.calls.append(("take_snapshot", page_id))
        if self.snapshots:
            return self.snapshots.pop(0)
        return []

    def click(self, page_id: int, element_id: int) -> None:
        self.calls.append(("click", page_id, element_id))

    def fill(self, page_id: int, element_id: int, text: str) -> None:
        self.calls.append(("fill", page_id, element_id, text))

    def press_key(self, page_id: int, key: str) -> None:
        self.calls.append(("press_key", page_id, key))

    def get_active_page(self) -> dict:
        self.calls.append(("get_active_page",))
        if self.active_pages:
            page = self.active_pages.pop(0)
        else:
            page = {"pageId": 7, "url": "chrome://newtab/", "title": "BrowserOS"}
        return {"structuredContent": {"page": page}}

    def save_screenshot(self, page_id: int, file_path: Path) -> None:
        self.calls.append(("save_screenshot", page_id, str(file_path)))


def test_communicate_submits_prompt_from_agent_page(tmp_path: Path):
    fake = _FakeBrowserClient(
        snapshots=[
            _snapshot(
                (387, "textbox", "What should I do?"),
                (386, "button", "Send"),
            ),
            _snapshot(
                (387, "textbox", "What should I do?"),
                (386, "button", "Send"),
            ),
            _snapshot(
                (387, "textbox", "What should I do?"),
                (386, "button", "Send"),
            ),
            _snapshot((1, "link", "YouTube Home")),
        ],
        active_pages=[
            {"pageId": 7, "url": "chrome://newtab/", "title": "BrowserOS"},
            {"pageId": 7, "url": "https://www.youtube.com/", "title": "YouTube"},
        ],
    )
    client = OpenBrowserClient(browser_client=fake)

    result = client.communicate(
        "Go to YouTube",
        screenshot_path=tmp_path / "proof.png",
        timeout_seconds=0.1,
        poll_interval=0.0,
    )

    assert result.status == "success"
    assert result.page_url == "https://www.youtube.com/"
    assert ("fill", 7, 387, "Go to YouTube") in fake.calls
    assert ("click", 7, 386) in fake.calls
    assert ("save_screenshot", 7, str(tmp_path / "proof.png")) in fake.calls


def test_communicate_uses_launcher_suggestion_before_navigation():
    prompt = "Search for misilo"
    fake = _FakeBrowserClient(
        snapshots=[
            _snapshot((13, "combobox", "Ask BrowserOS or search Google...")),
            _snapshot((13, "combobox", "Ask BrowserOS or search Google...")),
            _snapshot(
                (13, "combobox", "Ask BrowserOS or search Google..."),
                (279, "option", f"Ask BrowserOS: {prompt}"),
            ),
            _snapshot((1, "button", "Stop")),
            _snapshot((1, "link", "misilo - YouTube")),
        ],
        active_pages=[
            {"pageId": 7, "url": "chrome://newtab/", "title": "BrowserOS"},
            {
                "pageId": 7,
                "url": "https://www.youtube.com/results?search_query=misilo",
                "title": "misilo - YouTube",
            },
        ],
    )
    client = OpenBrowserClient(browser_client=fake)

    result = client.communicate(prompt, timeout_seconds=0.1, poll_interval=0.0)

    assert result.status == "success"
    assert result.page_title == "misilo - YouTube"
    assert ("click", 7, 13) in fake.calls
    assert ("fill", 7, 13, prompt) in fake.calls
    assert ("click", 7, 279) in fake.calls
