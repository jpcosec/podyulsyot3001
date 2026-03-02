from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent


def load_prompt(name: str) -> str:
    """Load a prompt file by name (without extension).

    Usage: load_prompt("cv_multi_agent") -> reads cv_multi_agent.txt
    """
    path = _PROMPTS_DIR / f"{name}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Prompt not found: {path}")
    return path.read_text(encoding="utf-8")


def load_prompt_with_context(name: str, context_json: str) -> str:
    """Load a prompt and inject context at {{CONTEXT_JSON}} placeholder."""
    template = load_prompt(name)
    if "{{CONTEXT_JSON}}" not in template:
        raise ValueError(f"Prompt '{name}' has no {{{{CONTEXT_JSON}}}} placeholder")
    return template.replace("{{CONTEXT_JSON}}", context_json)
