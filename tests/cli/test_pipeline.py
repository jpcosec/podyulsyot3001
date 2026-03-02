"""Tests for the redesigned CLI using new step-based structure."""

from src.cli.pipeline import _build_parser


def test_parse_job_ingest_defaults():
    """Test: pipeline job 201084 ingest"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "ingest"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "ingest"
    assert args.source == "tu_berlin"
    assert args.force is False


def test_parse_job_match_defaults():
    """Test: pipeline job 201084 match"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "match"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "match"
    assert args.force is False


def test_parse_job_render_defaults():
    """Test: pipeline job 201084 render"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "render"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "render"
    assert args.via == "docx"
    assert args.docx_template == "modern"
    assert args.language == "english"


def test_parse_job_render_custom_options():
    """Test: pipeline job 201084 render --via latex --language german"""
    parser = _build_parser()
    args = parser.parse_args([
        "job", "201084", "render",
        "--via", "latex",
        "--language", "german",
        "--force",
    ])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "render"
    assert args.via == "latex"
    assert args.language == "german"
    assert args.force is True


def test_parse_job_package_defaults():
    """Test: pipeline job 201084 package"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "package"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "package"
    assert args.force is False


def test_parse_job_status():
    """Test: pipeline job 201084 status"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "status"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "status"


def test_parse_job_run():
    """Test: pipeline job 201084 run"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "run"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "run"


def test_parse_job_regenerate():
    """Test: pipeline job 201084 regenerate matching"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "regenerate", "matching"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "regenerate"
    assert args.regenerate_step == "matching"


def test_parse_job_validate_ats():
    """Test: pipeline job 201084 validate-ats"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "validate-ats"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "validate-ats"
    assert args.ats_target == "pdf"


def test_parse_job_validate_ats_docx():
    """Test: pipeline job 201084 validate-ats --ats-target docx"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "validate-ats", "--ats-target", "docx"])

    assert args.command == "job"
    assert args.verb == "validate-ats"
    assert args.ats_target == "docx"


def test_parse_job_template_test():
    """Test: pipeline job 201084 template-test"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "template-test"])

    assert args.command == "job"
    assert args.job_id == "201084"
    assert args.verb == "template-test"
    assert args.target == "pdf"
    assert args.require_perfect is False


def test_parse_job_template_test_require_perfect():
    """Test: pipeline job 201084 template-test --require-perfect"""
    parser = _build_parser()
    args = parser.parse_args(["job", "201084", "template-test", "--require-perfect"])

    assert args.command == "job"
    assert args.verb == "template-test"
    assert args.require_perfect is True


def test_parse_jobs_list_defaults():
    """Test: pipeline jobs"""
    parser = _build_parser()
    args = parser.parse_args(["jobs"])

    assert args.command == "jobs"
    assert args.expiring is None
    assert args.expired is False
    assert args.keyword is None
    assert args.category is None


def test_parse_jobs_expiring():
    """Test: pipeline jobs --expiring 7"""
    parser = _build_parser()
    args = parser.parse_args(["jobs", "--expiring", "7"])

    assert args.command == "jobs"
    assert args.expiring == 7
    assert args.expired is False


def test_parse_jobs_expired():
    """Test: pipeline jobs --expired"""
    parser = _build_parser()
    args = parser.parse_args(["jobs", "--expired"])

    assert args.command == "jobs"
    assert args.expired is True


def test_parse_jobs_keyword():
    """Test: pipeline jobs --keyword bioprocess"""
    parser = _build_parser()
    args = parser.parse_args(["jobs", "--keyword", "bioprocess"])

    assert args.command == "jobs"
    assert args.keyword == "bioprocess"


def test_parse_jobs_category():
    """Test: pipeline jobs --category research"""
    parser = _build_parser()
    args = parser.parse_args(["jobs", "--category", "research"])

    assert args.command == "jobs"
    assert args.category == "research"


def test_parse_ingest_url_single():
    """Test: pipeline ingest-url <url>"""
    parser = _build_parser()
    args = parser.parse_args([
        "ingest-url",
        "https://www.jobs.tu-berlin.de/en/job-postings/201084",
    ])

    assert args.command == "ingest-url"
    assert args.urls == ["https://www.jobs.tu-berlin.de/en/job-postings/201084"]
    assert args.strict_english is False


def test_parse_ingest_url_multiple():
    """Test: pipeline ingest-url <url1> <url2>"""
    parser = _build_parser()
    args = parser.parse_args([
        "ingest-url",
        "https://www.jobs.tu-berlin.de/en/job-postings/201084",
        "https://www.jobs.tu-berlin.de/en/job-postings/201085",
    ])

    assert args.command == "ingest-url"
    assert len(args.urls) == 2


def test_parse_ingest_url_strict_english():
    """Test: pipeline ingest-url <url> --strict-english"""
    parser = _build_parser()
    args = parser.parse_args([
        "ingest-url",
        "https://www.jobs.tu-berlin.de/en/job-postings/201084",
        "--strict-english",
    ])

    assert args.command == "ingest-url"
    assert args.strict_english is True


def test_parse_ingest_listing():
    """Test: pipeline ingest-listing <url>"""
    parser = _build_parser()
    args = parser.parse_args([
        "ingest-listing",
        "https://www.jobs.tu-berlin.de/en/job-postings",
    ])

    assert args.command == "ingest-listing"
    assert args.url == "https://www.jobs.tu-berlin.de/en/job-postings"
    assert args.delay == 0.5
    assert args.strict_english is False


def test_parse_ingest_listing_with_delay():
    """Test: pipeline ingest-listing <url> --delay 1.5"""
    parser = _build_parser()
    args = parser.parse_args([
        "ingest-listing",
        "https://www.jobs.tu-berlin.de/en/job-postings",
        "--delay", "1.5",
    ])

    assert args.command == "ingest-listing"
    assert args.delay == 1.5


def test_parse_archive_specific_job():
    """Test: pipeline archive 201084"""
    parser = _build_parser()
    args = parser.parse_args(["archive", "201084"])

    assert args.command == "archive"
    assert args.job_id == "201084"
    assert args.expired is False


def test_parse_archive_expired():
    """Test: pipeline archive --expired"""
    parser = _build_parser()
    args = parser.parse_args(["archive", "--expired"])

    assert args.command == "archive"
    assert args.expired is True


def test_parse_index():
    """Test: pipeline index"""
    parser = _build_parser()
    args = parser.parse_args(["index"])

    assert args.command == "index"


def test_parse_backup():
    """Test: pipeline backup"""
    parser = _build_parser()
    args = parser.parse_args(["backup"])

    assert args.command == "backup"
