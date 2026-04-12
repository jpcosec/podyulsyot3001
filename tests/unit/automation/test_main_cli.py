"""Tests for automation CLI parsing and exit codes."""

from unittest.mock import patch

from src.automation.main import _build_parser, main


def test_build_parser_exposes_apply_and_scrape_flags():
    """The canonical parser should expose current CLI flags."""
    parser = _build_parser()
    args = parser.parse_args(["scrape", "--source", "linkedin", "--limit", "2"])

    assert args.command == "scrape"
    assert args.source == "linkedin"
    assert args.limit == 2
    assert args.mode == "search"
    assert args.mission == "discovery"


def test_main_returns_error_for_resume_without_thread_id(capsys):
    """Input validation should return a non-zero exit code instead of exiting."""
    exit_code = main(
        ["apply", "--source", "linkedin", "--job-id", "1", "--cv", "cv.pdf", "--resume"]
    )

    output = capsys.readouterr().out
    assert exit_code == 1
    assert "--resume requires --thread-id" in output


def test_main_dispatches_scrape_and_returns_async_exit_code():
    """CLI main should forward scrape execution and return its exit code."""
    with patch("src.automation.main.run_scrape") as mock_run_scrape:
        mock_run_scrape.return_value = 0

        exit_code = main(["scrape", "--source", "linkedin"])

    assert exit_code == 0
    mock_run_scrape.assert_called_once()
