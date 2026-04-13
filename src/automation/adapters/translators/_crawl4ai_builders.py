"""Crawl4AI script builders."""

from src.automation.ariadne.contracts.base import AriadneIntent


def escape_value(value: str) -> str:
    """Escape value for C4A script."""
    return value.replace('"', '\\"')


def build_click_script(selector: str) -> str:
    return f"CLICK `{selector}`"


def build_set_script(selector: str, value: str) -> str:
    escaped_value = escape_value(value)
    return f'SET `{selector}` "{escaped_value}"'


def build_press_script(value: str) -> str:
    return f"PRESS {value}"


def build_wait_script(value: str, selector: str) -> str:
    if value and value.lstrip("-").isdigit():
        if int(value) < 100:
            return f"WAIT {value}"
        else:
            seconds = int(value) / 1000
            return f"WAIT {seconds}"
    elif selector:
        return f"WAIT `{selector}` 5"
    return "WAIT 2"


def build_extract_script(selector: str) -> str:
    return f"EVAL `await page.innerText(`{selector}`)`"


def build_c4a_script(intent: AriadneIntent, selector: str, value: str) -> str:
    """Build native C4A-Script command for the given intent."""
    builders = {
        AriadneIntent.CLICK: lambda: build_click_script(selector),
        AriadneIntent.FILL: lambda: build_set_script(selector, value),
        AriadneIntent.SELECT: lambda: build_set_script(selector, value),
        AriadneIntent.PRESS: lambda: build_press_script(value),
        AriadneIntent.UPLOAD: lambda: build_set_script(selector, value),
        AriadneIntent.WAIT: lambda: build_wait_script(value, selector),
        AriadneIntent.EXTRACT: lambda: build_extract_script(selector),
    }
    builder = builders.get(intent)
    if builder:
        return builder()
    raise ValueError(f"Unsupported intent for Crawl4AI: {intent}")
