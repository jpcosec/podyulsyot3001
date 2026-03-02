import json
import pytest
from pathlib import Path
from src.utils.loader import load_json


def test_load_json_returns_dict(tmp_path):
    f = tmp_path / "data.json"
    f.write_text('{"key": "value"}')
    result = load_json(f)
    assert result == {"key": "value"}


def test_load_json_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_json(tmp_path / "missing.json")
