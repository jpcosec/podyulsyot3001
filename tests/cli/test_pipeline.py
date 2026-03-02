from src.cli.pipeline import build_parser


def test_parse_motivation_pre_defaults():
    parser = build_parser()
    args = parser.parse_args(["motivation-pre", "201084"])

    assert args.command == "motivation-pre"
    assert args.job_id == "201084"
    assert args.source == "tu_berlin"
    assert args.output_name == "motivation_letter.pre.md"


def test_parse_fetch_url_defaults():
    parser = build_parser()
    args = parser.parse_args(
        ["fetch-url", "https://www.jobs.tu-berlin.de/en/job-postings/201084"]
    )

    assert args.command == "fetch-url"
    assert args.urls == ["https://www.jobs.tu-berlin.de/en/job-postings/201084"]
    assert args.source == "tu_berlin"
    assert args.strict_english is True


def test_parse_fetch_listing_defaults():
    parser = build_parser()
    args = parser.parse_args(
        [
            "fetch-listing",
            "https://www.jobs.tu-berlin.de/en/job-postings?filter[x]=y",
        ]
    )

    assert args.command == "fetch-listing"
    assert args.url == "https://www.jobs.tu-berlin.de/en/job-postings?filter[x]=y"
    assert args.source == "tu_berlin"
    assert args.strict_english is True
    assert args.delay == 0.5


def test_parse_fetch_listing_allow_non_english():
    parser = build_parser()
    args = parser.parse_args(
        [
            "fetch-listing",
            "https://www.jobs.tu-berlin.de/en/job-postings?filter[x]=y",
            "--allow-non-english",
        ]
    )

    assert args.command == "fetch-listing"
    assert args.strict_english is False


def test_parse_archive_passed_defaults():
    parser = build_parser()
    args = parser.parse_args(["archive-passed"])

    assert args.command == "archive-passed"
    assert args.source == "tu_berlin"
    assert args.today is None
    assert args.apply is False


def test_parse_archive_passed_apply():
    parser = build_parser()
    args = parser.parse_args(
        ["archive-passed", "--source", "tu_berlin", "--today", "2026-03-02", "--apply"]
    )

    assert args.command == "archive-passed"
    assert args.source == "tu_berlin"
    assert args.today == "2026-03-02"
    assert args.apply is True


def test_parse_motivation_build_custom_output():
    parser = build_parser()
    args = parser.parse_args(
        [
            "motivation-build",
            "201084",
            "--source",
            "tu_berlin",
            "--output-name",
            "letter.custom.md",
        ]
    )

    assert args.command == "motivation-build"
    assert args.job_id == "201084"
    assert args.output_name == "letter.custom.md"
    assert args.skip_pdf is False
    assert args.skip_email is False


def test_parse_motivation_build_skip_flags():
    parser = build_parser()
    args = parser.parse_args(
        ["motivation-build", "201084", "--skip-pdf", "--skip-email"]
    )

    assert args.command == "motivation-build"
    assert args.skip_pdf is True
    assert args.skip_email is True


def test_parse_app_prepare_defaults():
    parser = build_parser()
    args = parser.parse_args(["app-prepare", "201084"])

    assert args.command == "app-prepare"
    assert args.job_id == "201084"
    assert args.source == "tu_berlin"
    assert args.target == "all"
    assert args.ats_mode == "fallback"


def test_parse_app_renderize_custom_flags():
    parser = build_parser()
    args = parser.parse_args(
        [
            "app-renderize",
            "201084",
            "--target",
            "cv",
            "--ats-mode",
            "strict",
            "--language",
            "english",
            "--via",
            "docx",
            "--docx-template",
            "modern",
        ]
    )

    assert args.command == "app-renderize"
    assert args.target == "cv"
    assert args.ats_mode == "strict"
    assert args.language == "english"
    assert args.via == "docx"
    assert args.docx_template == "modern"


def test_parse_app_status_defaults():
    parser = build_parser()
    args = parser.parse_args(["app-status", "201084"])

    assert args.command == "app-status"
    assert args.job_id == "201084"
    assert args.source == "tu_berlin"
    assert args.target == "all"


def test_parse_jobs_index_defaults():
    parser = build_parser()
    args = parser.parse_args(["jobs-index"])

    assert args.command == "jobs-index"
    assert args.source == "all"


def test_parse_app_run_defaults():
    parser = build_parser()
    args = parser.parse_args(["app-run", "201084"])

    assert args.command == "app-run"
    assert args.job_id == "201084"
    assert args.source == "tu_berlin"
    assert args.target == "all"
    assert args.ats_mode == "fallback"
    assert args.language == "english"
    assert args.via == "docx"
