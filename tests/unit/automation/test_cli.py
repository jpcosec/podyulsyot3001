"""Tests for the unified automation CLI parser."""
from __future__ import annotations

import pytest

from src.automation.main import build_parser


def test_scrape_subcommand_requires_source():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["scrape"])


def test_scrape_parses_source_and_defaults():
    parser = build_parser()
    args = parser.parse_args(["scrape", "--source", "stepstone"])
    assert args.command == "scrape"
    assert args.source == "stepstone"
    assert args.overwrite is False
    assert args.limit is None


def test_scrape_parses_all_options():
    parser = build_parser()
    args = parser.parse_args([
        "scrape", "--source", "xing",
        "--job-query", "data scientist",
        "--city", "berlin",
        "--max-days", "7",
        "--limit", "10",
        "--overwrite",
    ])
    assert args.job_query == "data scientist"
    assert args.max_days == 7
    assert args.limit == 10
    assert args.overwrite is True


def test_apply_subcommand_requires_source():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["apply"])


def test_apply_parses_apply_mode():
    parser = build_parser()
    args = parser.parse_args([
        "apply", "--source", "xing",
        "--job-id", "12345",
        "--cv", "/path/cv.pdf",
        "--dry-run",
    ])
    assert args.command == "apply"
    assert args.source == "xing"
    assert args.job_id == "12345"
    assert args.cv_path == "/path/cv.pdf"
    assert args.dry_run is True
    assert args.backend == "crawl4ai"


def test_apply_parses_setup_session():
    parser = build_parser()
    args = parser.parse_args(["apply", "--source", "xing", "--setup-session"])
    assert args.setup_session is True
    assert args.job_id is None


def test_apply_parses_browseros_backend():
    parser = build_parser()
    args = parser.parse_args([
        "apply", "--backend", "browseros",
        "--source", "linkedin",
        "--job-id", "99",
        "--cv", "/cv.pdf",
    ])
    assert args.backend == "browseros"
    assert args.source == "linkedin"
